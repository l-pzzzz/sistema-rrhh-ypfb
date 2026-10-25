"""Fixtures de las pruebas de CPS: contratos de fábrica y la señal emitida a mano (Kardex aún no está unido)."""

import datetime

import pytest

from apps.core.senales import contrato_registrado, contrato_retirado
from apps.core.tests.fabricas import CargoFactory, ContratoFactory, EmpleadoFactory, UsuarioFactory
from apps.cps.models import AfiliacionCPS
from apps.kardex.models import Contrato, ContratoCargo


def fecha(texto):
    """dd/mm/aaaa → date."""
    return datetime.datetime.strptime(texto, "%d/%m/%Y").date()


def nuevo_contrato(inicio="05/01/2026", empleado=None, cargo=None, **campos):
    contrato = ContratoFactory(fecha_inicio=fecha(inicio), empleado=empleado or EmpleadoFactory(), **campos)
    ContratoCargo.objects.create(contrato=contrato, cargo=cargo or CargoFactory())
    return contrato


def registrar(contrato):
    """Emite contrato_registrado como lo hará ServicioContrato y devuelve la afiliación creada."""
    contrato_registrado.send(sender=Contrato, contrato=contrato)
    return AfiliacionCPS.objects.get(contrato=contrato)


def retirar(contrato, retiro):
    """Concluye el contrato, emite contrato_retirado y devuelve la afiliación actualizada."""
    contrato.fecha_retiro = fecha(retiro)
    contrato.tipo_retiro = Contrato.TipoRetiro.VOLUNTARIO
    contrato.estado = Contrato.Estado.CONCLUIDO
    contrato.save()
    contrato_retirado.send(sender=Contrato, contrato=contrato)
    return AfiliacionCPS.objects.get(contrato=contrato)


@pytest.fixture
def afiliador(db):
    return UsuarioFactory(login="afiliador1")
