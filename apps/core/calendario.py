"""Calendario laboral: días hábiles según DIAS_LAB y FERIADO (RF-07, RF-08, RF-17, RF-18, RF-30).

Un día es hábil si cae dentro de los DIAS_LAB primeros días de la semana (5 = lunes a viernes)
y no es feriado nacional ni feriado departamental de la ubicación indicada.

``CalendarioLaboral`` es la clase del informe (docs/06). Las funciones del módulo
(``sumar_dias_habiles``, ``dias_habiles_entre`` y ``es_dia_habil``) son accesos directos a una
instancia compartida.
"""

import datetime

from django.db.models import Q

from .parametros import parametros

UN_DIA = datetime.timedelta(days=1)


class CalendarioLaboral:
    def es_dia_habil(self, fecha, ubicacion=None):
        return self._es_laborable(fecha, {}) and fecha not in self._feriados(fecha, fecha, ubicacion)

    def dias_habiles_entre(self, desde, hasta, ubicacion=None):
        """Cantidad de días hábiles entre dos fechas, ambas incluidas."""
        if hasta < desde:
            return 0
        feriados = self._feriados(desde, hasta, ubicacion)
        dias_lab = {}
        total = 0
        fecha = desde
        while fecha <= hasta:
            if self._es_laborable(fecha, dias_lab) and fecha not in feriados:
                total += 1
            fecha += UN_DIA
        return total

    def sumar_dias_habiles(self, inicio, dias, ubicacion=None, incluye_inicio=True):
        """Fecha del día hábil número ``dias``.

        Con ``incluye_inicio`` el día de inicio, si es hábil, cuenta como día 1 (RF-07, regla 1, y
        plazo de baja, docs/06); sin él, se cuenta desde el día siguiente.
        """
        if dias < 1:
            raise ValueError("La cantidad de días hábiles debe ser mayor a 0.")
        fecha = inicio if incluye_inicio else inicio + UN_DIA
        # Los feriados se traen por tramos para no consultar día por día.
        tramo = datetime.timedelta(days=dias * 2 + 30)
        limite = fecha + tramo
        feriados = self._feriados(fecha, limite, ubicacion)
        dias_lab = {}
        contados = 0
        while True:
            if fecha > limite:
                feriados |= self._feriados(limite + UN_DIA, limite + tramo, ubicacion)
                limite += tramo
            if self._es_laborable(fecha, dias_lab) and fecha not in feriados:
                contados += 1
                if contados == dias:
                    return fecha
            fecha += UN_DIA

    @staticmethod
    def _dias_laborables(anio):
        """DIAS_LAB de la gestión; si la gestión no existe, el de la última gestión anterior configurada."""
        return int(parametros.valor_vigente("DIAS_LAB", anio))

    def _es_laborable(self, fecha, dias_lab):
        """``dias_lab`` guarda DIAS_LAB por año durante un mismo cálculo."""
        if fecha.year not in dias_lab:
            dias_lab[fecha.year] = self._dias_laborables(fecha.year)
        return fecha.weekday() < dias_lab[fecha.year]

    @staticmethod
    def _feriados(desde, hasta, ubicacion):
        from apps.administracion.models import Feriado

        filtro = Q(alcance=Feriado.Alcance.NACIONAL)
        if ubicacion is not None:
            filtro |= Q(alcance=Feriado.Alcance.DEPARTAMENTAL, ubicacion=ubicacion)
        return set(Feriado.objects.filter(filtro, fecha__range=(desde, hasta)).values_list("fecha", flat=True))


calendario_laboral = CalendarioLaboral()

sumar_dias_habiles = calendario_laboral.sumar_dias_habiles
dias_habiles_entre = calendario_laboral.dias_habiles_entre
es_dia_habil = calendario_laboral.es_dia_habil
