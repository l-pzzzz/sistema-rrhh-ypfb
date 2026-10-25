"""Menú principal según el nivel y el rol del usuario (RNF-07, AGENTS.md §7).

Cada opción apunta a la URL ``<app>:inicio`` del módulo; mientras el módulo no la defina, la
opción se muestra deshabilitada. ``solo_lectura`` indica a la plantilla que el rol solo consulta
ese módulo; cada módulo además lo exige en sus vistas con ``requiere_nivel``.
"""

from django.urls import NoReverseMatch, reverse

from apps.administracion.models import Rol

from .permisos import tiene_acceso

ADMIN, OPERADOR, CONSULTA = Rol.Nivel.ADMINISTRADOR, Rol.Nivel.OPERADOR, Rol.Nivel.CONSULTA

# (texto, nombre de URL, niveles, roles con escritura, roles de solo lectura).
# Roles vacíos = cualquier rol de esos niveles, con escritura.
OPCIONES = [
    (
        "Kardex y Contratos",
        "kardex:inicio",
        (OPERADOR, CONSULTA),
        (Rol.AFILIADOR,),
        (Rol.ENCARGADO_DE_PAGOS, Rol.RESPONSABLE_VACACIONES, Rol.CONSULTA),
    ),
    ("Seguro CPS", "cps:inicio", (OPERADOR,), (Rol.AFILIADOR,), ()),
    ("Evaluaciones", "finiquitos:evaluaciones", (OPERADOR,), (Rol.AFILIADOR,), ()),
    ("Planillas", "planillas:inicio", (OPERADOR,), (Rol.ENCARGADO_DE_PAGOS,), ()),
    ("Finiquitos", "finiquitos:inicio", (OPERADOR,), (Rol.ENCARGADO_DE_PAGOS,), ()),
    ("Vacaciones y Lactancias", "vacaciones:inicio", (OPERADOR,), (Rol.RESPONSABLE_VACACIONES,), ()),
    ("Administración", "administracion:inicio", (ADMIN,), (), ()),
    ("Reportes", "reportes:inicio", (ADMIN, OPERADOR, CONSULTA), (), ()),
]


def _url(nombre):
    try:
        return reverse(nombre)
    except NoReverseMatch:
        return None


def menu(request):
    usuario = getattr(request, "user", None)
    if usuario is None or not usuario.is_authenticated:
        return {"menu": []}
    opciones = []
    for texto, nombre, niveles, roles_escritura, roles_lectura in OPCIONES:
        solo_lectura = bool(roles_lectura) and tiene_acceso(usuario, niveles, roles_lectura)
        roles = roles_escritura + roles_lectura if roles_escritura else ()
        if tiene_acceso(usuario, niveles, roles):
            opciones.append({"texto": texto, "url": _url(nombre), "solo_lectura": solo_lectura})
    return {"menu": opciones}
