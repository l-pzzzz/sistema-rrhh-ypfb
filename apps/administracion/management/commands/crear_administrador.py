"""Crea la cuenta del Administrador del Sistema pidiendo usuario y contraseña por consola (CU-12, RF-23).

Uso: ``python manage.py crear_administrador``. La contraseña nunca se recibe como argumento.
"""

import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.administracion.models import Bitacora, Rol, Usuario
from apps.core import auditoria

LONGITUD_LOGIN = 30


class Command(BaseCommand):
    help = "Crea un usuario con el rol Administrador del Sistema; pide usuario y contraseña por consola."

    def handle(self, *args, **options):
        login = self._pedir_login()
        clave = self._pedir_clave(login)
        with transaction.atomic():
            usuario = Usuario.objects.create_superuser(login, clave)
            auditoria.registrar(
                Bitacora.Operacion.ALTA,
                tabla="USUARIO",
                valor_nuevo={"Login": usuario.login, "IdRol": usuario.rol_id, "Activo": usuario.activo},
            )
        self.stdout.write(self.style.SUCCESS(f"Administrador «{login}» creado."))

    def _pedir_login(self):
        login = input("Usuario: ").strip()
        if not login:
            raise CommandError("El usuario no puede estar vacío.")
        if len(login) > LONGITUD_LOGIN:
            raise CommandError(f"El usuario admite como máximo {LONGITUD_LOGIN} caracteres.")
        if Usuario.objects.filter(login=login).exists():
            raise CommandError(f"El usuario «{login}» ya existe.")
        if not Rol.objects.filter(nombre=Rol.ADMINISTRADOR_DEL_SISTEMA).exists():
            raise CommandError("No existe el rol Administrador del Sistema: ejecute primero «manage.py migrate».")
        return login

    def _pedir_clave(self, login):
        clave = getpass.getpass("Contraseña: ")
        if clave != getpass.getpass("Repita la contraseña: "):
            raise CommandError("Las contraseñas no coinciden.")
        try:
            validate_password(clave, Usuario(login=login))
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from error
        return clave
