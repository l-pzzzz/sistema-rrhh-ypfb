"""Vistas del módulo Kardex y contratos (CU-01 a CU-03).

Escriben solo los operadores con rol Afiliador; el Encargado de Pagos, el Responsable de
Vacaciones y Lactancias y el nivel Consulta solo consultan (AGENTS.md §7, RNF-07).
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.administracion.models import Rol
from apps.core.permisos import requiere_nivel

from . import forms
from .models import Contrato, Dependiente, Documento, Empleado
from .services import (
    ServicioContrato,
    ServicioDependiente,
    ServicioDocumento,
    ServicioEmpleado,
    alertas_categoria,
    aviso_afiliacion,
    buscar_empleados,
)

ROLES_LECTURA = (Rol.AFILIADOR, Rol.ENCARGADO_DE_PAGOS, Rol.RESPONSABLE_VACACIONES, Rol.CONSULTA)

lectura = requiere_nivel((Rol.Nivel.OPERADOR, Rol.Nivel.CONSULTA), rol=ROLES_LECTURA)
escritura = requiere_nivel(Rol.Nivel.OPERADOR, rol=Rol.AFILIADOR)

POR_PAGINA = 25


def puede_escribir(usuario):
    return usuario.rol.nivel == Rol.Nivel.OPERADOR and usuario.rol.nombre == Rol.AFILIADOR


def _agregar_errores(form, error):
    """Muestra en el formulario los errores de un servicio (en su campo, si el formulario lo tiene)."""
    if hasattr(error, "error_dict"):
        for campo, errores in error.error_dict.items():
            form.add_error(campo if campo in form.fields else None, errores)
    else:
        form.add_error(None, error.messages)


def _avisos(request, avisos):
    for aviso in avisos:
        messages.warning(request, aviso)


def _formulario(request, form, titulo, empleado=None, **extra):
    contexto = {"form": form, "titulo": titulo, "empleado": empleado, **extra}
    return render(request, "kardex/formulario.html", contexto)


# ---------------------------------------------------------------- CU-01


@lectura
def inicio(request):
    """CU-01.1 Buscar empleado por CI, código o nombre (RF-29) y alertas de categoría (RF-03)."""
    form = forms.BusquedaForm(request.GET or None)
    filtros = form.cleaned_data if form.is_valid() else {}
    empleados = buscar_empleados(
        filtros.get("q", ""), filtros.get("departamento"), filtros.get("categoria"), filtros.get("estado")
    )
    pagina = Paginator(empleados, POR_PAGINA).get_page(request.GET.get("pagina"))
    contexto = {"form": form, "pagina": pagina, "consulta": request.GET.urlencode()}
    if request.headers.get("HX-Request"):
        return render(request, "kardex/_resultados.html", contexto)
    escribe = puede_escribir(request.user)
    contexto |= {"puede_escribir": escribe, "alertas": alertas_categoria() if escribe else []}
    return render(request, "kardex/inicio.html", contexto)


@lectura
def ficha(request, ci):
    """CU-01 Ficha del empleado: datos, contratos, dependientes (RF-05, regla 5) y documentos (RF-04)."""
    empleado = get_object_or_404(Empleado, pk=ci)
    contratos = empleado.contratos.prefetch_related("cargos__ubicacion").order_by("-fecha_inicio")
    vigente = next((c for c in contratos if c.estado == Contrato.Estado.VIGENTE), None)
    dependientes = empleado.dependientes.order_by("apellidos", "nombres")
    documentos = Documento.objects.filter(
        persona_id__in=[empleado.ci, *(d.ci for d in dependientes)]
    ).select_related("tipo", "persona").order_by("persona_id", "tipo__descripcion", "-fecha_carga")
    servicio = ServicioDependiente()
    hoy = timezone.localdate()
    avisos_dependientes = {d.ci: servicio.avisos(d, hoy) for d in dependientes}
    contexto = {
        "empleado": empleado,
        "contratos": contratos,
        "vigente": vigente,
        "dependientes": [(d, avisos_dependientes[d.ci]) for d in dependientes],
        "documentos": documentos,
        "aviso_cps": aviso_afiliacion(empleado),
        "puede_escribir": puede_escribir(request.user),
    }
    return render(request, "kardex/ficha.html", contexto)


@escritura
def empleado_nuevo(request):
    """CU-01.2 Registrar datos del empleado (RF-01)."""
    form = forms.EmpleadoForm(request.POST or None, initial={"ci": request.GET.get("ci", "")})
    if request.method == "POST" and form.is_valid():
        try:
            empleado = ServicioEmpleado().registrar(form.cleaned_data)
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(request, "Empleado registrado.")
            return redirect("kardex:ficha", ci=empleado.ci)
    return _formulario(request, form, "Nuevo empleado")


@escritura
def empleado_editar(request, ci):
    """CU-01.3 Actualizar o corregir datos del empleado (RF-01, regla 4)."""
    empleado = get_object_or_404(Empleado, pk=ci)
    form = forms.EmpleadoEdicionForm(request.POST or None, initial=_valores(empleado, forms.EmpleadoEdicionForm))
    if request.method == "POST" and form.is_valid():
        datos = dict(form.cleaned_data)
        operacion, motivo = datos.pop("operacion"), datos.pop("motivo")
        try:
            ServicioEmpleado().modificar(empleado, datos, operacion, motivo)
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(request, "Datos del empleado guardados.")
            return redirect("kardex:ficha", ci=empleado.ci)
    return _formulario(request, form, "Actualizar o corregir datos del empleado", empleado)


def _valores(objeto, clase_form):
    return {campo: getattr(objeto, campo) for campo in clase_form.campos_modelo[1]}


def _persona(ci):
    """Empleado o dependiente dueño de un documento."""
    return Empleado.objects.filter(pk=ci).first() or get_object_or_404(Dependiente, pk=ci)


def _empleado_de(persona):
    return persona if isinstance(persona, Empleado) else persona.empleado


@escritura
def documento_adjuntar(request, ci):
    """CU-01.4 Adjuntar documento del empleado o de un dependiente (RF-04)."""
    persona = _persona(ci)
    form = forms.DocumentoForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        datos = form.cleaned_data
        try:
            ServicioDocumento().adjuntar(persona, datos["tipo"], datos["archivo"], datos["fecha_emision"])
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(request, "Documento adjuntado.")
            return redirect("kardex:ficha", ci=_empleado_de(persona).ci)
    return _formulario(request, form, f"Adjuntar documento de {persona.nombres} {persona.apellidos}",
                       _empleado_de(persona), multipart=True)


@escritura
def documento_reemplazar(request, nro):
    """CU-01.4 Reemplazar documento; la versión anterior queda en el historial (RF-04, regla 3)."""
    documento = get_object_or_404(Documento.objects.select_related("tipo"), pk=nro)
    persona = _persona(documento.persona_id)
    form = forms.ReemplazoForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        datos = form.cleaned_data
        try:
            ServicioDocumento().reemplazar(documento, datos["archivo"], datos["motivo"], datos["fecha_emision"])
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(request, "Documento reemplazado.")
            return redirect("kardex:ficha", ci=_empleado_de(persona).ci)
    return _formulario(request, form, f"Reemplazar {documento.tipo} de {persona.nombres} {persona.apellidos}",
                       _empleado_de(persona), multipart=True)


@lectura
def documento_ver(request, nro):
    """CU-01 Consultar documento (RF-04). Los archivos solo se sirven a usuarios con acceso al Kardex."""
    documento = get_object_or_404(Documento, pk=nro)
    return FileResponse(documento.archivo.open("rb"), filename=documento.archivo.name.rsplit("/", 1)[-1])


# ---------------------------------------------------------------- CU-02


@escritura
def contrato_nuevo(request, ci):
    """CU-02.1 Registrar contrato con cargos y CU-02.2 categoría por antigüedad (RF-02, RF-03)."""
    empleado = get_object_or_404(Empleado, pk=ci)
    servicio = ServicioContrato()
    if empleado.contratos.filter(estado=Contrato.Estado.VIGENTE).exists():
        # Extensión 2a: ofrece actualizar el contrato vigente o registrar el retiro.
        messages.error(request, "Rechazado: un empleado no puede tener dos contratos vigentes.")
        return redirect("kardex:ficha", ci=empleado.ci)
    hoy = timezone.localdate()
    categoria = servicio.categoria_por_antiguedad(empleado.fecha_ingreso, hoy)
    form = forms.ContratoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        datos = form.cleaned_data
        try:
            contrato = servicio.registrar(empleado, datos["fecha_inicio"], datos["fecha_fin"], datos["cargos"], hoy)
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(request, f"Contrato {contrato.nro} registrado con la categoría {contrato.categoria_id}.")
            return redirect("kardex:ficha", ci=empleado.ci)
    return _formulario(
        request, form, "Nuevo contrato", empleado,
        categoria=categoria, haber_basico=servicio.haber_basico(categoria, hoy.year), gestion=hoy.year,
    )


def _contrato_vigente(nro):
    return get_object_or_404(Contrato.objects.select_related("empleado"), pk=nro, estado=Contrato.Estado.VIGENTE)


@escritura
def contrato_editar(request, nro):
    """CU-02.3 Actualizar o corregir contrato (RF-02, regla 4)."""
    contrato = _contrato_vigente(nro)
    inicial = {"fecha_inicio": contrato.fecha_inicio, "fecha_fin": contrato.fecha_fin, "cargos": contrato.cargos.all()}
    form = forms.ContratoEdicionForm(request.POST or None, initial=inicial)
    if request.method == "POST" and form.is_valid():
        datos = form.cleaned_data
        try:
            ServicioContrato().modificar(
                contrato, {"fecha_inicio": datos["fecha_inicio"], "fecha_fin": datos["fecha_fin"]},
                datos["cargos"], datos["operacion"], datos["motivo"],
            )
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(request, "Contrato guardado.")
            return redirect("kardex:ficha", ci=contrato.empleado_id)
    return _formulario(request, form, f"Actualizar o corregir el contrato {contrato.nro}", contrato.empleado)


@escritura
def contrato_retiro(request, nro):
    """CU-02.4 Registrar retiro del empleado (RF-28)."""
    contrato = _contrato_vigente(nro)
    form = forms.RetiroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        datos = form.cleaned_data
        try:
            ServicioContrato().registrar_retiro(
                contrato, datos["fecha_retiro"], datos["tipo_retiro"], datos["motivo_retiro"]
            )
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(request, "Retiro registrado: el contrato quedó CONCLUIDO y el empleado RETIRADO.")
            return redirect("kardex:ficha", ci=contrato.empleado_id)
    return _formulario(request, form, f"Registrar retiro del contrato {contrato.nro}", contrato.empleado,
                       confirmar="El contrato quedará CONCLUIDO y el empleado RETIRADO. ¿Desea continuar?")


# ---------------------------------------------------------------- CU-03


@escritura
def dependiente_nuevo(request, ci):
    """CU-03.1 Registrar dependiente con la fotocopia del CI (CU-03.2; RF-05)."""
    empleado = get_object_or_404(Empleado, pk=ci)
    form = forms.DependienteForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        datos = dict(form.cleaned_data)
        parentesco, fotocopia = datos.pop("parentesco"), datos.pop("fotocopia_ci")
        try:
            _, avisos = ServicioDependiente().registrar(empleado, datos, parentesco, fotocopia)
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(request, "Dependiente registrado.")
            _avisos(request, avisos)
            return redirect("kardex:ficha", ci=empleado.ci)
    return _formulario(request, form, "Nuevo dependiente", empleado, multipart=True,
                       avisos=aviso_afiliacion(empleado))


@escritura
def dependiente_editar(request, ci):
    """CU-03.3 Actualizar o corregir dependiente (RF-05)."""
    dependiente = get_object_or_404(Dependiente.objects.select_related("empleado"), pk=ci)
    form = forms.DependienteEdicionForm(
        request.POST or None, initial=_valores(dependiente, forms.DependienteEdicionForm)
    )
    if request.method == "POST" and form.is_valid():
        datos = dict(form.cleaned_data)
        operacion, motivo = datos.pop("operacion"), datos.pop("motivo")
        try:
            avisos = ServicioDependiente().modificar(dependiente, datos, operacion, motivo)
        except ValidationError as error:
            _agregar_errores(form, error)
        else:
            messages.success(request, "Dependiente guardado.")
            _avisos(request, avisos)
            return redirect("kardex:ficha", ci=dependiente.empleado_id)
    return _formulario(request, form, "Actualizar o corregir dependiente", dependiente.empleado)
