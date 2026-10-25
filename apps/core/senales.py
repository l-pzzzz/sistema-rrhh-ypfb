"""Señales del contrato (patrón Observer, docs/06).

Kardex las emite; CPS, Administración y Finiquitos las escuchan en su receivers.py.
"""

from django.dispatch import Signal

contrato_registrado = Signal()  # kwargs: contrato
contrato_retirado = Signal()  # kwargs: contrato (con FechaRetiro, TipoRetiro y MotivoRetiro ya guardados)
