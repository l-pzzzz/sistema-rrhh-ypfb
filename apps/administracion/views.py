"""Vistas del módulo Administración (CU-12 a CU-14 y CU-16)."""

from django.contrib.auth import views as auth_views

from .forms import InicioSesionForm


class InicioSesionView(auth_views.LoginView):
    """CU-16 Iniciar sesión (RF-27)."""

    form_class = InicioSesionForm
    template_name = "administracion/login.html"
    redirect_authenticated_user = True


class CierreSesionView(auth_views.LogoutView):
    """Cierre de sesión."""
