"""CU-05 Procesar planilla de sueldos (RF-10 a RF-13, RF-16), patrón Facade (docs/06).

``FachadaPlanilla`` oculta a las vistas la importación, el cálculo (``CalculadoraDescuentos``), el cierre y
la generación de boletas (``GeneradorBoletas``). ``ControladorPlanilla`` arma los datos de las pantallas.
"""

from dataclasses import dataclass
from decimal import Decimal

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.administracion.models import Bitacora, GestionSalarial
from apps.core import auditoria
from apps.core.parametros import parametros
from apps.kardex.models import Contrato, Empleado

from .models import Anticipo, BoletaPago, DetalleBoleta, Marcacion, Planilla
from .services import (
    CIEN,
    PlanillaCerrada,
    ServicioAnticipos,
    ServicioF110,
    _mes_anterior,
    haber_basico,
    redondear,
)
from .services import HaberNoConfigurado as HaberNoConfigurado  # noqa: F401  (se reexporta)

CERO = Decimal("0.00")
TREINTA = Decimal("30")
UMBRAL_RC_IVA_SMN = Decimal("2")  # RN-05: el RC-IVA no aplica hasta 2 salarios mínimos.
MAX_OTROS_INGRESOS = Decimal("99999999.99")
DURACION_BORRADOR = 60 * 60 * 24 * 30
MOTIVO_CIERRE = "Aprobación y cierre"
C = DetalleBoleta.Concepto


@dataclass(frozen=True)
class Calculo:
    """Resultado de RN-01 a RN-07 para un contrato."""

    haber_basico: Decimal
    dias: int
    sueldo_ganado: Decimal
    otros_ingresos: Decimal
    total_ganado: Decimal
    tot_ingresos: Decimal
    anticipos: Decimal
    afp_aplica: bool
    porc_afp: Decimal
    afp: Decimal
    base_rc_iva: Decimal
    porc_iva: Decimal
    impuesto: Decimal
    facturas: Decimal
    credito: Decimal
    saldo_anterior: Decimal
    rc_iva: Decimal
    saldo_favor: Decimal
    tot_descuentos: Decimal
    liquido: Decimal


class CalculadoraDescuentos:
    """RN-01 a RN-07: ingresos, AFP y RC-IVA con los parámetros de la gestión (RF-12, RF-13)."""

    def __init__(self, anio):
        # Sin parámetros de la gestión no se procesa la planilla (RF-11, regla 4).
        self.smn = parametros.valor("SMN", anio)
        self.porc_afp = parametros.valor("PORC_AFP", anio)
        self.umbral_afp = parametros.valor("UMBRAL_AFP", anio)
        self.porc_iva = parametros.valor("PORC_IVA", anio)

    def calcular(self, haber_basico, dias, otros_ingresos=CERO, anticipos=CERO, facturas=CERO,
                 saldo_anterior=CERO):
        haber_basico = redondear(haber_basico)
        sueldo = redondear(haber_basico * dias / TREINTA)  # RN-01
        total_ganado = sueldo + otros_ingresos  # RN-02
        afp_aplica = total_ganado > self.umbral_afp * self.smn
        afp = redondear(total_ganado * self.porc_afp / CIEN) if afp_aplica else CERO  # RN-04
        minimo = UMBRAL_RC_IVA_SMN * self.smn
        base = CERO
        if haber_basico > minimo:  # RN-05
            base = max(redondear(total_ganado - afp - minimo), CERO)
        impuesto = redondear(base * self.porc_iva / CIEN)
        credito = redondear(facturas * self.porc_iva / CIEN)
        disponible = credito + saldo_anterior
        rc_iva = max(impuesto - disponible, CERO)
        saldo_favor = max(disponible - impuesto, CERO)
        tot_descuentos = anticipos + afp + rc_iva  # RN-03
        return Calculo(
            haber_basico=haber_basico, dias=dias, sueldo_ganado=sueldo, otros_ingresos=otros_ingresos,
            total_ganado=total_ganado, tot_ingresos=total_ganado, anticipos=anticipos, afp_aplica=afp_aplica,
            porc_afp=self.porc_afp, afp=afp, base_rc_iva=base, porc_iva=self.porc_iva, impuesto=impuesto,
            facturas=facturas, credito=credito, saldo_anterior=saldo_anterior, rc_iva=rc_iva,
            saldo_favor=saldo_favor, tot_descuentos=tot_descuentos, liquido=total_ganado - tot_descuentos,  # RN-07
        )


@dataclass(frozen=True)
class Inconsistencia:
    ci: str
    motivo: str


@dataclass(frozen=True)
class LineaPlanilla:
    contrato: Contrato
    calculo: Calculo


@dataclass
class Preplanilla:
    planilla: Planilla
    lineas: list
    inconsistencias: list

    @property
    def totales(self):
        campos = ("sueldo_ganado", "otros_ingresos", "tot_ingresos", "anticipos", "afp", "rc_iva",
                  "tot_descuentos", "liquido")
        return {c: sum((getattr(linea.calculo, c) for linea in self.lineas), CERO) for c in campos}


@dataclass
class ResultadoImportacion:
    importados: int
    reemplazados: int
    inconsistencias: list


class GeneradorBoletas:
    """CU-05.5 Generar boletas de pago: BOLETA PAGO y DETALLE BOLETA con la base y el porcentaje (RN-08)."""

    def generar(self, planilla, lineas):
        """Devuelve (cantidad de boletas, total líquido)."""
        BoletaPago.objects.bulk_create(
            BoletaPago(
                planilla=planilla, contrato=linea.contrato, dias_trab=linea.calculo.dias,
                tot_ingresos=linea.calculo.tot_ingresos, tot_descuentos=linea.calculo.tot_descuentos,
                liquido=linea.calculo.liquido,
            )
            for linea in lineas
        )
        # MySQL no devuelve las claves de bulk_create: se relee el mapa contrato → boleta.
        boletas = dict(BoletaPago.objects.filter(planilla=planilla).values_list("contrato_id", "nro"))
        detalles = []
        for linea in lineas:
            nro = boletas[linea.contrato.nro]
            for concepto, base, porcentaje, monto in self._conceptos(linea.calculo):
                detalles.append(DetalleBoleta(boleta_id=nro, concepto=concepto, base=base, porcentaje=porcentaje,
                                              monto=monto))
        DetalleBoleta.objects.bulk_create(detalles, batch_size=2000)
        return len(lineas), sum((linea.calculo.liquido for linea in lineas), CERO)

    @staticmethod
    def _conceptos(c):
        return [
            (C.SUELDO_GANADO, c.haber_basico, None, c.sueldo_ganado),
            (C.OTROS_INGRESOS, None, None, c.otros_ingresos),
            (C.ANTICIPO, None, None, c.anticipos),
            (C.AFP, c.total_ganado, c.porc_afp if c.afp_aplica else None, c.afp),
            (C.RC_IVA, c.base_rc_iva, c.porc_iva if c.base_rc_iva > 0 else None, c.rc_iva),
            (C.SALDO_RC_IVA, c.facturas, None, c.saldo_favor),
        ]


class FachadaPlanilla:
    """Punto de entrada de CU-05 para las vistas."""

    # --- Importación (CU-05.1 y CU-05.3) ---------------------------------------------------------

    def importar_asistencia(self, fuente, anio, mes, motivo=None, usuario=None):
        if planilla_cerrada_de(anio, mes):
            raise PlanillaCerrada("La planilla del mes está cerrada: solo se permite consultarla.")
        motivo = (motivo or "").strip()
        inconsistencias = []
        validos = {}
        for registro in fuente.registros():
            if registro.motivo:
                inconsistencias.append(Inconsistencia(registro.ci, registro.motivo))
            else:
                validos[registro.ci] = registro.dias
        existentes = set(Empleado.objects.filter(ci__in=validos).values_list("ci", flat=True))
        contratos = dict(
            Contrato.objects.filter(empleado_id__in=existentes, estado=Contrato.Estado.VIGENTE)
            .values_list("empleado_id", "nro")
        )
        for ci in validos:
            if ci not in existentes:
                inconsistencias.append(Inconsistencia(ci, "CI no registrado"))
            elif ci not in contratos:
                inconsistencias.append(Inconsistencia(ci, "Sin contrato vigente"))
        previas = {m.contrato_id: m for m in Marcacion.objects.filter(contrato_id__in=contratos.values(),
                                                                       anio=anio, mes=mes)}
        if previas and not motivo:
            raise ValueError("Reimportar reemplaza marcaciones existentes: indique el motivo.")
        nuevas, cambiadas = [], []
        for ci, nro in contratos.items():
            if nro in previas:
                previas[nro].dias_trab = validos[ci]
                cambiadas.append(previas[nro])
            else:
                nuevas.append(Marcacion(contrato_id=nro, anio=anio, mes=mes, dias_trab=validos[ci]))
        with transaction.atomic():
            Marcacion.objects.bulk_create(nuevas)
            Marcacion.objects.bulk_update(cambiadas, ["dias_trab"])
            if nuevas:
                auditoria.registrar(Bitacora.Operacion.ALTA, tabla="MARCACION", usuario=usuario,
                                    valor_nuevo={"Año": anio, "Mes": mes, "Registros": len(nuevas)})
            if cambiadas:
                auditoria.registrar(Bitacora.Operacion.ACTUALIZACION, tabla="MARCACION", usuario=usuario,
                                    motivo=motivo, valor_nuevo={"Año": anio, "Mes": mes, "Registros": len(cambiadas)})
        sin_marcacion = Contrato.objects.filter(estado=Contrato.Estado.VIGENTE).exclude(
            marcaciones__anio=anio, marcaciones__mes=mes
        ).values_list("empleado_id", flat=True)
        inconsistencias += [Inconsistencia(ci, "Contrato vigente sin marcación") for ci in sin_marcacion]
        return ResultadoImportacion(len(nuevas) + len(cambiadas), len(cambiadas), inconsistencias)

    # --- Preplanilla (CU-05.2) -------------------------------------------------------------------

    def generar_preplanilla(self, anio, mes):
        if not 1 <= mes <= 12:
            raise ValueError("El mes debe estar entre 1 y 12.")
        calculadora = CalculadoraDescuentos(anio)
        with transaction.atomic():
            gestion = GestionSalarial.objects.filter(anio=anio).first()
            if gestion is None:
                from apps.core.parametros import ParametroNoConfigurado

                raise ParametroNoConfigurado(f"La gestión {anio} no está configurada.")
            planilla, creada = Planilla.objects.get_or_create(gestion=gestion, mes=mes)
            if planilla.estado == Planilla.Estado.CERRADA:
                raise PlanillaCerrada("La planilla del mes está cerrada: solo se permite consultarla.")
            lineas, inconsistencias = self._calcular(planilla, calculadora)
            if creada:
                auditoria.registrar(Bitacora.Operacion.ALTA, tabla="PLANILLA",
                                    valor_nuevo={"Nro": planilla.nro, "Año": anio, "Mes": mes})
        return Preplanilla(planilla, lineas, inconsistencias)

    def _calcular(self, planilla, calculadora):
        anio, mes = planilla.gestion_id, planilla.mes
        marcaciones = dict(Marcacion.objects.filter(anio=anio, mes=mes).values_list("contrato_id", "dias_trab"))
        vigentes = list(
            Contrato.objects.filter(estado=Contrato.Estado.VIGENTE).select_related("categoria").order_by("nro")
        )
        inconsistencias = [Inconsistencia(c.empleado_id, "Contrato vigente sin marcación")
                           for c in vigentes if c.nro not in marcaciones]
        haberes = {}
        anticipos = ServicioAnticipos().pendientes(anio, mes)
        facturas = ServicioF110().facturas_aplicables(anio, mes)
        saldos = self._saldos_anteriores(anio, mes)
        otros = self.otros_ingresos(planilla)
        lineas = []
        for contrato in vigentes:
            if contrato.nro not in marcaciones:
                continue
            if contrato.categoria_id not in haberes:
                haberes[contrato.categoria_id] = haber_basico(contrato, anio)
            calculo = calculadora.calcular(
                haberes[contrato.categoria_id], marcaciones[contrato.nro],
                otros_ingresos=otros.get(contrato.nro, CERO), anticipos=anticipos.get(contrato.nro, CERO),
                facturas=facturas.get(contrato.nro, CERO), saldo_anterior=saldos.get(contrato.nro, CERO),
            )
            lineas.append(LineaPlanilla(contrato, calculo))
        return lineas, inconsistencias

    @staticmethod
    def _saldos_anteriores(anio, mes):
        """RN-05: saldo a favor del RC-IVA del mes anterior, de su planilla cerrada."""
        anio_ant, mes_ant = _mes_anterior(anio, mes)
        filas = DetalleBoleta.objects.filter(
            boleta__planilla__gestion_id=anio_ant, boleta__planilla__mes=mes_ant,
            boleta__planilla__estado=Planilla.Estado.CERRADA, concepto=C.SALDO_RC_IVA,
        ).values_list("boleta__contrato_id", "monto")
        return dict(filas)

    # --- Otros ingresos: borrador en la caché hasta el cierre ------------------------------------

    @staticmethod
    def clave_borrador(planilla):
        return f"planillas:otros_ingresos:{planilla.nro}"

    def otros_ingresos(self, planilla):
        guardado = cache.get(self.clave_borrador(planilla)) or {}
        return {int(nro): Decimal(monto) for nro, monto in guardado.items()}

    def registrar_otros_ingresos(self, planilla, nro_contrato, monto):
        if planilla.estado == Planilla.Estado.CERRADA:
            raise PlanillaCerrada("La planilla del mes está cerrada.")
        monto = redondear(monto)
        if not CERO <= monto <= MAX_OTROS_INGRESOS:
            raise ValueError("Los otros ingresos deben estar entre 0 y 99.999.999,99.")
        en_planilla = Marcacion.objects.filter(
            contrato_id=nro_contrato, contrato__estado=Contrato.Estado.VIGENTE,
            anio=planilla.gestion_id, mes=planilla.mes,
        ).exists()
        if not en_planilla:
            raise ValueError("El contrato no está en la planilla del mes.")
        borrador = {str(k): str(v) for k, v in self.otros_ingresos(planilla).items()}
        if monto == CERO:
            borrador.pop(str(nro_contrato), None)
        else:
            borrador[str(nro_contrato)] = str(monto)
        cache.set(self.clave_borrador(planilla), borrador, DURACION_BORRADOR)

    # --- Aprobar y cerrar (CU-05.4) --------------------------------------------------------------

    def aprobar_y_cerrar(self, planilla, usuario):
        with transaction.atomic():
            planilla = Planilla.objects.select_for_update().get(pk=planilla.pk)
            if planilla.estado == Planilla.Estado.CERRADA:
                raise PlanillaCerrada("La planilla ya está cerrada y no admite cambios.")
            lineas, _ = self._calcular(planilla, CalculadoraDescuentos(planilla.gestion_id))
            if not lineas:
                raise ValueError("La planilla no tiene contratos con días trabajados.")
            cantidad, total = GeneradorBoletas().generar(planilla, lineas)
            Anticipo.objects.filter(
                contrato_id__in=[linea.contrato.nro for linea in lineas], planilla__isnull=True,
                fecha__year=planilla.gestion_id, fecha__month=planilla.mes,
            ).update(planilla=planilla)
            planilla.estado = Planilla.Estado.CERRADA
            planilla.fecha_cierre = timezone.localdate()
            planilla.aprobado_por = usuario
            planilla.save(update_fields=["estado", "fecha_cierre", "aprobado_por"])
            auditoria.registrar(
                Bitacora.Operacion.ACTUALIZACION, tabla="PLANILLA", motivo=MOTIVO_CIERRE, usuario=usuario,
                valor_ant={"Nro": planilla.nro, "Estado": Planilla.Estado.PREPLANILLA},
                valor_nuevo={"Nro": planilla.nro, "Estado": Planilla.Estado.CERRADA,
                             "AprobadoPor": usuario.login, "FechaCierre": planilla.fecha_cierre.isoformat()},
            )
            # Una sola ALTA resume las boletas (RNF-04).
            auditoria.registrar(
                Bitacora.Operacion.ALTA, tabla="BOLETA PAGO", usuario=usuario,
                valor_nuevo={"Planilla": planilla.nro, "Boletas": cantidad, "TotalLiquido": str(total)},
            )
        cache.delete(self.clave_borrador(planilla))
        return planilla


def planilla_cerrada_de(anio, mes):
    from .services import planilla_cerrada

    return planilla_cerrada(anio, mes)


class ControladorPlanilla:
    """Datos de las pantallas de CU-05: gestiones, meses y estado de cada planilla."""

    def gestiones(self):
        return list(GestionSalarial.objects.order_by("-anio").values_list("anio", flat=True))

    def meses(self, anio):
        planillas = {p.mes: p for p in Planilla.objects.filter(gestion_id=anio)}
        return [(mes, planillas.get(mes)) for mes in range(1, 13)]
