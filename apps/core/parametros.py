"""Parámetros legales y de negocio por gestión (patrón Singleton, docs/06; RF-22, RNF-19).

Uso: ``from apps.core.parametros import parametros`` y ``parametros.valor("SMN", anio)``.
Los valores se guardan en la caché de Django (Redis en producción) para que todos los procesos
de Gunicorn y Celery vean el mismo valor; se invalida al guardar un PARAMETRO.
"""

from decimal import Decimal

from django.core.cache import cache

PREFIJO = "parametros:"
DURACION = 60 * 60


class ParametroNoConfigurado(LookupError):
    """La gestión no tiene configurado el parámetro pedido (RF-11, regla 4)."""


class ParametrosSistema:
    """Singleton ParametrosSistema del informe (docs/06); la instancia del módulo es ``parametros``."""

    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
        return cls._instancia

    def todos(self, anio):
        """Diccionario {clave: Decimal} de la gestión."""
        clave_cache = f"{PREFIJO}{anio}"
        valores = cache.get(clave_cache)
        if valores is None:
            from apps.administracion.models import Parametro

            valores = {
                clave: str(valor)
                for clave, valor in Parametro.objects.filter(gestion_id=anio).values_list("clave", "valor")
            }
            cache.set(clave_cache, valores, DURACION)
        return {clave: Decimal(valor) for clave, valor in valores.items()}

    def valor(self, clave, anio):
        valores = self.todos(anio)
        if clave not in valores:
            raise ParametroNoConfigurado(f"El parámetro {clave} no está configurado para la gestión {anio}.")
        return valores[clave]

    def valor_vigente(self, clave, anio):
        """Valor de la gestión ``anio`` o, si no lo tiene, el de la última gestión anterior que lo tenga.

        Solo para cálculos que cruzan a una gestión todavía no configurada (por ejemplo, un plazo en
        días hábiles que termina en el año siguiente). La planilla usa ``valor()``: sin parámetros de
        su gestión no se procesa (RF-11, regla 4).
        """
        try:
            return self.valor(clave, anio)
        except ParametroNoConfigurado:
            from apps.administracion.models import Parametro

            anterior = (
                Parametro.objects.filter(clave=clave, gestion_id__lt=anio)
                .order_by("-gestion_id")
                .values_list("gestion_id", flat=True)
                .first()
            )
            if anterior is None:
                raise
            return self.valor(clave, anterior)

    def invalidar(self, anio=None):
        if anio is not None:
            cache.delete(f"{PREFIJO}{anio}")
            return
        from apps.administracion.models import GestionSalarial

        anios = GestionSalarial.objects.values_list("anio", flat=True)
        cache.delete_many([f"{PREFIJO}{a}" for a in anios])


parametros = ParametrosSistema()
