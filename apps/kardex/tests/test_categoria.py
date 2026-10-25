"""RF-03: categoría por antigüedad y recálculo diario con alerta al Afiliador (CA-01)."""

import datetime
from unittest import mock

import pytest
from django.utils import timezone

from apps.administracion.models import Bitacora
from apps.core.tests.fabricas import ContratoFactory, EmpleadoFactory
from apps.kardex import tasks
from apps.kardex.models import Contrato
from apps.kardex.services import ServicioContrato, alertas_categoria, anios_cumplidos

pytestmark = pytest.mark.django_db

INGRESO = datetime.date(2020, 11, 24)


@pytest.mark.parametrize(
    ("hoy", "anios"),
    [
        (datetime.date(2026, 11, 23), 5),
        (datetime.date(2026, 11, 24), 6),
        (datetime.date(2027, 2, 28), 6),
        (datetime.date(2020, 11, 24), 0),
    ],
)
def test_anios_cumplidos(hoy, anios):
    assert anios_cumplidos(INGRESO, hoy) == anios


def test_anios_cumplidos_ingreso_29_de_febrero():
    assert anios_cumplidos(datetime.date(2020, 2, 29), datetime.date(2021, 2, 28)) == 0
    assert anios_cumplidos(datetime.date(2020, 2, 29), datetime.date(2021, 3, 1)) == 1


@pytest.mark.parametrize(("anios", "cod"), [(0, "A"), (5, "A"), (6, "B"), (15, "B"), (16, "C"), (40, "C")])
def test_rangos_de_la_tabla_categoria(anios, cod):
    hoy = datetime.date(2026, 6, 1)
    ingreso = hoy.replace(year=hoy.year - anios)
    assert ServicioContrato().categoria_por_antiguedad(ingreso, hoy).cod == cod


def test_ca01_cambio_de_categoria_al_cumplir_6_anios():
    """CA-01: con 5 años y 11 meses, categoría A; al cumplir 6 años, categoría B y alerta al Afiliador."""
    empleado = EmpleadoFactory(fecha_ingreso=INGRESO)
    contrato = ContratoFactory(empleado=empleado, fecha_inicio=INGRESO)
    servicio = ServicioContrato()

    assert servicio.recalcular_categorias(datetime.date(2026, 10, 24)) == []  # 5 años y 11 meses
    contrato.refresh_from_db()
    assert contrato.categoria_id == "A"

    # La tarea corre a la 01:00 del día en que cumple 6 años.
    madrugada = timezone.make_aware(datetime.datetime(2026, 11, 24, 1, 0))
    with mock.patch("apps.core.auditoria.timezone.now", return_value=madrugada):
        alertas = servicio.recalcular_categorias(datetime.date(2026, 11, 24))
    contrato.refresh_from_db()
    assert contrato.categoria_id == "B"
    assert [a.mensaje for a in alertas] == ["Cambio de categoría: A → B"]

    b = Bitacora.objects.get(operacion=Bitacora.Operacion.ACTUALIZACION, tabla="contrato")
    assert b.motivo == "Cambio de categoría: A → B"
    assert b.usuario is None

    # El Afiliador ve la alerta al día siguiente (RF-03, criterio de aceptación).
    (alerta,) = alertas_categoria(datetime.date(2026, 11, 25))
    assert alerta.mensaje == "Cambio de categoría: A → B"
    assert alerta.ci == empleado.ci
    assert alerta.contrato == contrato.nro


def test_recalculo_ignora_contratos_concluidos():
    empleado = EmpleadoFactory(fecha_ingreso=datetime.date(2000, 1, 3))
    ContratoFactory(empleado=empleado, estado=Contrato.Estado.CONCLUIDO, fecha_retiro=datetime.date(2026, 3, 2))
    assert ServicioContrato().recalcular_categorias(datetime.date(2026, 6, 1)) == []


def test_alerta_se_muestra_30_dias():
    ContratoFactory(empleado=EmpleadoFactory(fecha_ingreso=INGRESO))
    madrugada = timezone.make_aware(datetime.datetime(2026, 11, 24, 1, 0))
    with mock.patch("apps.core.auditoria.timezone.now", return_value=madrugada):
        ServicioContrato().recalcular_categorias(datetime.date(2026, 11, 24))
    assert len(alertas_categoria(datetime.date(2026, 12, 24))) == 1  # 30 días después
    assert alertas_categoria(datetime.date(2026, 12, 25)) == []


def test_alerta_por_correo_a_los_afiliadores(monkeypatch, mailoutbox):
    monkeypatch.setenv("CORREO_AFILIADORES", "uno@ypfb.test, dos@ypfb.test")
    ContratoFactory(empleado=EmpleadoFactory(fecha_ingreso=INGRESO))
    ServicioContrato().recalcular_categorias(datetime.date(2026, 11, 24))
    (correo,) = mailoutbox
    assert correo.to == ["uno@ypfb.test", "dos@ypfb.test"]
    assert "Cambio de categoría: A → B" in correo.body


def test_sin_correo_configurado_solo_pantalla(monkeypatch, mailoutbox):
    monkeypatch.setenv("CORREO_AFILIADORES", "")
    ContratoFactory(empleado=EmpleadoFactory(fecha_ingreso=INGRESO))
    assert len(ServicioContrato().recalcular_categorias(datetime.date(2026, 11, 24))) == 1
    assert mailoutbox == []


def test_sin_cambios_no_envia_correo(monkeypatch, mailoutbox):
    monkeypatch.setenv("CORREO_AFILIADORES", "uno@ypfb.test")
    ContratoFactory(empleado=EmpleadoFactory(fecha_ingreso=INGRESO))
    ServicioContrato().recalcular_categorias(datetime.date(2026, 10, 24))
    assert mailoutbox == []


def test_tarea_programada_diaria():
    assert tasks.PROGRAMACION["kardex-recalcular-categorias"]["task"] == "apps.kardex.tasks.recalcular_categorias"
    horario = tasks.PROGRAMACION["kardex-recalcular-categorias"]["schedule"]
    assert horario.hour == {1} and horario.minute == {0}

    ContratoFactory(empleado=EmpleadoFactory(fecha_ingreso=INGRESO))
    with mock.patch("apps.kardex.tasks.timezone.localdate", return_value=datetime.date(2026, 11, 24)):
        assert tasks.recalcular_categorias() == 1
