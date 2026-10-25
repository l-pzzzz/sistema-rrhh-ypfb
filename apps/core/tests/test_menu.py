"""Menú por rol (AGENTS.md §7, RNF-07)."""

import pytest
from django.test import RequestFactory

from apps.core.context_processors import menu

from .fabricas import UsuarioFactory, rol

pytestmark = pytest.mark.django_db

# Rol → {opción del menú: solo lectura}. "Reportes" la ven todos (RF-26).
ESPERADO = {
    "Afiliador": {
        "Kardex y Contratos": False,
        "Seguro CPS": False,
        "Evaluaciones": False,
        "Reportes": False,
    },
    "Encargado de Pagos": {
        "Kardex y Contratos": True,
        "Planillas": False,
        "Finiquitos": False,
        "Reportes": False,
    },
    "Responsable de Vacaciones y Lactancias": {
        "Kardex y Contratos": True,
        "Vacaciones y Lactancias": False,
        "Reportes": False,
    },
    "Administrador del Sistema": {
        "Administración": False,
        "Reportes": False,
    },
    "Consulta": {
        "Kardex y Contratos": True,
        "Reportes": False,
    },
}


@pytest.mark.parametrize(("nombre_rol", "esperado"), ESPERADO.items())
def test_menu_por_rol(nombre_rol, esperado):
    request = RequestFactory().get("/")
    request.user = UsuarioFactory(rol=rol(nombre_rol))
    opciones = menu(request)["menu"]
    assert {o["texto"]: o["solo_lectura"] for o in opciones} == esperado


def test_anonimo_sin_menu():
    from django.contrib.auth.models import AnonymousUser

    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    assert menu(request) == {"menu": []}


def test_solo_lectura_se_muestra_en_la_plantilla(client):
    client.force_login(UsuarioFactory(rol=rol("Encargado de Pagos")))
    html = client.get("/").content.decode()
    assert "Kardex y Contratos" in html
    assert "solo lectura" in html
