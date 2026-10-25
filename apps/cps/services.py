"""Reglas de negocio del módulo Seguro de salud CPS (CU-04).

CU-04 Gestionar afiliación / desafiliación CPS (RF-06, RF-07, RF-08, RF-09).
"""

import datetime
import json

from django.core.cache import cache
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone

from apps.administracion.models import Bitacora
from apps.core import auditoria
from apps.core.calendario import dias_habiles_entre, sumar_dias_habiles
from apps.core.parametros import parametros
from apps.kardex.models import Contrato, ContratoCargo

from .models import AfiliacionCPS

TABLA = "afiliacion_cps"
Estado = AfiliacionCPS.Estado
Tipo = AfiliacionCPS.Tipo

MENSAJE_SIN_CONTRATO = "El empleado no tiene un contrato vigente"
NOTA_CONCLUIDO_SIN_AFILIAR = "Contrato concluido antes de la afiliación"
DIAS_AMARILLO = 2  # RF-07, regla 3: amarillo con 2 o menos días hábiles restantes.
CLAVE_SEMAFORO = "cps:semaforo"


class AfiliacionRechazada(ValueError):
    """Una regla de CU-04 impide la operación; el mensaje se muestra al Afiliador."""


class AvisoIncompleto(AfiliacionRechazada):
    """CU-04, extensión 3a: faltan datos del trabajador o del contrato."""

    def __init__(self, faltantes):
        self.faltantes = faltantes
        super().__init__("Faltan datos para generar el aviso: " + ", ".join(faltantes) + ".")


# --- Plazos y semáforo (RF-07, RF-08) -------------------------------------------------------------


def ubicacion_de(contrato):
    """Departamento del primer cargo del contrato, para los feriados departamentales (docs/06)."""
    primero = ContratoCargo.objects.filter(contrato=contrato).select_related("cargo__ubicacion").order_by("cargo_id")
    primero = primero.first()
    return primero.cargo.ubicacion if primero else None


def fecha_limite(inicio, clave, ubicacion=None):
    """Inicio + plazo (PLAZO_AFIL o PLAZO_BAJA) en días hábiles; el día de inicio cuenta como día 1."""
    plazo = int(parametros.valor_vigente(clave, inicio.year))
    return sumar_dias_habiles(inicio, plazo, ubicacion, incluye_inicio=True)


def semaforo(limite, hoy=None, ubicacion=None):
    """(color, días hábiles restantes contando hoy) de un plazo que vence en ``limite``.

    Verde con más de 2 días hábiles restantes después de hoy, amarillo con 2 o menos y rojo si venció.
    """
    hoy = hoy or timezone.localdate()
    if hoy > limite:
        return "rojo", 0
    restantes = dias_habiles_entre(hoy, limite, ubicacion)
    return ("amarillo" if restantes - 1 <= DIAS_AMARILLO else "verde"), restantes


def mensaje_baja(restantes):
    """Alerta de desafiliación pendiente de RF-08, con el contador de días hábiles."""
    verbo, dias = ("Queda", "día hábil") if restantes == 1 else ("Quedan", "días hábiles")
    return f"Desafiliación pendiente. {verbo} {restantes} {dias} para presentar el aviso de baja"


def aviso_baja(afiliacion, hoy=None):
    _, restantes = semaforo_de(afiliacion, hoy)
    return mensaje_baja(restantes)


def semaforo_de(afiliacion, hoy=None):
    """Semáforo de una afiliación pendiente (alta) o de una baja pendiente."""
    hoy = hoy or timezone.localdate()
    en_baja = afiliacion.estado != Estado.PENDIENTE
    limite = afiliacion.fecha_lim_baja if en_baja else afiliacion.fecha_limite
    return semaforo(limite, hoy, ubicacion_de(afiliacion.contrato))


def clave_semaforo(afil):
    """'A<nro>' si es un alta pendiente, 'B<nro>' si es una baja pendiente y None en los demás casos."""
    contrato_estado = afil.contrato.estado
    if afil.estado == Estado.PENDIENTE and contrato_estado == Contrato.Estado.VIGENTE:
        return f"A{afil.nro}"
    if (afil.estado in (Estado.EN_PLAZO, Estado.FUERA_DE_PLAZO) and contrato_estado == Contrato.Estado.CONCLUIDO
            and afil.fecha_lim_baja and not afil.fecha_desafil):
        return f"B{afil.nro}"
    return None


def altas_pendientes():
    return AfiliacionCPS.objects.filter(estado=Estado.PENDIENTE, contrato__estado=Contrato.Estado.VIGENTE)


def bajas_pendientes():
    return AfiliacionCPS.objects.filter(
        estado__in=(Estado.EN_PLAZO, Estado.FUERA_DE_PLAZO),
        contrato__estado=Contrato.Estado.CONCLUIDO,
        fecha_lim_baja__isnull=False,
        fecha_desafil__isnull=True,
    )


def calcular_semaforos(hoy=None):
    """{'A<nro>' | 'B<nro>': (color, restantes)} de todas las altas y bajas pendientes."""
    hoy = hoy or timezone.localdate()
    datos = {}
    for prefijo, consulta in (("A", altas_pendientes()), ("B", bajas_pendientes())):
        for afil in consulta.select_related("contrato"):
            datos[f"{prefijo}{afil.nro}"] = semaforo_de(afil, hoy)
    return datos


def guardar_semaforos(hoy=None):
    """Tarea diaria (RF-07, RF-08): deja el semáforo del día en la caché."""
    hoy = hoy or timezone.localdate()
    datos = calcular_semaforos(hoy)
    cache.set(CLAVE_SEMAFORO, {"fecha": hoy.isoformat(), "datos": datos}, 60 * 60 * 30)
    return datos


def semaforos_en_cache(hoy=None):
    """Semáforo guardado por la tarea diaria; si no es de hoy, se calcula en el momento."""
    hoy = hoy or timezone.localdate()
    guardado = cache.get(CLAVE_SEMAFORO)
    if guardado and guardado["fecha"] == hoy.isoformat():
        return guardado["datos"]
    return calcular_semaforos(hoy)


# --- Bitácora -------------------------------------------------------------------------------------


def _instantanea(afil, movimiento):
    """Valor para la bitácora; ``nro`` va primero para poder ubicar los movimientos de la afiliación."""
    return {
        "nro": afil.nro,
        "movimiento": movimiento,
        "contrato": afil.contrato_id,
        "tipo": afil.tipo,
        "estado": afil.estado,
        "fecha_limite": afil.fecha_limite,
        "fecha_afil": afil.fecha_afil,
        "matricula": afil.matricula,
        "fecha_lim_baja": afil.fecha_lim_baja,
        "fecha_desafil": afil.fecha_desafil,
    }


def _auditar(operacion, afil, anterior, movimiento, motivo=None):
    auditoria.registrar(
        operacion,
        tabla=TABLA,
        valor_ant=None if anterior is None else json.dumps(anterior, ensure_ascii=False, default=str),
        valor_nuevo=json.dumps(_instantanea(afil, movimiento), ensure_ascii=False, default=str),
        motivo=motivo,
    )


# --- Observer: contrato registrado / retirado -----------------------------------------------------


def _hubo_desafiliacion(empleado):
    return AfiliacionCPS.objects.filter(contrato__empleado=empleado, estado=Estado.DESAFILIADO).exists()


@transaction.atomic
def crear_afiliacion_pendiente(contrato):
    """CU-02 paso 5 → CU-04: afiliación PENDIENTE con su fecha límite (RF-07)."""
    existente = AfiliacionCPS.objects.filter(contrato=contrato).first()
    if existente:
        return existente
    afil = AfiliacionCPS.objects.create(
        contrato=contrato,
        tipo=Tipo.REINGRESO if _hubo_desafiliacion(contrato.empleado) else Tipo.NUEVO,
        fecha_limite=fecha_limite(contrato.fecha_inicio, "PLAZO_AFIL", ubicacion_de(contrato)),
    )
    _auditar(Bitacora.Operacion.ALTA, afil, None, "PENDIENTE")
    return afil


@transaction.atomic
def fijar_limite_de_baja(contrato):
    """Contrato retirado: FechaLimBaja = FechaRetiro + PLAZO_BAJA días hábiles (RF-08).

    Si nunca se afilió, la afiliación sigue PENDIENTE y sin plazo de baja (docs/06, decisiones de C1).
    """
    afil = AfiliacionCPS.objects.filter(contrato=contrato).first()
    if afil is None or afil.estado == Estado.PENDIENTE:
        return afil
    anterior = _instantanea(afil, "")
    afil.fecha_lim_baja = fecha_limite(contrato.fecha_retiro, "PLAZO_BAJA", ubicacion_de(contrato))
    afil.save(update_fields=["fecha_lim_baja"])
    _auditar(
        Bitacora.Operacion.ACTUALIZACION, afil, anterior, "LIMITE_BAJA",
        motivo="Retiro del contrato: fecha límite del aviso de baja",
    )
    return afil


# --- CU-04.2, CU-04.3, CU-04.4 --------------------------------------------------------------------


def _exigir_contrato_vigente(afil):
    if afil.contrato.estado != Contrato.Estado.VIGENTE:
        raise AfiliacionRechazada(MENSAJE_SIN_CONTRATO)


def _exigir_motivo(motivo):
    if not (motivo or "").strip():
        raise AfiliacionRechazada("Indique el motivo de la actualización o corrección.")
    return motivo.strip()


def _exigir_desafiliacion_anterior(afil, tipo):
    if tipo != Tipo.REINGRESO:
        return
    anterior = AfiliacionCPS.objects.filter(
        contrato__empleado=afil.contrato.empleado, estado=Estado.DESAFILIADO
    ).exclude(pk=afil.pk)
    if not anterior.exists():
        raise AfiliacionRechazada("El reingreso exige una desafiliación anterior registrada del mismo empleado.")


def _exigir_matricula_libre(afil, matricula):
    otra = (
        AfiliacionCPS.objects.filter(matricula=matricula, contrato__estado=Contrato.Estado.VIGENTE)
        .exclude(pk=afil.pk)
        .first()
    )
    if otra:
        raise AfiliacionRechazada(
            f"La matrícula {matricula} ya está registrada en el contrato {otra.contrato_id}; corríjala."
        )


def _datos_faltantes(afil):
    empleado, faltantes = afil.contrato.empleado, []
    if not (empleado.nombres and empleado.apellidos):
        faltantes.append("Nombres y apellidos")
    if not empleado.direccion:
        faltantes.append("Domicilio")
    if not ContratoCargo.objects.filter(contrato=afil.contrato).exists():
        faltantes.append("Cargo del contrato")
    return faltantes


@transaction.atomic
def generar_aviso(afil, tipo):
    """CU-04.3 Generar aviso de afiliación (RF-06): PDF del parte de ingreso.

    Valida el contrato vigente, el reingreso y los datos; guarda el tipo elegido.
    """
    from weasyprint import HTML

    _exigir_contrato_vigente(afil)
    _exigir_desafiliacion_anterior(afil, tipo)
    faltantes = _datos_faltantes(afil)
    if faltantes:
        raise AvisoIncompleto(faltantes)
    if afil.tipo != tipo:
        anterior = _instantanea(afil, "")
        afil.tipo = tipo
        afil.save(update_fields=["tipo"])
        _auditar(
            Bitacora.Operacion.ACTUALIZACION, afil, anterior, "TIPO",
            motivo="Tipo de afiliación indicado al generar el aviso",
        )
    cargos = [fila.cargo for fila in ContratoCargo.objects.filter(contrato=afil.contrato).select_related("cargo")]
    html = render_to_string(
        "cps/aviso.html",
        {"afiliacion": afil, "contrato": afil.contrato, "empleado": afil.contrato.empleado, "cargos": cargos,
         "ubicacion": ubicacion_de(afil.contrato), "generado": timezone.localtime()},
    )
    return HTML(string=html).write_pdf()


def _estado_de_alta(afil, fecha_afil):
    return Estado.EN_PLAZO if fecha_afil <= afil.fecha_limite else Estado.FUERA_DE_PLAZO


@transaction.atomic
def registrar_afiliacion(afil, matricula, fecha_afil):
    """CU-04.2 Registrar afiliación y matrícula (RF-06, RF-07): EN PLAZO o FUERA DE PLAZO."""
    afil = AfiliacionCPS.objects.select_for_update().select_related("contrato").get(pk=afil.pk)
    _exigir_contrato_vigente(afil)
    if afil.estado != Estado.PENDIENTE:
        raise AfiliacionRechazada("La afiliación ya está registrada; use actualizar o corregir.")
    matricula = (matricula or "").strip()
    if not matricula:
        raise AfiliacionRechazada("Ingrese la matrícula CPS.")
    _exigir_matricula_libre(afil, matricula)
    anterior = _instantanea(afil, "")
    afil.matricula, afil.fecha_afil, afil.estado = matricula, fecha_afil, _estado_de_alta(afil, fecha_afil)
    afil.save(update_fields=["matricula", "fecha_afil", "estado"])
    _auditar(
        Bitacora.Operacion.ACTUALIZACION, afil, anterior, "AFILIACION",
        motivo="Registro de matrícula y fecha de afiliación (CU-04.2)",
    )
    return afil


@transaction.atomic
def registrar_baja(afil, fecha_desafil):
    """CU-04.4 Registrar aviso de baja (RF-08): la afiliación queda DESAFILIADA."""
    afil = AfiliacionCPS.objects.select_for_update().select_related("contrato").get(pk=afil.pk)
    if not bajas_pendientes().filter(pk=afil.pk).exists():
        raise AfiliacionRechazada("La afiliación no tiene una baja pendiente: el contrato no está retirado.")
    anterior = _instantanea(afil, "")
    afil.fecha_desafil, afil.estado = fecha_desafil, Estado.DESAFILIADO
    afil.save(update_fields=["fecha_desafil", "estado"])
    _auditar(Bitacora.Operacion.BAJA, afil, anterior, "BAJA")
    return afil


@transaction.atomic
def corregir(afil, operacion, motivo, **campos):
    """Actualizar o corregir una afiliación (RF-09, regla 2); exige el motivo y deja el valor anterior y el nuevo.

    Campos admitidos: ``matricula``, ``fecha_afil``, ``fecha_desafil`` y ``tipo``. El estado se recalcula.
    """
    if operacion not in Bitacora.OPERACIONES_CON_MOTIVO:
        raise ValueError("Use ACTUALIZACION o CORRECCION.")
    motivo = _exigir_motivo(motivo)
    afil = AfiliacionCPS.objects.select_for_update().select_related("contrato").get(pk=afil.pk)
    cambios = {c: v for c, v in campos.items() if c in CAMPOS_CORREGIBLES and v not in (None, "")}
    if afil.estado == Estado.PENDIENTE and ("matricula" in cambios or "fecha_afil" in cambios):
        raise AfiliacionRechazada("La afiliación está pendiente: regístrela primero.")
    if "matricula" in cambios:
        _exigir_matricula_libre(afil, cambios["matricula"].strip())
        cambios["matricula"] = cambios["matricula"].strip()
    if "tipo" in cambios:
        _exigir_desafiliacion_anterior(afil, cambios["tipo"])
    anterior = _instantanea(afil, "")
    for campo, valor in cambios.items():
        setattr(afil, campo, valor)
    if afil.fecha_desafil:
        afil.estado = Estado.DESAFILIADO
    elif afil.fecha_afil:
        afil.estado = _estado_de_alta(afil, afil.fecha_afil)
    afil.save()
    _auditar(operacion, afil, anterior, "CORRECCION", motivo=motivo)
    return afil


CAMPOS_CORREGIBLES = ("matricula", "fecha_afil", "fecha_desafil", "tipo")


# --- RF-09: historial -----------------------------------------------------------------------------

ETIQUETAS = {
    "PENDIENTE": "Afiliación pendiente",
    "AFILIACION": "Alta",
    "LIMITE_BAJA": "Plazo de baja",
    "TIPO": "Tipo de aviso",
    "BAJA": "Baja",
    "CORRECCION": "Corrección",
}


def _detalle(movimiento, nuevo, motivo):
    if movimiento == "PENDIENTE":
        return f"Fecha límite de afiliación: {_dmy(nuevo['fecha_limite'])}"
    if movimiento == "AFILIACION":
        return f"Matrícula {nuevo['matricula']} · {nuevo['estado']}"
    if movimiento == "LIMITE_BAJA":
        return f"Fecha límite del aviso de baja: {_dmy(nuevo['fecha_lim_baja'])}"
    if movimiento == "BAJA":
        return "Aviso de baja presentado"
    return motivo or ""


def _dmy(texto):
    try:
        return datetime.date.fromisoformat(texto).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return texto or ""


def _fecha_del_movimiento(movimiento, nuevo):
    clave = {"AFILIACION": "fecha_afil", "BAJA": "fecha_desafil"}.get(movimiento)
    if clave and nuevo.get(clave):
        return datetime.date.fromisoformat(nuevo[clave])
    return None


def historial(empleado):
    """Movimientos de las afiliaciones del empleado en orden cronológico: alta, baja y correcciones.

    Cada fila: ``fecha`` (la del hecho; en altas y bajas la de la CPS), ``registrado`` (fecha y hora de
    la bitácora), ``etiqueta``, ``detalle`` y ``responsable``. Las notas no vienen de la bitácora.
    """
    afiliaciones = list(AfiliacionCPS.objects.filter(contrato__empleado=empleado).select_related("contrato"))
    filas = []
    for afil in afiliaciones:
        registros = Bitacora.objects.filter(tabla=TABLA, valor_nuevo__startswith=f'{{"nro": {afil.nro},')
        for registro in registros.select_related("usuario").order_by("fecha_hora", "id"):
            nuevo = json.loads(registro.valor_nuevo)
            movimiento = nuevo["movimiento"]
            filas.append({
                "fecha": _fecha_del_movimiento(movimiento, nuevo),
                "registrado": registro.fecha_hora,
                "etiqueta": ETIQUETAS[movimiento],
                "detalle": _detalle(movimiento, nuevo, registro.motivo),
                "responsable": registro.usuario.login if registro.usuario_id else "Sistema",
                "contrato": afil.contrato_id,
            })
        if afil.estado == Estado.PENDIENTE and afil.contrato.estado == Contrato.Estado.CONCLUIDO:
            filas.append({
                "fecha": afil.contrato.fecha_retiro,
                "registrado": None,
                "etiqueta": "Nota",
                "detalle": NOTA_CONCLUIDO_SIN_AFILIAR,
                "responsable": "Sistema",
                "contrato": afil.contrato_id,
            })
    ahora = timezone.now()
    filas.sort(key=lambda f: (f["registrado"] is None, f["registrado"] or ahora, f["fecha"] or datetime.date.min))
    return filas
