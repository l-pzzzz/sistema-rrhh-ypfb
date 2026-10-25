"""Backend de autenticación sobre USUARIO (CU-16, RF-27)."""

from apps.core.auditoria import ip_de

from . import services
from .models import Usuario


class BackendUsuario:
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        ip = ip_de(request) if request is not None else None
        try:
            return services.autenticar(username, password, ip)
        except services.AccesoRechazado:
            return None

    def get_user(self, user_id):
        usuario = Usuario.objects.select_related("rol").filter(pk=user_id).first()
        return usuario if usuario is not None and usuario.activo else None
