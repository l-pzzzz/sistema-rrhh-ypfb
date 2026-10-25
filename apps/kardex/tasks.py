"""Tareas programadas del módulo Kardex (docs/06). El integrador une PROGRAMACION a CELERY_BEAT_SCHEDULE."""

from celery import shared_task
from celery.schedules import crontab
from django.utils import timezone

from .services import ServicioContrato

PROGRAMACION = {
    "kardex-recalcular-categorias": {
        "task": "apps.kardex.tasks.recalcular_categorias",
        "schedule": crontab(hour=1, minute=0),
    },
}


@shared_task(name="apps.kardex.tasks.recalcular_categorias")
def recalcular_categorias():
    """RF-03, regla 2: recálculo diario de la categoría por antigüedad; devuelve la cantidad de alertas."""
    return len(ServicioContrato().recalcular_categorias(timezone.localdate()))
