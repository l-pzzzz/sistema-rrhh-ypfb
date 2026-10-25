"""Tareas programadas del módulo CPS (docs/06): semáforo diario y resumen por correo (RF-07, RF-08)."""

import logging

from celery import shared_task
from celery.schedules import crontab
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from . import services

logger = logging.getLogger(__name__)

# El integrador une este diccionario en CELERY_BEAT_SCHEDULE (docs/06).
PROGRAMACION = {
    "actualizar-semaforo-cps": {
        "task": "apps.cps.tasks.actualizar_semaforo_cps",
        "schedule": crontab(hour=6, minute=0),
    },
}


def destinatarios():
    """Direcciones de CORREO_AFILIADORES (.env), separadas por comas; vacía = solo pantalla."""
    return list(settings.CORREO_AFILIADORES)


def resumen(hoy):
    """Líneas de las altas y bajas en amarillo o rojo, con el semáforo ya calculado."""
    semaforos = services.semaforos_en_cache(hoy)
    lineas = []
    for prefijo, consulta, texto in (
        ("A", services.altas_pendientes(), "Afiliación pendiente"),
        ("B", services.bajas_pendientes(), "Baja pendiente"),
    ):
        for afil in consulta.select_related("contrato__empleado"):
            color, restantes = semaforos.get(f"{prefijo}{afil.nro}") or services.semaforo_de(afil, hoy)
            if color == "verde":
                continue
            limite = afil.fecha_lim_baja if prefijo == "B" else afil.fecha_limite
            empleado = afil.contrato.empleado
            lineas.append(
                (color, f"[{color.upper()}] {texto}: {empleado.apellidos} {empleado.nombres} (CI {empleado.ci}), "
                        f"contrato {afil.contrato_id}, vence el {limite:%d/%m/%Y}, días hábiles restantes: {restantes}")
            )
    lineas.sort(key=lambda linea: linea[0] != "rojo")
    return [texto for _, texto in lineas]


@shared_task(name="apps.cps.tasks.actualizar_semaforo_cps")
def actualizar_semaforo_cps():
    """Actualiza el semáforo y envía a CORREO_AFILIADORES el resumen de amarillos y rojos."""
    hoy = timezone.localdate()
    services.guardar_semaforos(hoy)
    lineas = resumen(hoy)
    para = destinatarios()
    if not lineas:
        return 0
    if not para:
        logger.info("CORREO_AFILIADORES vacío: el resumen de plazos CPS solo se muestra en la bandeja.")
        return 0
    send_mail(
        f"Plazos CPS al {hoy:%d/%m/%Y}: {len(lineas)} afiliaciones o bajas por atender",
        "\n".join(lineas),
        None,
        para,
    )
    return len(lineas)
