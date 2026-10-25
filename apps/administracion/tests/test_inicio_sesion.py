"""CU-16 Iniciar sesión (RF-27, RNF-06, RNF-08)."""

import datetime

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from apps.administracion.models import Bitacora, Usuario
from apps.core.tests.fabricas import CLAVE_PRUEBA, UsuarioFactory

pytestmark = pytest.mark.django_db

URL = "administracion:login"


def intentar(client, login, clave):
    return client.post(reverse(URL), {"username": login, "password": clave}, REMOTE_ADDR="172.16.0.9")


def test_clave_guardada_como_bcrypt_puro():
    usuario = UsuarioFactory()
    assert usuario.password.startswith("$2b$")
    assert len(usuario.password) == 60
    assert usuario.check_password(CLAVE_PRUEBA)
    assert not usuario.check_password("otra")


def test_inicio_exitoso_reinicia_intentos(client):
    usuario = UsuarioFactory(intentos=2)
    respuesta = intentar(client, usuario.login, CLAVE_PRUEBA)
    assert respuesta.status_code == 302
    usuario.refresh_from_db()
    assert usuario.intentos == 0
    assert client.session["_auth_user_id"] == usuario.login


def test_intento_fallido_queda_en_bitacora(client):
    usuario = UsuarioFactory()
    respuesta = intentar(client, usuario.login, "mala")
    assert respuesta.status_code == 200
    usuario.refresh_from_db()
    assert usuario.intentos == 1
    b = Bitacora.objects.get(operacion=Bitacora.Operacion.LOGIN_FALLIDO)
    assert b.usuario == usuario
    assert b.login_intento == usuario.login
    assert b.ip == "172.16.0.9"


def test_login_inexistente_queda_en_bitacora_sin_usuario(client):
    intentar(client, "noexiste", "mala")
    b = Bitacora.objects.get(operacion=Bitacora.Operacion.LOGIN_FALLIDO)
    assert b.usuario is None
    assert b.login_intento == "noexiste"


def test_tercer_intento_bloquea_15_minutos(client):
    """RF-27: tras el tercer intento fallido, "Cuenta bloqueada por 15 minutos" y rechaza la clave correcta."""
    usuario = UsuarioFactory()
    for _ in range(3):
        respuesta = intentar(client, usuario.login, "mala")
    assert "Cuenta bloqueada por 15 minutos" in respuesta.content.decode()
    usuario.refresh_from_db()
    assert usuario.intentos == 3
    restante = usuario.bloq_hasta - timezone.now()
    assert datetime.timedelta(minutes=14) < restante <= datetime.timedelta(minutes=15)
    assert Bitacora.objects.filter(operacion=Bitacora.Operacion.LOGIN_FALLIDO).count() == 3
    assert Bitacora.objects.filter(operacion=Bitacora.Operacion.BLOQUEO, usuario=usuario).count() == 1

    respuesta = intentar(client, usuario.login, CLAVE_PRUEBA)
    assert "Cuenta bloqueada por 15 minutos" in respuesta.content.decode()
    assert "_auth_user_id" not in client.session


def test_bloqueo_vencido_permite_ingresar(client):
    usuario = UsuarioFactory(intentos=3, bloq_hasta=timezone.now() - datetime.timedelta(seconds=1))
    assert intentar(client, usuario.login, CLAVE_PRUEBA).status_code == 302
    usuario.refresh_from_db()
    assert usuario.intentos == 0
    assert usuario.bloq_hasta is None


def test_cuenta_inactiva_no_ingresa(client):
    usuario = UsuarioFactory(activo=False)
    assert intentar(client, usuario.login, CLAVE_PRUEBA).status_code == 200
    assert "_auth_user_id" not in client.session


def test_cierre_de_sesion(client):
    usuario = UsuarioFactory()
    client.force_login(usuario)
    respuesta = client.post(reverse("administracion:logout"))
    assert respuesta.status_code == 302
    assert "_auth_user_id" not in client.session


def test_sesion_expira_a_los_15_minutos_de_inactividad():
    assert settings.SESSION_COOKIE_AGE == 15 * 60
    assert settings.SESSION_SAVE_EVERY_REQUEST is True


def test_inicio_requiere_sesion(client):
    respuesta = client.get(reverse("inicio"))
    assert respuesta.status_code == 302
    assert reverse(URL) in respuesta.url


def test_menu_segun_rol(client):
    from apps.core.tests.fabricas import rol

    client.force_login(UsuarioFactory(rol=rol("Encargado de Pagos")))
    html = client.get(reverse("inicio")).content.decode()
    assert "Planillas" in html
    assert "Seguro CPS" not in html


def test_create_superuser_es_administrador():
    admin = Usuario.objects.create_superuser("admin", CLAVE_PRUEBA)
    assert admin.rol.nombre == "Administrador del Sistema"
    assert admin.check_password(CLAVE_PRUEBA)
