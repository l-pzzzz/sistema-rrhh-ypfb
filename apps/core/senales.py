"""Señales del contrato (patrón Observer, docs/06).

Kardex las emite (``ServicioContrato``). CPS, Administración y Finiquitos las escuchan en su
receivers.py con una subclase de ``ObservadorContrato`` (``ControlPlazosCPS``,
``DesactivadorCuenta`` y ``HabilitadorFiniquito``) que suscriben con ``conectar()``::

    class ControlPlazosCPS(ObservadorContrato):
        def actualizar(self, evento):
            ...

    conectar(ControlPlazosCPS())

Las señales de Django siguen siendo el mecanismo; las clases solo dan la forma del patrón del informe.
"""

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass

from django.dispatch import Signal

contrato_registrado = Signal()  # kwargs: contrato
contrato_retirado = Signal()  # kwargs: contrato (con FechaRetiro, TipoRetiro y MotivoRetiro ya guardados)


class TipoEvento(enum.StrEnum):
    REGISTRADO = "REGISTRADO"
    RETIRADO = "RETIRADO"


@dataclass(frozen=True)
class EventoContrato:
    """Datos del evento que recibe cada observador.

    ``fecha`` es la fecha del hecho en el contrato: FechaInicio si se registró y FechaRetiro si se retiró.
    """

    tipo: TipoEvento
    contrato: object
    fecha: object


class ObservadorContrato(ABC):
    """Interfaz de los observadores del contrato."""

    @abstractmethod
    def actualizar(self, evento):
        """Reacciona a un EventoContrato."""


_SENALES = (
    (contrato_registrado, TipoEvento.REGISTRADO, "fecha_inicio"),
    (contrato_retirado, TipoEvento.RETIRADO, "fecha_retiro"),
)


def _uid(observador, tipo):
    return f"observador-contrato-{id(observador)}-{tipo}"


def conectar(observador):
    """Suscribe el observador a contrato_registrado y contrato_retirado.

    Conectar dos veces el mismo observador no lo duplica. Se guarda una referencia fuerte: el
    observador vive mientras esté conectado.
    """
    if not isinstance(observador, ObservadorContrato):
        raise TypeError("Solo se pueden conectar subclases de ObservadorContrato.")
    for senal, tipo, campo_fecha in _SENALES:

        def receptor(sender, contrato, _tipo=tipo, _campo=campo_fecha, **kwargs):
            observador.actualizar(EventoContrato(tipo=_tipo, contrato=contrato, fecha=getattr(contrato, _campo)))

        senal.connect(receptor, weak=False, dispatch_uid=_uid(observador, tipo))
    return observador


def desconectar(observador):
    for senal, tipo, _ in _SENALES:
        senal.disconnect(dispatch_uid=_uid(observador, tipo))
