"""Formularios del módulo Planillas de sueldos (CU-05 a CU-07)."""

import datetime

from django import forms

MONTO = {"min_value": 0, "max_digits": 10, "decimal_places": 2}


class ArchivoMarcacionesForm(forms.Form):
    """CU-05.1 Importar días trabajados."""

    archivo = forms.FileField(label="Archivo de marcaciones (Excel o CSV)")
    motivo = forms.CharField(label="Motivo de la reimportación", max_length=200, required=False,
                             help_text="Obligatorio si ya se importaron marcaciones de este mes.")


class OtrosIngresosForm(forms.Form):
    """CU-05.2 Otros ingresos por trabajador (borrador hasta el cierre)."""

    contrato = forms.IntegerField(widget=forms.HiddenInput)
    monto = forms.DecimalField(label="Otros ingresos", **MONTO)


class BuscarCIForm(forms.Form):
    """CU-01.1 Buscar empleado por CI."""

    ci = forms.CharField(label="CI del empleado", max_length=15)


class AnticipoForm(BuscarCIForm):
    """CU-06 Registrar anticipo."""

    fecha = forms.DateField(label="Fecha", initial=datetime.date.today, widget=forms.DateInput(attrs={"type": "date"}))
    monto = forms.DecimalField(label="Monto (Bs)", **{**MONTO, "min_value": 0.01})


class F110Form(BuscarCIForm):
    """CU-07 Registrar formulario F110."""

    anio = forms.IntegerField(label="Gestión declarada", min_value=2000, max_value=2100)
    mes = forms.IntegerField(label="Mes declarado", min_value=1, max_value=12)
    monto = forms.DecimalField(label="Monto de las facturas (Bs)", **MONTO)
    fecha_pres = forms.DateField(label="Fecha de presentación", initial=datetime.date.today,
                                 widget=forms.DateInput(attrs={"type": "date"}))
