import importlib
import os

from celery import Celery
from django.core.exceptions import ImproperlyConfigured

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("rrhh")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


def programacion_beat():
    """Une los diccionarios PROGRAMACION de apps/<app>/tasks.py (docs/06, Celery Beat)."""
    import django
    from django.conf import settings

    django.setup()
    programacion = {}
    for nombre in settings.APPS_CON_TAREAS:
        modulo = importlib.import_module(f"apps.{nombre}.tasks")
        repetidas = programacion.keys() & modulo.PROGRAMACION.keys()
        if repetidas:
            raise ImproperlyConfigured(f"Tareas programadas repetidas: {sorted(repetidas)}")
        programacion.update(modulo.PROGRAMACION)
    return programacion


@app.on_after_finalize.connect
def _programar(sender, **kwargs):
    sender.conf.beat_schedule = {**programacion_beat(), **(sender.conf.beat_schedule or {})}
