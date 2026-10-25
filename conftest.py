import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _cache_limpia():
    """La caché de parámetros no debe pasar de una prueba a otra (cada prueba revierte la base)."""
    cache.clear()
    yield
    cache.clear()
