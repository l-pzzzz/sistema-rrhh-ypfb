"""Observer (docs/06): ServicioContrato emite contrato_registrado y contrato_retirado."""

import datetime

import pytest

from apps.core.senales import ObservadorContrato, TipoEvento, conectar, desconectar
from apps.core.tests.fabricas import CargoFactory, EmpleadoFactory
from apps.kardex.models import Contrato
from apps.kardex.services import ServicioContrato

pytestmark = pytest.mark.django_db


class ReceptorDePrueba(ObservadorContrato):
    def __init__(self):
        self.eventos = []

    def actualizar(self, evento):
        # El receptor ve el contrato ya guardado, con sus cargos y su estado.
        self.eventos.append((evento, Contrato.objects.get(pk=evento.contrato.pk).estado))


@pytest.fixture
def receptor():
    obs = conectar(ReceptorDePrueba())
    yield obs
    desconectar(obs)


def test_registrar_emite_contrato_registrado(receptor):
    contrato = ServicioContrato().registrar(
        EmpleadoFactory(), datetime.date(2026, 10, 23), None, [CargoFactory()], hoy=datetime.date(2026, 10, 23)
    )
    ((evento, estado),) = receptor.eventos
    assert evento.tipo is TipoEvento.REGISTRADO
    assert evento.contrato == contrato
    assert evento.fecha == datetime.date(2026, 10, 23)
    assert estado == Contrato.Estado.VIGENTE


def test_retiro_emite_contrato_retirado_con_datos_guardados(receptor):
    servicio = ServicioContrato()
    contrato = servicio.registrar(
        EmpleadoFactory(), datetime.date(2026, 1, 5), None, [CargoFactory()], hoy=datetime.date(2026, 1, 5)
    )
    servicio.registrar_retiro(
        contrato, datetime.date(2026, 10, 23), Contrato.TipoRetiro.DESPIDO_INJUSTIFICADO, "Reestructuración"
    )
    evento, estado = receptor.eventos[-1]
    assert evento.tipo is TipoEvento.RETIRADO
    assert evento.fecha == datetime.date(2026, 10, 23)
    assert evento.contrato.tipo_retiro == Contrato.TipoRetiro.DESPIDO_INJUSTIFICADO
    assert evento.contrato.motivo_retiro == "Reestructuración"
    assert estado == Contrato.Estado.CONCLUIDO


def test_rechazo_no_emite_senal(receptor):
    empleado = EmpleadoFactory()
    with pytest.raises(Exception):  # noqa: B017
        ServicioContrato().registrar(empleado, datetime.date(2026, 1, 5), None, [], hoy=datetime.date(2026, 1, 5))
    assert receptor.eventos == []
