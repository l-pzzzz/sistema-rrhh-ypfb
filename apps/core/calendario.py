"""Calendario laboral: días hábiles según DIAS_LAB y FERIADO (RF-07, RF-08, RF-17, RF-18, RF-30).

Un día es hábil si cae dentro de los DIAS_LAB primeros días de la semana (5 = lunes a viernes)
y no es feriado nacional ni feriado departamental de la ubicación indicada.
"""

import datetime

from django.db.models import Q

from .parametros import parametros

UN_DIA = datetime.timedelta(days=1)


def _feriados(desde, hasta, ubicacion):
    from apps.administracion.models import Feriado

    filtro = Q(alcance=Feriado.Alcance.NACIONAL)
    if ubicacion is not None:
        filtro |= Q(alcance=Feriado.Alcance.DEPARTAMENTAL, ubicacion=ubicacion)
    return set(Feriado.objects.filter(filtro, fecha__range=(desde, hasta)).values_list("fecha", flat=True))


def _es_laborable(fecha):
    return fecha.weekday() < int(parametros.valor("DIAS_LAB", fecha.year))


def es_dia_habil(fecha, ubicacion=None):
    return _es_laborable(fecha) and fecha not in _feriados(fecha, fecha, ubicacion)


def dias_habiles_entre(desde, hasta, ubicacion=None):
    """Cantidad de días hábiles entre dos fechas, ambas incluidas."""
    if hasta < desde:
        return 0
    feriados = _feriados(desde, hasta, ubicacion)
    total = 0
    fecha = desde
    while fecha <= hasta:
        if _es_laborable(fecha) and fecha not in feriados:
            total += 1
        fecha += UN_DIA
    return total


def sumar_dias_habiles(inicio, dias, ubicacion=None, incluye_inicio=True):
    """Fecha del día hábil número ``dias``.

    Con ``incluye_inicio`` el día de inicio, si es hábil, cuenta como día 1 (RF-07, regla 1);
    sin él, se cuenta desde el día siguiente.
    """
    if dias < 1:
        raise ValueError("La cantidad de días hábiles debe ser mayor a 0.")
    fecha = inicio if incluye_inicio else inicio + UN_DIA
    # Los feriados se traen por tramos para no consultar día por día.
    tramo = datetime.timedelta(days=dias * 2 + 30)
    limite = fecha + tramo
    feriados = _feriados(fecha, limite, ubicacion)
    contados = 0
    while True:
        if fecha > limite:
            feriados |= _feriados(limite + UN_DIA, limite + tramo, ubicacion)
            limite += tramo
        if _es_laborable(fecha) and fecha not in feriados:
            contados += 1
            if contados == dias:
                return fecha
        fecha += UN_DIA
