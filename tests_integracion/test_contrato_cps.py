"""Integración Kardex → CPS: CU-02.1 registrar contrato y CU-04 afiliación (RF-02, RF-07)."""

import datetime

import pytest

from apps.cps import services
from apps.cps.models import AfiliacionCPS

pytestmark = pytest.mark.django_db


def test_registrar_contrato_crea_afiliacion_pendiente_con_fecha_limite(registrar_contrato):
    inicio = datetime.date(2026, 3, 2)
    contrato = registrar_contrato(inicio)

    afil = AfiliacionCPS.objects.get(contrato=contrato)
    assert afil.estado == AfiliacionCPS.Estado.PENDIENTE
    assert afil.tipo == AfiliacionCPS.Tipo.NUEVO
    assert afil.fecha_limite == services.fecha_limite(inicio, "PLAZO_AFIL", services.ubicacion_de(contrato))
    assert afil.fecha_limite > inicio
    assert afil in services.altas_pendientes()


def test_un_contrato_registrado_dos_veces_no_duplica_la_afiliacion(registrar_contrato):
    contrato = registrar_contrato()
    services.crear_afiliacion_pendiente(contrato)
    assert AfiliacionCPS.objects.filter(contrato=contrato).count() == 1
