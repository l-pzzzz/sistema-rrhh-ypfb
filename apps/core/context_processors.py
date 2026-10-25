"""Menú principal según el nivel y el rol del usuario (RNF-07, docs/02 "Niveles de acceso").

Cada opción apunta a la URL ``<app>:inicio`` del módulo; mientras el módulo no la defina, la
opción se muestra deshabilitada.
"""

from django.urls import NoReverseMatch, reverse

from apps.administracion.models import Rol

from .permisos import tiene_acceso

ADMIN, OPERADOR, CONSULTA = Rol.Nivel.ADMINISTRADOR, Rol.Nivel.OPERADOR, Rol.Nivel.CONSULTA

# (texto, nombre de URL, niveles, roles) — roles vacío = cualquier rol del nivel.
OPCIONES = [
    ("Kardex", "kardex:inicio", (OPERADOR, CONSULTA), ("Afiliador", "Consulta")),
    ("Seguro CPS", "cps:inicio", (OPERADOR,), ("Afiliador",)),
    ("Evaluaciones", "finiquitos:evaluaciones", (OPERADOR,), ("Afiliador",)),
    ("Planillas", "planillas:inicio", (OPERADOR,), ("Encargado de Pagos",)),
    ("Finiquitos", "finiquitos:inicio", (OPERADOR,), ("Encargado de Pagos",)),
    ("Vacaciones y Lactancias", "vacaciones:inicio", (OPERADOR,), ("Responsable de Vacaciones y Lactancias",)),
    ("Administración", "administracion:inicio", (ADMIN,), ()),
    ("Reportes", "reportes:inicio", (ADMIN, OPERADOR, CONSULTA), ()),
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
    return {
        "menu": [
            {"texto": texto, "url": _url(nombre)}
            for texto, nombre, niveles, roles in OPCIONES
            if tiene_acceso(usuario, niveles, roles)
        ]
    }
