"""Formularios del módulo Seguro de salud CPS (CU-04)."""

from django import forms

from apps.administracion.models import Bitacora
from apps.kardex.models import Ubicacion

from .models import AfiliacionCPS

FORMATOS_FECHA = ["%d/%m/%Y", "%Y-%m-%d"]


def campo_fecha(etiqueta, **opciones):
    return forms.DateField(
        label=etiqueta,
        input_formats=FORMATOS_FECHA,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}, format="%Y-%m-%d"),
        **opciones,
    )


class FiltroBandejaForm(forms.Form):
    """CU-04.1: búsqueda (CU-01.1) y filtros de la bandeja de control (RF-07)."""

    PESTANAS = [("altas", "Altas pendientes"), ("bajas", "Bajas pendientes"), ("todas", "Todas")]
    SEMAFOROS = [("", "Todos"), ("verde", "En plazo"), ("amarillo", "Próximas a vencer"), ("rojo", "Vencidas")]

    pestana = forms.ChoiceField(choices=PESTANAS, required=False)
    q = forms.CharField(label="CI, código o nombre", required=False, max_length=60,
                        widget=forms.TextInput(attrs={"class": "form-control"}))
    semaforo = forms.ChoiceField(label="Estado del plazo", choices=SEMAFOROS, required=False,
                                 widget=forms.Select(attrs={"class": "form-select"}))
    estado = forms.ChoiceField(label="Estado de la afiliación", required=False,
                               choices=[("", "Todos"), *AfiliacionCPS.Estado.choices],
                               widget=forms.Select(attrs={"class": "form-select"}))
    desde = campo_fecha("Fecha límite desde", required=False)
    hasta = campo_fecha("Fecha límite hasta", required=False)
    departamento = forms.ModelChoiceField(label="Departamento", queryset=Ubicacion.objects.order_by("departamento"),
                                          required=False, empty_label="Todos",
                                          widget=forms.Select(attrs={"class": "form-select"}))


class TipoAvisoForm(forms.Form):
    """CU-04 paso 3: tipo de afiliación del aviso."""

    tipo = forms.ChoiceField(label="Tipo de afiliación", choices=AfiliacionCPS.Tipo.choices,
                             widget=forms.Select(attrs={"class": "form-select"}))


class AfiliacionForm(forms.Form):
    """CU-04.2: matrícula y fecha de afiliación."""

    matricula = forms.CharField(label="Matrícula CPS", max_length=20,
                                widget=forms.TextInput(attrs={"class": "form-control"}))
    fecha_afil = campo_fecha("Fecha de afiliación")


class BajaForm(forms.Form):
    """CU-04.4: fecha de presentación del aviso de baja."""

    fecha_desafil = campo_fecha("Fecha del aviso de baja")


class CorreccionForm(forms.Form):
    """RF-09: actualizar (cambio real) o corregir (error de registro), siempre con motivo."""

    operacion = forms.ChoiceField(
        label="Tipo de cambio",
        choices=[(Bitacora.Operacion.ACTUALIZACION, "Actualización (cambio real)"),
                 (Bitacora.Operacion.CORRECCION, "Corrección (error de registro)")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    motivo = forms.CharField(label="Motivo", max_length=200, widget=forms.TextInput(attrs={"class": "form-control"}))
    matricula = forms.CharField(label="Matrícula CPS", max_length=20, required=False,
                                widget=forms.TextInput(attrs={"class": "form-control"}))
    fecha_afil = campo_fecha("Fecha de afiliación", required=False)
    fecha_desafil = campo_fecha("Fecha del aviso de baja", required=False)
    tipo = forms.ChoiceField(label="Tipo de afiliación", required=False,
                             choices=[("", "Sin cambio"), *AfiliacionCPS.Tipo.choices],
                             widget=forms.Select(attrs={"class": "form-select"}))
