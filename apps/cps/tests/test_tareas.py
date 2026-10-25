"""Tarea diaria del semáforo y resumen por correo (RF-07, RF-08, docs/06)."""


import pytest
from django.core import mail
from django.core.cache import cache

from apps.cps import services, tasks

from .conftest import fecha, nuevo_contrato, registrar

pytestmark = pytest.mark.django_db


@pytest.fixture
def hoy(monkeypatch):
    dia = fecha("12/11/2026")
    monkeypatch.setattr("django.utils.timezone.localdate", lambda: dia)
    return dia


def test_programacion_diaria_a_las_6():
    entrada = tasks.PROGRAMACION["actualizar-semaforo-cps"]
    assert entrada["task"] == "apps.cps.tasks.actualizar_semaforo_cps"
    assert (entrada["schedule"].hour, entrada["schedule"].minute) == ({6}, {0})


def test_la_tarea_guarda_el_semaforo_en_cache(hoy):
    afil = registrar(nuevo_contrato("06/11/2026"))  # vence el 13/11
    tasks.actualizar_semaforo_cps()
    assert cache.get(services.CLAVE_SEMAFORO)["datos"][f"A{afil.nro}"] == ("amarillo", 2)


def test_sin_cache_del_dia_se_calcula_en_el_momento(hoy):
    afil = registrar(nuevo_contrato("06/11/2026"))
    assert services.semaforos_en_cache(hoy)[f"A{afil.nro}"] == ("amarillo", 2)
    cache.set(services.CLAVE_SEMAFORO, {"fecha": "2020-01-01", "datos": {}})
    assert services.semaforos_en_cache(hoy)[f"A{afil.nro}"] == ("amarillo", 2)


def test_correo_a_los_afiliadores_con_amarillos_y_rojos(hoy, settings):
    settings.CORREO_AFILIADORES = ["uno@ypfb.test", "dos@ypfb.test"]
    registrar(nuevo_contrato("06/11/2026"))  # amarillo
    registrar(nuevo_contrato("02/11/2026"))  # vencida: rojo
    registrar(nuevo_contrato("12/11/2026"))  # vence el 19/11: verde
    assert tasks.actualizar_semaforo_cps() == 2
    (correo,) = mail.outbox
    assert correo.to == ["uno@ypfb.test", "dos@ypfb.test"]
    assert correo.body.count("[ROJO]") == 1 and correo.body.count("[AMARILLO]") == 1
    assert correo.body.index("[ROJO]") < correo.body.index("[AMARILLO]")


def test_sin_destinatarios_no_envia(hoy, settings):
    settings.CORREO_AFILIADORES = []
    registrar(nuevo_contrato("02/11/2026"))
    assert tasks.actualizar_semaforo_cps() == 0
    assert mail.outbox == []


def test_sin_novedades_no_envia(hoy, settings):
    settings.CORREO_AFILIADORES = ["uno@ypfb.test"]
    registrar(nuevo_contrato("12/11/2026"))
    tasks.actualizar_semaforo_cps()
    assert mail.outbox == []
