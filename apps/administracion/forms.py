"""Formularios del módulo Administración (CU-12 a CU-14 y CU-16)."""

from django import forms

from apps.core.auditoria import ip_de

from . import services


class InicioSesionForm(forms.Form):
    """CU-16 Iniciar sesión."""

    username = forms.CharField(label="Usuario", max_length=30)
    password = forms.CharField(label="Contraseña", strip=False, widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.usuario = None
        super().__init__(*args, **kwargs)

    def clean(self):
        datos = super().clean()
        if self.errors:
            return datos
        try:
            self.usuario = services.autenticar(datos["username"], datos["password"], ip_de(self.request))
        except services.AccesoRechazado as error:
            raise forms.ValidationError(str(error)) from error
        return datos

    def get_user(self):
        return self.usuario
