"""Fidelidad del modelo de datos con el informe (docs/05 y docs/esquema/schema.json).

Esta prueba no se modifica para que pase (AGENTS.md §4): si falla, el error está en los modelos.
Todo lo esperado se lee de docs/; no hay nombres de tabla ni de columna escritos a mano.
"""

import json
import re
from pathlib import Path

import pytest
from django.apps import apps
from django.conf import settings
from django.db import connection
from django.db.models import CompositePrimaryKey

DOCS = Path(settings.BASE_DIR) / "docs"
ESQUEMA = json.loads((DOCS / "esquema" / "schema.json").read_text(encoding="utf-8"))["tables"]
TABLA_APP = json.loads((DOCS / "esquema" / "tabla_app.json").read_text(encoding="utf-8"))
APPS_NEGOCIO = {"kardex", "cps", "planillas", "vacaciones", "finiquitos", "administracion", "reportes"}


def _clases_docs05():
    """Lee la tabla "Tabla → app de Django → clase" de docs/05."""
    texto = (DOCS / "05_modelo_de_datos.md").read_text(encoding="utf-8")
    filas = re.findall(r"^\| ([A-Z0-9 ]+) \| `(\w+)` \| `(\w+)` \|$", texto, flags=re.MULTILINE)
    return {tabla: (app, clase) for tabla, app, clase in filas}


CLASES = _clases_docs05()


def nombre_db_table(tabla):
    """Convención de docs/05: minúsculas y guion bajo (CONTRATO CARGO → contrato_cargo)."""
    return tabla.lower().replace(" ", "_")


def modelo_de(tabla):
    app, clase = CLASES[tabla]
    return apps.get_model(app, clase)


def columnas_del_modelo(modelo):
    return {f.column: f for f in modelo._meta.local_concrete_fields if f.column is not None}


def columnas_pk(modelo):
    pk = modelo._meta.pk
    if isinstance(pk, CompositePrimaryKey):
        return {f.column for f in pk.fields}
    return {pk.column}


TABLAS = sorted(ESQUEMA)


def test_hay_30_tablas_en_el_esquema_y_en_docs05():
    assert len(ESQUEMA) == 30
    assert set(CLASES) == set(ESQUEMA)
    assert {t: app for t, (app, _) in CLASES.items()} == TABLA_APP


def test_exactamente_30_modelos_de_negocio():
    modelos = [
        m
        for m in apps.get_models()
        if m._meta.app_label in APPS_NEGOCIO and not m._meta.auto_created
    ]
    assert sorted(m._meta.db_table for m in modelos) == sorted(nombre_db_table(t) for t in ESQUEMA)


@pytest.mark.parametrize("tabla", TABLAS)
def test_modelo_app_y_db_table(tabla):
    app, clase = CLASES[tabla]
    modelo = modelo_de(tabla)
    assert modelo.__name__ == clase
    assert modelo._meta.app_label == TABLA_APP[tabla] == app
    assert modelo._meta.db_table == nombre_db_table(tabla)


@pytest.mark.parametrize("tabla", TABLAS)
def test_columnas_exactas(tabla):
    esperadas = {col[0] for col in ESQUEMA[tabla]["cols"]}
    assert set(columnas_del_modelo(modelo_de(tabla))) == esperadas


@pytest.mark.parametrize("tabla", TABLAS)
def test_clave_primaria(tabla):
    esperadas = {col[0] for col in ESQUEMA[tabla]["cols"] if "PK" in col[2]}
    assert columnas_pk(modelo_de(tabla)) == esperadas


@pytest.mark.parametrize("tabla", TABLAS)
def test_claves_foraneas(tabla):
    columnas = columnas_del_modelo(modelo_de(tabla))
    for nombre, _tipo, clave, _nulo, _desc, ref in ESQUEMA[tabla]["cols"]:
        campo = columnas[nombre]
        if "FK" in clave:
            tabla_ref, col_ref = ref.split(".")
            assert campo.is_relation, f"{tabla}.{nombre} debe ser FK"
            assert campo.related_model._meta.db_table == nombre_db_table(tabla_ref)
            assert campo.target_field.column == col_ref
        else:
            assert not campo.is_relation, f"{tabla}.{nombre} no debe ser FK"


@pytest.mark.parametrize("tabla", TABLAS)
def test_nulabilidad(tabla):
    columnas = columnas_del_modelo(modelo_de(tabla))
    for nombre, _tipo, _clave, nulo, *_ in ESQUEMA[tabla]["cols"]:
        assert columnas[nombre].null is nulo, f"{tabla}.{nombre}: null debe ser {nulo}"


# Equivalencia explícita entre los tipos del informe y los que Django genera en MySQL 8.
TIPOS_MYSQL = {
    "INT": "integer",
    "BIGINT": "bigint",
    "SMALLINT": "smallint",
    "TINYINT": "tinyint",
    "DATE": "date",
    "DATETIME": "datetime(6)",
    "BOOLEAN": "bool",
    "TEXT": "longtext",
}


def tipo_esperado(tipo):
    m = re.fullmatch(r"(VARCHAR|CHAR|DECIMAL)\((.+)\)", tipo)
    if m:
        base = {"VARCHAR": "varchar", "CHAR": "char", "DECIMAL": "numeric"}[m.group(1)]
        return f"{base}({m.group(2).replace(' ', '')})"
    return TIPOS_MYSQL[tipo]


def tipo_real(campo):
    tipo = campo.db_type(connection).lower().replace(" auto_increment", "")
    return tipo.replace(" ", "")


@pytest.mark.skipif(connection.vendor != "mysql", reason="los tipos se verifican en MySQL 8")
@pytest.mark.django_db  # db_type() consulta la versión del servidor MySQL.
@pytest.mark.parametrize("tabla", TABLAS)
def test_tipos(tabla):
    columnas = columnas_del_modelo(modelo_de(tabla))
    for nombre, tipo, *_ in ESQUEMA[tabla]["cols"]:
        assert tipo_real(columnas[nombre]) == tipo_esperado(tipo), f"{tabla}.{nombre}"


@pytest.mark.django_db
@pytest.mark.parametrize("tabla", TABLAS)
def test_tabla_creada_por_las_migraciones(tabla):
    """La base real (después de migrar) tiene la tabla con esas columnas y nulabilidad."""
    with connection.cursor() as cursor:
        descripcion = connection.introspection.get_table_description(cursor, nombre_db_table(tabla))
    reales = {c.name: c.null_ok for c in descripcion}
    esperadas = {col[0]: col[3] for col in ESQUEMA[tabla]["cols"]}
    assert reales == esperadas
