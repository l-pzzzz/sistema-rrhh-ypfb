"""Control de acceso por nivel y rol (RNF-07).

``@requiere_nivel(Rol.Nivel.OPERADOR, rol="Afiliador")`` exige sesión iniciada, el nivel (o uno
de los niveles de una tupla) y, si se indica, el rol. Un acceso denegado responde 403 y queda en
BITACORA como ACCESO DENEGADO.
"""

from functools import wraps

from django.contrib.auth.views import redirect_to_login

from apps.administracion.models import Bitacora

from . import auditoria
from .views import acceso_denegado


def tiene_acceso(usuario, niveles, roles):
    if not usuario.is_authenticated:
        return False
    return usuario.rol.nivel in niveles and (not roles or usuario.rol.nombre in roles)


def _como_tupla(valor):
    if valor is None:
        return ()
    return (valor,) if isinstance(valor, str) else tuple(valor)


def requiere_nivel(nivel, rol=None):
    niveles = _como_tupla(nivel)
    roles = _como_tupla(rol)

    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not tiene_acceso(request.user, niveles, roles):
                auditoria.registrar(
                    Bitacora.Operacion.ACCESO_DENEGADO,
                    valor_nuevo=request.get_full_path(),
                    usuario=request.user,
                    ip=auditoria.ip_de(request),
                )
                return acceso_denegado(request)
            return vista(request, *args, **kwargs)

        return envoltura

    return decorador
