"""Parámetros de la gestión: Singleton con caché por año (RF-22, RNF-19)."""

from decimal import Decimal

import pytest

from apps.administracion.models import GestionSalarial, Parametro
from apps.core.parametros import ParametroNoConfigurado, ParametrosSistema, parametros

from .fabricas import gestion

pytestmark = pytest.mark.django_db


def test_es_singleton():
    assert ParametrosSistema() is ParametrosSistema() is parametros


def test_lee_el_valor_de_la_gestion():
    assert parametros.valor("SMN", 2026) == Decimal("1656.00")
    assert parametros.valor("PORC_AFP", 2026) == Decimal("12.21")


def test_usa_cache(django_assert_num_queries):
    parametros.invalidar()
    parametros.valor("SMN", 2026)
    with django_assert_num_queries(0):
        parametros.valor("PORC_IVA", 2026)


def test_cambio_de_parametro_invalida_la_cache():
    assert parametros.valor("SMN", 2026) == Decimal("1656.00")
    p = Parametro.objects.get(gestion=gestion(), clave="SMN")
    p.valor = Decimal("3300.00")
    p.save()
    assert parametros.valor("SMN", 2026) == Decimal("3300.00")


def test_gestion_sin_parametros():
    with pytest.raises(ParametroNoConfigurado):
        parametros.valor("SMN", 1999)


def test_clave_inexistente():
    with pytest.raises(ParametroNoConfigurado):
        parametros.valor("NO_EXISTE", 2026)


def test_todos_de_la_gestion():
    assert len(parametros.todos(2026)) == 11


def test_valor_vigente_usa_la_ultima_gestion_anterior():
    """Sin gestión 2027 se usa el valor de la última gestión configurada (2026)."""
    assert parametros.valor_vigente("DIAS_LAB", 2027) == Decimal("5.00")
    with pytest.raises(ParametroNoConfigurado):
        parametros.valor("DIAS_LAB", 2027)


def test_valor_vigente_prefiere_la_gestion_del_anio():
    nueva = GestionSalarial.objects.create(anio=2027)
    Parametro.objects.create(gestion=nueva, clave="DIAS_LAB", valor=Decimal("6"))
    assert parametros.valor_vigente("DIAS_LAB", 2027) == Decimal("6")


def test_valor_vigente_sin_gestion_anterior():
    with pytest.raises(ParametroNoConfigurado):
        parametros.valor_vigente("DIAS_LAB", 2020)
