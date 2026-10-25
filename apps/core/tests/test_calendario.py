"""Calendario laboral: días hábiles con fines de semana y FERIADO (RF-07, RF-18, RF-30)."""

import datetime

import pytest

from apps.administracion.models import Feriado, Parametro
from apps.core import calendario
from apps.core.parametros import parametros

from .fabricas import FeriadoFactory, UbicacionFactory, gestion

pytestmark = pytest.mark.django_db

D = datetime.date


def test_cp01_fecha_limite_afiliacion():
    """CP-01: inicio viernes 23/10/2026, PLAZO_AFIL = 6 días hábiles, sin feriados → viernes 30/10/2026."""
    plazo = int(parametros.valor("PLAZO_AFIL", 2026))
    assert plazo == 6
    assert calendario.sumar_dias_habiles(D(2026, 10, 23), plazo) == D(2026, 10, 30)


def test_rf07_ejemplo_del_criterio_de_aceptacion():
    """RF-07: ingresa el viernes 6/11/2026 con plazo de 6 días hábiles → vence el viernes 13/11/2026."""
    assert calendario.sumar_dias_habiles(D(2026, 11, 6), 6) == D(2026, 11, 13)


def test_plazo_de_baja_cuenta_el_dia_del_retiro():
    """docs/06: FechaLimBaja = FechaRetiro + PLAZO_BAJA días hábiles; el día del retiro cuenta como día 1."""
    plazo = int(parametros.valor("PLAZO_BAJA", 2026))
    assert plazo == 5
    # Retiro el viernes 23/10/2026: 23, 26, 27, 28 y 29 → jueves 29/10/2026.
    assert calendario.sumar_dias_habiles(D(2026, 10, 23), plazo) == D(2026, 10, 29)


def test_inicio_en_fin_de_semana_cuenta_desde_el_primer_dia_habil():
    # Sábado 24/10/2026: el primer día hábil es el lunes 26/10.
    assert calendario.sumar_dias_habiles(D(2026, 10, 24), 1) == D(2026, 10, 26)


def test_sin_incluir_el_dia_de_inicio():
    assert calendario.sumar_dias_habiles(D(2026, 10, 23), 5, incluye_inicio=False) == D(2026, 10, 30)


def test_feriado_nacional_se_salta():
    FeriadoFactory(fecha=D(2026, 10, 27))
    assert calendario.sumar_dias_habiles(D(2026, 10, 23), 6) == D(2026, 11, 2)


def test_rf18_vacacion_con_feriado_descuenta_4_dias():
    """RF-18: del lunes 2 al viernes 6 de noviembre de 2026, con feriado el 2/11 → 4 días hábiles."""
    FeriadoFactory(fecha=D(2026, 11, 2), descripcion="Todos Santos")
    assert calendario.dias_habiles_entre(D(2026, 11, 2), D(2026, 11, 6)) == 4


def test_rf30_feriado_departamental_solo_en_su_departamento():
    """RF-30: el 24/09 de Santa Cruz no se descuenta en Santa Cruz, pero sí en otros departamentos."""
    santa_cruz = UbicacionFactory(departamento="Santa Cruz")
    la_paz = UbicacionFactory(departamento="La Paz")
    FeriadoFactory(fecha=D(2026, 9, 24), alcance=Feriado.Alcance.DEPARTAMENTAL, ubicacion=santa_cruz)
    # Lunes 21 al viernes 25 de septiembre de 2026.
    assert calendario.dias_habiles_entre(D(2026, 9, 21), D(2026, 9, 25), ubicacion=santa_cruz) == 4
    assert calendario.dias_habiles_entre(D(2026, 9, 21), D(2026, 9, 25), ubicacion=la_paz) == 5
    assert calendario.dias_habiles_entre(D(2026, 9, 21), D(2026, 9, 25)) == 5


def test_dias_lab_parametrizable():
    """Con DIAS_LAB = 6 el sábado es hábil (RF-22)."""
    Parametro.objects.filter(gestion=gestion(), clave="DIAS_LAB").update(valor=6)
    parametros.invalidar()
    assert calendario.es_dia_habil(D(2026, 10, 24))
    assert not calendario.es_dia_habil(D(2026, 10, 25))


def test_dias_habiles_entre_rango_vacio():
    assert calendario.dias_habiles_entre(D(2026, 10, 30), D(2026, 10, 29)) == 0
