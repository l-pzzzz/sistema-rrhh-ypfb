"""Fixtures de las pruebas de integración: se usa Kardex real, sin emitir señales a mano."""

import datetime

import pytest

from apps.core.tests.fabricas import CargoFactory, EmpleadoFactory
from apps.kardex.services import ServicioContrato

HOY = datetime.date(2026, 3, 2)


@pytest.fixture
def registrar_contrato(db):
    """Registra un contrato con ServicioContrato (emite contrato_registrado)."""

    def _registrar(inicio=datetime.date(2026, 3, 2), empleado=None):
        empleado = empleado or EmpleadoFactory(fecha_ingreso=inicio)
        return ServicioContrato().registrar(empleado, inicio, None, [CargoFactory()], hoy=HOY)

    return _registrar
