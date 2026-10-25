"""Patrón Observer del contrato (docs/06): EventoContrato, ObservadorContrato y conectar()."""

import dataclasses
import datetime

import pytest

from apps.core.senales import (
    EventoContrato,
    ObservadorContrato,
    TipoEvento,
    conectar,
    contrato_registrado,
    contrato_retirado,
    desconectar,
)
from apps.kardex.models import Contrato

from .fabricas import ContratoFactory

pytestmark = pytest.mark.django_db


class ObservadorDePrueba(ObservadorContrato):
    def __init__(self):
        self.eventos = []

    def actualizar(self, evento):
        self.eventos.append(evento)


@pytest.fixture
def observador():
    obs = ObservadorDePrueba()
    conectar(obs)
    yield obs
    desconectar(obs)


def test_recibe_contrato_registrado(observador):
    contrato = ContratoFactory(fecha_inicio=datetime.date(2026, 10, 23))
    contrato_registrado.send(sender=Contrato, contrato=contrato)
    assert observador.eventos == [
        EventoContrato(tipo=TipoEvento.REGISTRADO, contrato=contrato, fecha=datetime.date(2026, 10, 23))
    ]


def test_recibe_contrato_retirado(observador):
    contrato = ContratoFactory(
        fecha_inicio=datetime.date(2026, 1, 5),
        fecha_retiro=datetime.date(2026, 10, 23),
        tipo_retiro=Contrato.TipoRetiro.DESPIDO_INJUSTIFICADO,
        motivo_retiro="Reestructuración",
        estado=Contrato.Estado.CONCLUIDO,
    )
    contrato_retirado.send(sender=Contrato, contrato=contrato)
    (evento,) = observador.eventos
    assert evento.tipo is TipoEvento.RETIRADO
    assert evento.contrato == contrato
    assert evento.fecha == datetime.date(2026, 10, 23)


def test_recibe_ambos_eventos_en_orden(observador):
    contrato = ContratoFactory()
    contrato_registrado.send(sender=Contrato, contrato=contrato)
    contrato.fecha_retiro = datetime.date(2026, 6, 30)
    contrato_retirado.send(sender=Contrato, contrato=contrato)
    assert [e.tipo for e in observador.eventos] == [TipoEvento.REGISTRADO, TipoEvento.RETIRADO]


def test_evento_es_inmutable():
    evento = EventoContrato(tipo=TipoEvento.REGISTRADO, contrato=None, fecha=datetime.date(2026, 1, 5))
    with pytest.raises(dataclasses.FrozenInstanceError):
        evento.tipo = TipoEvento.RETIRADO


def test_observador_es_abstracto():
    with pytest.raises(TypeError):
        ObservadorContrato()

    class SinActualizar(ObservadorContrato):
        pass

    with pytest.raises(TypeError):
        SinActualizar()


def test_conectar_dos_veces_no_duplica(observador):
    conectar(observador)
    contrato_registrado.send(sender=Contrato, contrato=ContratoFactory())
    assert len(observador.eventos) == 1


def test_desconectar():
    obs = ObservadorDePrueba()
    conectar(obs)
    desconectar(obs)
    contrato_registrado.send(sender=Contrato, contrato=ContratoFactory())
    assert obs.eventos == []


def test_conectar_rechaza_lo_que_no_es_observador():
    with pytest.raises(TypeError):
        conectar(object())
