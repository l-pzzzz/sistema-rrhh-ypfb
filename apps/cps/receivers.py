"""Receptores de las señales de apps.core.senales (Seguro de salud CPS).

CU-04 Gestionar afiliación / desafiliación CPS (RF-07, RF-08).
"""

from apps.core.senales import EventoContrato, ObservadorContrato, TipoEvento, conectar

from . import services


class ControlPlazosCPS(ObservadorContrato):
    """Observador del contrato: fechas límite de afiliación y de baja (docs/06)."""

    def actualizar(self, evento: EventoContrato):
        if evento.tipo == TipoEvento.REGISTRADO:
            services.crear_afiliacion_pendiente(evento.contrato)
        elif evento.tipo == TipoEvento.RETIRADO:
            services.fijar_limite_de_baja(evento.contrato)


control_plazos = conectar(ControlPlazosCPS())
