"""CP-01 y RF-07/RF-08: fechas límite, receptor ControlPlazosCPS y semáforo."""

import pytest

from apps.core.tests.fabricas import CargoFactory, FeriadoFactory
from apps.cps import services
from apps.cps.models import AfiliacionCPS

from .conftest import fecha, nuevo_contrato, registrar, retirar

pytestmark = pytest.mark.django_db


def test_cp01_fecha_limite_viernes_23_10_2026():
    """CP-01: inicia el viernes 23/10/2026, 6 días hábiles, sin feriados → viernes 30/10/2026."""
    afil = registrar(nuevo_contrato("23/10/2026"))
    assert afil.fecha_limite == fecha("30/10/2026")
    assert afil.estado == AfiliacionCPS.Estado.PENDIENTE
    assert afil.tipo == AfiliacionCPS.Tipo.NUEVO


def test_rf07_ingreso_6_11_2026_vence_13_11_2026():
    assert registrar(nuevo_contrato("06/11/2026")).fecha_limite == fecha("13/11/2026")


def test_un_feriado_nacional_corre_la_fecha_limite():
    FeriadoFactory(fecha=fecha("26/10/2026"))
    assert registrar(nuevo_contrato("23/10/2026")).fecha_limite == fecha("02/11/2026")


def test_feriado_departamental_solo_afecta_a_su_departamento():
    cargo_a, cargo_b = CargoFactory(), CargoFactory()
    FeriadoFactory(fecha=fecha("26/10/2026"), alcance="DEPARTAMENTAL", ubicacion=cargo_a.ubicacion)
    assert registrar(nuevo_contrato("23/10/2026", cargo=cargo_a)).fecha_limite == fecha("02/11/2026")
    assert registrar(nuevo_contrato("23/10/2026", cargo=cargo_b)).fecha_limite == fecha("30/10/2026")


def test_la_senal_dos_veces_no_duplica_la_afiliacion():
    contrato = nuevo_contrato("23/10/2026")
    registrar(contrato)
    registrar(contrato)
    assert AfiliacionCPS.objects.filter(contrato=contrato).count() == 1


def test_contrato_de_un_empleado_ya_desafiliado_es_reingreso():
    primero = nuevo_contrato("05/01/2026")
    services.registrar_afiliacion(registrar(primero), "M-1", fecha("06/01/2026"))
    services.registrar_baja(retirar(primero, "30/04/2026"), fecha("05/05/2026"))
    segundo = nuevo_contrato("01/09/2026", empleado=primero.empleado)
    assert registrar(segundo).tipo == AfiliacionCPS.Tipo.REINGRESO


@pytest.mark.parametrize(
    ("hoy", "color", "quedan"),
    [
        ("10/11/2026", "verde", 4),
        ("11/11/2026", "amarillo", 3),
        ("13/11/2026", "amarillo", 1),
        ("16/11/2026", "rojo", 0),
    ],
)
def test_rf07_semaforo(hoy, color, quedan):
    """Plazo vencido el viernes 13/11: amarillo desde el miércoles 11/11 y rojo desde el lunes 16/11."""
    assert services.semaforo(fecha("13/11/2026"), fecha(hoy)) == (color, quedan)


def test_rf08_retiro_calcula_la_fecha_limite_de_baja_y_el_aviso():
    contrato = nuevo_contrato("05/01/2026")
    services.registrar_afiliacion(registrar(contrato), "M-2", fecha("06/01/2026"))
    afil = retirar(contrato, "21/10/2026")  # miércoles; el día del retiro cuenta como día 1
    assert afil.fecha_lim_baja == fecha("27/10/2026")
    assert services.aviso_baja(afil, fecha("21/10/2026")) == (
        "Desafiliación pendiente. Quedan 5 días hábiles para presentar el aviso de baja"
    )
    assert services.semaforo(afil.fecha_lim_baja, fecha("28/10/2026")) == ("rojo", 0)


def test_retiro_sin_afiliacion_deja_la_afiliacion_pendiente_sin_limite_de_baja():
    contrato = nuevo_contrato("05/10/2026")
    registrar(contrato)
    afil = retirar(contrato, "09/10/2026")
    assert afil.estado == AfiliacionCPS.Estado.PENDIENTE
    assert afil.fecha_lim_baja is None
