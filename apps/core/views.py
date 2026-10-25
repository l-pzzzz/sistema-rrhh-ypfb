"""Vistas comunes: página de inicio y error 403."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def inicio(request):
    """CU-16.2: el usuario accede al menú de su rol."""
    return render(request, "inicio.html")


def acceso_denegado(request, exception=None):
    return render(request, "403.html", status=403)
