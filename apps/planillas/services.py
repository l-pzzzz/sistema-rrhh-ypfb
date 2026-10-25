"""Reglas de negocio del módulo Planillas de sueldos (CU-05 a CU-07)."""

from decimal import ROUND_HALF_UP, Decimal

from django.db import IntegrityError, transaction

from apps.administracion.models import Bitacora
from apps.core import auditoria
from apps.core.parametros import parametros
from apps.kardex.models import AjusteSalarial, Contrato

from .models import Anticipo, FormularioF110, Planilla

DOS_CENTAVOS = Decimal("0.01")
CIEN = Decimal("100")

# Reglas del caso que no están entre los 11 parámetros de docs/04 (ver dudas del PR).
DIA_LIMITE = 15  # RF-14 y RF-15: el F110 y el anticipo se cuentan a partir del día 15.
TOPE_ANTICIPO = Decimal("0.50")  # RF-15 regla 2: 50 % del haber básico de la categoría.


class PlanillaCerrada(Exception):
    """La planilla del mes está CERRADA y no admite cambios (RF-11)."""


class ContratoNoVigente(Exception):
    """El empleado no tiene un contrato vigente."""


class HaberNoConfigurado(LookupError):
    """La gestión no tiene haber básico para la categoría (RF-11, regla 4)."""


class AnticipoRechazado(Exception):
    """El anticipo no cumple la fecha o el tope (RF-15)."""


class F110Rechazado(Exception):
    """El formulario F110 no cumple las reglas del RF-14."""


def redondear(valor):
    """Importes con ROUND_HALF_UP a 2 decimales (AGENTS.md §5)."""
    return Decimal(valor).quantize(DOS_CENTAVOS, rounding=ROUND_HALF_UP)


def bs(monto):
    """Formato boliviano: 3.000,00."""
    texto = f"{redondear(monto):,.2f}"
    return texto.replace(",", "\0").replace(".", ",").replace("\0", ".")


def haber_basico(contrato, anio):
    """Haber básico de la categoría del contrato en la gestión (AJUSTE SALARIAL)."""
    haber = AjusteSalarial.objects.filter(categoria_id=contrato.categoria_id, gestion_id=anio).values_list(
        "haber_basico", flat=True
    ).first()
    if haber is None:
        raise HaberNoConfigurado(
            f"No hay haber básico para la categoría {contrato.categoria_id} en la gestión {anio}."
        )
    return haber


def contrato_vigente_por_ci(ci):
    """CU-01.1: contrato vigente del empleado buscado por su CI."""
    contrato = (
        Contrato.objects.select_related("empleado", "categoria")
        .filter(empleado_id=str(ci).strip(), estado=Contrato.Estado.VIGENTE)
        .first()
    )
    if contrato is None:
        raise ContratoNoVigente("El empleado no tiene un contrato vigente")
    return contrato


def planilla_cerrada(anio, mes):
    return Planilla.objects.filter(gestion_id=anio, mes=mes, estado=Planilla.Estado.CERRADA).exists()


def _mes_siguiente(anio, mes):
    return (anio + 1, 1) if mes == 12 else (anio, mes + 1)


def _mes_anterior(anio, mes):
    return (anio - 1, 12) if mes == 1 else (anio, mes - 1)


class ServicioAnticipos:
    """CU-06 Registrar anticipo (RF-15, RN-06)."""

    def registrar(self, contrato, fecha, monto, usuario=None):
        monto = redondear(monto)
        if contrato.estado != Contrato.Estado.VIGENTE:
            raise ContratoNoVigente("El empleado no tiene un contrato vigente")
        if monto <= 0:
            raise AnticipoRechazado("El monto del anticipo debe ser mayor a 0.")
        if fecha.day <= DIA_LIMITE:
            raise AnticipoRechazado(f"El anticipo solo se registra después del día {DIA_LIMITE} del mes.")
        if planilla_cerrada(fecha.year, fecha.month):
            raise AnticipoRechazado("La planilla del mes está cerrada.")
        tope = redondear(haber_basico(contrato, fecha.year) * TOPE_ANTICIPO)
        acumulado = sum(
            Anticipo.objects.filter(contrato=contrato, fecha__year=fecha.year, fecha__month=fecha.month)
            .values_list("monto", flat=True),
            Decimal("0"),
        )
        if acumulado + monto > tope:
            raise AnticipoRechazado(
                f"La suma de los anticipos del mes supera el 50 % del haber básico (Bs {bs(tope)})."
            )
        with transaction.atomic():
            anticipo = Anticipo.objects.create(contrato=contrato, fecha=fecha, monto=monto)
            auditoria.registrar(
                Bitacora.Operacion.ALTA,
                tabla="ANTICIPO",
                valor_nuevo={"Nro": anticipo.nro, "NroCon": contrato.nro, "Fecha": fecha.isoformat(),
                             "Monto": str(monto)},
                usuario=usuario,
            )
        return anticipo

    def pendientes(self, anio, mes):
        """{nro de contrato: suma de anticipos} del mes que aún no se descontaron."""
        totales = {}
        filas = Anticipo.objects.filter(fecha__year=anio, fecha__month=mes, planilla__isnull=True)
        for contrato_id, monto in filas.values_list("contrato_id", "monto"):
            totales[contrato_id] = totales.get(contrato_id, Decimal("0")) + monto
        return totales


class ServicioF110:
    """CU-07 Registrar formulario F110 (RF-13, RF-14)."""

    def credito(self, facturas, anio):
        """CU-07.1: crédito fiscal = PORC_IVA de las facturas."""
        return redondear(Decimal(facturas) * parametros.valor("PORC_IVA", anio) / CIEN)

    @staticmethod
    def mes_de_aplicacion(f110):
        """(año, mes) de la planilla donde se aplica: hasta el día 15 el mes declarado; después, el siguiente."""
        if f110.fecha_pres.day <= DIA_LIMITE:
            return f110.anio, f110.mes
        return _mes_siguiente(f110.anio, f110.mes)

    def registrar(self, contrato, anio, mes, monto_facturas, fecha_pres, usuario=None):
        monto = redondear(monto_facturas)
        if monto < 0:
            raise F110Rechazado("El monto de las facturas no puede ser negativo.")
        if not 1 <= mes <= 12:
            raise F110Rechazado("El mes declarado debe estar entre 1 y 12.")
        if contrato.estado != Contrato.Estado.VIGENTE:
            raise ContratoNoVigente("El empleado no tiene un contrato vigente")
        if FormularioF110.objects.filter(contrato=contrato, anio=anio, mes=mes).exists():
            raise F110Rechazado("El contrato ya tiene un F110 para ese mes.")
        f110 = FormularioF110(contrato=contrato, anio=anio, mes=mes, monto_fact=monto, fecha_pres=fecha_pres)
        if planilla_cerrada(*self.mes_de_aplicacion(f110)):
            raise F110Rechazado("La planilla donde se aplicaría este F110 está cerrada.")
        try:
            with transaction.atomic():
                f110.save()
                auditoria.registrar(
                    Bitacora.Operacion.ALTA,
                    tabla="FORMULARIO F110",
                    valor_nuevo={"Nro": f110.nro, "NroCon": contrato.nro, "Año": anio, "Mes": mes,
                                 "MontoFact": str(monto), "FechaPres": fecha_pres.isoformat()},
                    usuario=usuario,
                )
        except IntegrityError as error:
            raise F110Rechazado("El contrato ya tiene un F110 para ese mes.") from error
        return f110

    def facturas_aplicables(self, anio, mes):
        """{nro de contrato: monto de facturas} que se aplica a la planilla (anio, mes)."""
        anio_ant, mes_ant = _mes_anterior(anio, mes)
        aplicables = {}
        propios = FormularioF110.objects.filter(anio=anio, mes=mes, fecha_pres__day__lte=DIA_LIMITE)
        tardios = FormularioF110.objects.filter(anio=anio_ant, mes=mes_ant, fecha_pres__day__gt=DIA_LIMITE)
        for f110 in (*propios, *tardios):
            aplicables[f110.contrato_id] = f110.monto_fact
        return aplicables

