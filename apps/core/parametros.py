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


class ServicioParametros:
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

    def invalidar(self, anio=None):
        if anio is not None:
            cache.delete(f"{PREFIJO}{anio}")
            return
        from apps.administracion.models import GestionSalarial

        anios = GestionSalarial.objects.values_list("anio", flat=True)
        cache.delete_many([f"{PREFIJO}{a}" for a in anios])


parametros = ServicioParametros()
