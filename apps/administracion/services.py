"""Reglas de negocio del módulo Administración (CU-12 a CU-14 y CU-16)."""

import datetime
from functools import cache

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.core import auditoria

from .models import Bitacora, Usuario, cifrar_clave, verificar_clave

MENSAJE_BLOQUEO = "Cuenta bloqueada por {minutos} minutos"
MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos"
MENSAJE_INACTIVA = "La cuenta está inactiva"


class AccesoRechazado(Exception):
    pass


def mensaje_bloqueo():
    return MENSAJE_BLOQUEO.format(minutos=settings.MINUTOS_BLOQUEO)


@cache
def _hash_relleno():
    """Hash para que un login inexistente tarde lo mismo que uno real."""
    return cifrar_clave("relleno")


def autenticar(login, clave, ip):
    """CU-16.1 Validar credenciales y CU-16.3 Bloquear cuenta 15 minutos (RF-27).

    Devuelve el usuario o lanza AccesoRechazado con el mensaje para la pantalla. Los intentos y la
    bitácora se confirman antes de lanzar el rechazo.
    """
    usuario, error = _validar(login, clave, ip)
    if error:
        raise AccesoRechazado(error)
    return usuario


@transaction.atomic
def _validar(login, clave, ip):
    usuario = Usuario.objects.select_for_update().select_related("rol").filter(login=login).first()
    if usuario is None:
        verificar_clave(clave, _hash_relleno())
        auditoria.registrar(Bitacora.Operacion.LOGIN_FALLIDO, tabla="USUARIO", login_intento=login[:30], ip=ip)
        return None, MENSAJE_CREDENCIALES

    ahora = timezone.now()
    if usuario.bloq_hasta and usuario.bloq_hasta > ahora:
        return None, mensaje_bloqueo()
    if usuario.bloq_hasta:
        usuario.bloq_hasta = None
        usuario.intentos = 0

    error = None
    if not usuario.check_password(clave):
        usuario.intentos += 1
        auditoria.registrar(Bitacora.Operacion.LOGIN_FALLIDO, tabla="USUARIO", usuario=usuario,
                            login_intento=login, ip=ip)
        error = MENSAJE_CREDENCIALES
        if usuario.intentos >= settings.MAX_INTENTOS_FALLIDOS:
            usuario.bloq_hasta = ahora + datetime.timedelta(minutes=settings.MINUTOS_BLOQUEO)
            auditoria.registrar(Bitacora.Operacion.BLOQUEO, tabla="USUARIO", usuario=usuario,
                                valor_nuevo={"BloqHasta": usuario.bloq_hasta.isoformat()}, ip=ip)
            error = mensaje_bloqueo()
    elif not usuario.activo:
        error = MENSAJE_INACTIVA
    else:
        usuario.intentos = 0
    usuario.save(update_fields=["intentos", "bloq_hasta"])
    return (None, error) if error else (usuario, None)
