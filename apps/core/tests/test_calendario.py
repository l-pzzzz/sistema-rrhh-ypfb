"""Calendario laboral: días hábiles con fines de semana y FERIADO (RF-07, RF-18, RF-30)."""

import datetime

import pytest

from apps.administracion.models import Feriado, GestionSalarial, Parametro
from apps.core import calendario
from apps.core.calendario import CalendarioLaboral
from apps.core.parametros import ParametroNoConfigurado, parametros

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


def test_plazo_que_pasa_a_un_anio_sin_gestion():
    """Plazo que empieza el lunes 28/12/2026 y termina en 2027, sin gestión 2027: usa DIAS_LAB de 2026.

    28, 29, 30 y 31/12, viernes 1/1 (sin feriados registrados) y lunes 4/1/2027.
    """
    assert not GestionSalarial.objects.filter(anio=2027).exists()
    assert calendario.sumar_dias_habiles(D(2026, 12, 28), 6) == D(2027, 1, 4)
    assert calendario.dias_habiles_entre(D(2026, 12, 28), D(2027, 1, 8)) == 10


def test_plazo_que_pasa_a_un_anio_con_gestion_propia():
    """Si la gestión 2027 existe, sus días se cuentan con su propio DIAS_LAB (6: el sábado es hábil)."""
    nueva = GestionSalarial.objects.create(anio=2027)
    Parametro.objects.create(gestion=nueva, clave="DIAS_LAB", valor=6)
    # 28, 29, 30 y 31/12/2026, viernes 1/1/2027 y sábado 2/1/2027.
    assert calendario.sumar_dias_habiles(D(2026, 12, 28), 6) == D(2027, 1, 2)


def test_sin_ninguna_gestion_anterior():
    with pytest.raises(ParametroNoConfigurado):
        calendario.es_dia_habil(D(2020, 3, 2))


def test_calendario_laboral_y_accesos_directos():
    """docs/06: CalendarioLaboral agrupa las tres operaciones; las funciones del módulo son accesos directos."""
    cal = CalendarioLaboral()
    assert cal.sumar_dias_habiles(D(2026, 10, 23), 6) == calendario.sumar_dias_habiles(D(2026, 10, 23), 6)
    assert cal.dias_habiles_entre(D(2026, 10, 19), D(2026, 10, 25)) == calendario.dias_habiles_entre(
        D(2026, 10, 19), D(2026, 10, 25)
    ) == 5
    assert cal.es_dia_habil(D(2026, 10, 23)) is calendario.es_dia_habil(D(2026, 10, 23)) is True
