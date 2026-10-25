"""Comando crear_administrador: usuario y contraseña por consola (CU-12, RF-23)."""

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.administracion.models import Bitacora, Usuario
from apps.core.tests.fabricas import CLAVE_PRUEBA, UsuarioFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def consola(monkeypatch):
    """Simula lo que el operador escribe: el usuario y las dos contraseñas."""

    def escribir(login, clave, repetida=None):
        monkeypatch.setattr("builtins.input", lambda _: login)
        claves = iter([clave, clave if repetida is None else repetida])
        monkeypatch.setattr("getpass.getpass", lambda _: next(claves))

    return escribir


def test_crea_administrador(consola):
    consola("jefe.sistemas", CLAVE_PRUEBA)
    call_command("crear_administrador")
    usuario = Usuario.objects.get(login="jefe.sistemas")
    assert usuario.rol.nombre == "Administrador del Sistema"
    assert usuario.activo
    assert usuario.password.startswith("$2b$")
    assert usuario.check_password(CLAVE_PRUEBA)
    b = Bitacora.objects.get(operacion=Bitacora.Operacion.ALTA, tabla="USUARIO")
    assert '"Login": "jefe.sistemas"' in b.valor_nuevo
    assert CLAVE_PRUEBA not in b.valor_nuevo


def test_contrasenas_distintas(consola):
    consola("jefe.sistemas", CLAVE_PRUEBA, repetida=CLAVE_PRUEBA + "x")
    with pytest.raises(CommandError, match="no coinciden"):
        call_command("crear_administrador")
    assert not Usuario.objects.filter(login="jefe.sistemas").exists()


@pytest.mark.parametrize("clave", ["corta1A", "sinmayuscula1", "SinNumeroAlguno"])
def test_rechaza_contrasena_debil(consola, clave):
    """RF-23: al menos 8 caracteres, 1 mayúscula y 1 número."""
    consola("jefe.sistemas", clave)
    with pytest.raises(CommandError):
        call_command("crear_administrador")
    assert not Usuario.objects.filter(login="jefe.sistemas").exists()


def test_usuario_existente(consola):
    UsuarioFactory(login="jefe.sistemas")
    consola("jefe.sistemas", CLAVE_PRUEBA)
    with pytest.raises(CommandError, match="ya existe"):
        call_command("crear_administrador")


def test_usuario_vacio(consola):
    consola("   ", CLAVE_PRUEBA)
    with pytest.raises(CommandError, match="vacío"):
        call_command("crear_administrador")
