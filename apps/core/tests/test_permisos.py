"""Control de acceso por nivel y rol (RNF-07)."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory

from apps.administracion.models import Bitacora, Rol
from apps.core.permisos import requiere_nivel

from .fabricas import UsuarioFactory, rol

pytestmark = pytest.mark.django_db


@requiere_nivel(Rol.Nivel.OPERADOR, rol="Afiliador")
def vista_afiliador(request):
    return HttpResponse("ok")


@requiere_nivel((Rol.Nivel.OPERADOR, Rol.Nivel.CONSULTA))
def vista_lectura(request):
    return HttpResponse("ok")


def peticion(usuario):
    request = RequestFactory().get("/kardex/", REMOTE_ADDR="10.1.1.1")
    request.user = usuario
    return request


def test_anonimo_va_al_inicio_de_sesion():
    respuesta = vista_afiliador(peticion(AnonymousUser()))
    assert respuesta.status_code == 302
    assert "/login/" in respuesta.url


def test_nivel_y_rol_correctos():
    assert vista_afiliador(peticion(UsuarioFactory(rol=rol("Afiliador")))).status_code == 200


def test_otro_operador_recibe_403_y_queda_en_bitacora():
    usuario = UsuarioFactory(rol=rol("Encargado de Pagos"))
    assert vista_afiliador(peticion(usuario)).status_code == 403
    b = Bitacora.objects.get(operacion=Bitacora.Operacion.ACCESO_DENEGADO)
    assert b.usuario == usuario
    assert b.ip == "10.1.1.1"


def test_administrador_no_entra_a_modulos_de_operador():
    """Separación de funciones (docs/02, nivel Administrador)."""
    usuario = UsuarioFactory(rol=rol("Administrador del Sistema"))
    assert vista_afiliador(peticion(usuario)).status_code == 403


def test_varios_niveles():
    assert vista_lectura(peticion(UsuarioFactory(rol=rol("Consulta")))).status_code == 200
    assert vista_lectura(peticion(UsuarioFactory(rol=rol("Administrador del Sistema")))).status_code == 403
