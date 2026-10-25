"""Formularios del módulo Kardex y contratos (CU-01 a CU-03).

Solo validan el formato de cada campo (RNF-02); las reglas de negocio están en services.py.
"""

from django import forms
from django.forms.models import fields_for_model

from apps.administracion.models import Bitacora

from .models import Cargo, Categoria, Contrato, Dependiente, Empleado, TipoDocumento, Ubicacion
from .services import CAMPOS_EMPLEADO, CAMPOS_PERSONA


def fecha():
    return forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")


ETIQUETAS = {
    "ci": "CI",
    "fecha_nac": "Fecha de nacimiento",
    "telefono": "Teléfono",
    "codigo": "Código",
    "fecha_ingreso": "Fecha de ingreso",
    "direccion": "Dirección",
    "nom_emerg": "Contacto de emergencia",
    "par_emerg": "Parentesco del contacto",
    "tel_emerg": "Teléfono del contacto",
}


class FormularioBootstrap(forms.Form):
    """Agrega los campos del modelo indicados en ``campos_modelo`` y las clases de Bootstrap 5."""

    campos_modelo = None  # (modelo, [campos])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.campos_modelo:
            modelo, nombres = self.campos_modelo
            widgets = {n: fecha() for n in nombres if n.startswith("fecha")}
            campos = fields_for_model(modelo, fields=nombres, widgets=widgets, labels=ETIQUETAS)
            # Los campos del modelo van antes que los declarados en el formulario.
            self.fields = {**campos, **self.fields}
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, forms.CheckboxSelectMultiple | forms.CheckboxInput):
                continue
            clase = "form-select" if isinstance(widget, forms.Select) else "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {clase}".strip()


class MotivoForm(FormularioBootstrap):
    """CU-01.3, CU-02.3 y CU-03.3: actualizar (cambio real) o corregir (error de registro), con motivo."""

    operacion = forms.ChoiceField(
        label="Tipo de cambio",
        choices=[
            (Bitacora.Operacion.ACTUALIZACION, "Actualización (cambio real)"),
            (Bitacora.Operacion.CORRECCION, "Corrección (error de registro)"),
        ],
    )
    motivo = forms.CharField(max_length=200, widget=forms.Textarea(attrs={"rows": 2}))


class BusquedaForm(FormularioBootstrap):
    """CU-01.1 Buscar empleado (RF-29)."""

    q = forms.CharField(label="CI, código o nombre", required=False, max_length=80)
    departamento = forms.ModelChoiceField(
        Ubicacion.objects.order_by("departamento"), required=False, empty_label="Todos los departamentos"
    )
    categoria = forms.ModelChoiceField(
        Categoria.objects.order_by("cod"), required=False, empty_label="Todas las categorías"
    )
    estado = forms.ChoiceField(choices=[("", "Todos los estados"), *Empleado.Estado.choices], required=False)


class EmpleadoForm(FormularioBootstrap):
    """CU-01.2 Registrar datos del empleado (RF-01)."""

    campos_modelo = (Empleado, ["ci", *CAMPOS_PERSONA, *CAMPOS_EMPLEADO])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ci"].help_text = "Con complemento opcional, por ejemplo 1234567-1A."


class EmpleadoEdicionForm(MotivoForm):
    """CU-01.3 Actualizar o corregir datos del empleado (RF-01). El CI no se modifica."""

    campos_modelo = (Empleado, [*CAMPOS_PERSONA, *CAMPOS_EMPLEADO])


class CargosField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, cargo):
        return f"{cargo.nombre} — {cargo.ubicacion.departamento}"


class ContratoForm(FormularioBootstrap):
    """CU-02.1 Registrar contrato con sus cargos y ubicación (RF-02)."""

    fecha_inicio = forms.DateField(label="Fecha de inicio", widget=fecha())
    fecha_fin = forms.DateField(label="Fecha de fin", required=False, widget=fecha(),
                                help_text="Vacía si el contrato es indefinido.")
    cargos = CargosField(
        Cargo.objects.select_related("ubicacion").order_by("ubicacion__departamento", "nombre"),
        label="Cargo o cargos",
        widget=forms.CheckboxSelectMultiple,
    )


class ContratoEdicionForm(ContratoForm, MotivoForm):
    """CU-02.3 Actualizar o corregir contrato (RF-02, regla 4)."""


class RetiroForm(FormularioBootstrap):
    """CU-02.4 Registrar retiro del empleado (RF-28)."""

    fecha_retiro = forms.DateField(label="Fecha de retiro", widget=fecha())
    tipo_retiro = forms.ChoiceField(label="Tipo de retiro", choices=Contrato.TipoRetiro.choices)
    motivo_retiro = forms.CharField(label="Motivo", max_length=200, widget=forms.Textarea(attrs={"rows": 2}))


class DocumentoForm(FormularioBootstrap):
    """CU-01.4 Adjuntar documento (RF-04)."""

    tipo = forms.ModelChoiceField(TipoDocumento.objects.order_by("descripcion"), label="Tipo de documento")
    fecha_emision = forms.DateField(label="Fecha de emisión", required=False, widget=fecha())
    archivo = forms.FileField(help_text="PDF, JPG o PNG de hasta 5 MB.",
                              widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png"}))


class ReemplazoForm(FormularioBootstrap):
    """CU-01.4 Reemplazar documento: la versión anterior queda en el historial (RF-04, regla 3)."""

    fecha_emision = forms.DateField(label="Fecha de emisión", required=False, widget=fecha())
    archivo = forms.FileField(help_text="PDF, JPG o PNG de hasta 5 MB.",
                              widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png"}))
    motivo = forms.CharField(max_length=200, widget=forms.Textarea(attrs={"rows": 2}))


class DependienteForm(FormularioBootstrap):
    """CU-03.1 Registrar dependiente con la fotocopia del CI (CU-03.2; RF-05)."""

    campos_modelo = (Dependiente, ["ci", *CAMPOS_PERSONA, "parentesco"])
    fotocopia_ci = forms.FileField(
        label="Fotocopia del CI",
        help_text="Obligatoria. PDF, JPG o PNG de hasta 5 MB.",
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png"}),
    )


class DependienteEdicionForm(MotivoForm):
    """CU-03.3 Actualizar o corregir dependiente (RF-05)."""

    campos_modelo = (Dependiente, [*CAMPOS_PERSONA, "parentesco"])
