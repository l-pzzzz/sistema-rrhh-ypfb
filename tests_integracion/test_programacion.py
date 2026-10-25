"""Celery Beat: cada tarea programada de docs/06 está en CELERY_BEAT_SCHEDULE (RF-03, RF-07, RF-08, RF-19, RF-25)."""

import pytest
from celery.schedules import crontab

from config.celery import app, programacion_beat

TAREAS_C1 = {
    "RF-03 recalcular categoría (diario 01:00)": ("apps.kardex.tasks.recalcular_categorias", crontab(hour=1, minute=0)),
    "RF-07/RF-08 semáforo CPS (diario 06:00)": ("apps.cps.tasks.actualizar_semaforo_cps", crontab(hour=6, minute=0)),
}


def _programadas():
    app.finalize()
    return {entrada["task"]: entrada["schedule"] for entrada in app.conf.beat_schedule.values()}


@pytest.mark.parametrize(("tarea", "horario"), TAREAS_C1.values(), ids=TAREAS_C1.keys())
def test_tarea_de_docs_06_esta_programada(tarea, horario):
    assert _programadas()[tarea] == horario


def test_celery_beat_schedule_une_las_programaciones_sin_repetir():
    programacion = programacion_beat()
    assert set(programacion) <= set(app.conf.beat_schedule)
    assert len(_programadas()) == len(app.conf.beat_schedule)


@pytest.mark.parametrize("palabra", ["lactancia", "respaldo"])
@pytest.mark.xfail(reason="Pendiente de C2: las tareas de lactancia (RF-19) y respaldo (RF-25) aún no existen.")
def test_tareas_de_c2_programadas(palabra):
    assert any(palabra in tarea for tarea in _programadas())


def test_correo_configurado_para_smtp_con_tls(settings):
    assert settings.EMAIL_PORT == 587
    assert settings.EMAIL_USE_TLS is True
    for nombre in ("CORREO_AFILIADORES", "CORREO_RESP_VACACIONES", "CORREO_ADMINISTRADOR"):
        assert isinstance(getattr(settings, nombre), list)
