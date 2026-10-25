"""Vistas del módulo Planillas de sueldos (CU-05 a CU-07)."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.administracion.models import Rol
from apps.core.parametros import ParametroNoConfigurado
from apps.core.permisos import requiere_nivel

from . import exportacion
from .asistencia import AdaptadorArchivoAsistencia, ArchivoInvalido, ArchivoMarcacionesCSV
from .fachada import ControladorPlanilla, FachadaPlanilla
from .forms import AnticipoForm, ArchivoMarcacionesForm, F110Form, OtrosIngresosForm
from .models import Anticipo, BoletaPago, FormularioF110, Planilla
from .services import (
    AnticipoRechazado,
    ContratoNoVigente,
    F110Rechazado,
    HaberNoConfigurado,
    PlanillaCerrada,
    ServicioAnticipos,
    ServicioF110,
    avisar_administrador,
    contrato_vigente_por_ci,
)

solo_pagos = requiere_nivel(Rol.Nivel.OPERADOR, rol=Rol.ENCARGADO_DE_PAGOS)
ERRORES_PROCESO = (ParametroNoConfigurado, HaberNoConfigurado, PlanillaCerrada, ValueError)
MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
         "Noviembre", "Diciembre"]


def _bloquear(request, error):
    """CU-05, extensión 2b: faltan parámetros de la gestión; se bloquea el proceso y se avisa al Administrador."""
    texto = f"No se puede procesar la planilla: {error}"
    avisar_administrador("Planillas: faltan parámetros de la gestión", texto)
    messages.error(request, texto)
    return redirect("planillas:inicio")


def _mes(anio, mes):
    if not 1 <= mes <= 12:
        raise Http404
    return {"anio": anio, "mes": mes, "nombre_mes": MESES[mes]}


@solo_pagos
def inicio(request):
    """CU-05 paso 1: gestiones y meses disponibles."""
    controlador = ControladorPlanilla()
    gestiones = controlador.gestiones()
    try:
        anio = int(request.GET.get("anio") or (gestiones[0] if gestiones else timezone.localdate().year))
    except ValueError:
        raise Http404 from None
    meses = [{"numero": m, "nombre": MESES[m], "planilla": p} for m, p in controlador.meses(anio)]
    return render(request, "planillas/inicio.html", {"gestiones": gestiones, "anio": anio, "meses": meses})


@solo_pagos
def procesar(request, anio, mes):
    """CU-05.1 y CU-05.3: importar días trabajados y listar inconsistencias (RF-10)."""
    contexto = _mes(anio, mes)
    if Planilla.objects.filter(gestion_id=anio, mes=mes, estado=Planilla.Estado.CERRADA).exists():
        messages.info(request, "La planilla ya está cerrada: solo se permite consultarla.")
        return redirect("planillas:detalle", anio=anio, mes=mes)
    form = ArchivoMarcacionesForm(request.POST or None, request.FILES or None)
    resultado = None
    if request.method == "POST" and form.is_valid():
        try:
            fuente = AdaptadorArchivoAsistencia(ArchivoMarcacionesCSV(form.cleaned_data["archivo"]))
            resultado = FachadaPlanilla().importar_asistencia(
                fuente, anio, mes, motivo=form.cleaned_data["motivo"], usuario=request.user)
            messages.success(request, f"Se importaron {resultado.importados} registros.")
        except (ArchivoInvalido, PlanillaCerrada, ValueError) as error:
            messages.error(request, str(error))
    return render(request, "planillas/procesar.html", {**contexto, "form": form, "resultado": resultado})


@solo_pagos
def preplanilla(request, anio, mes):
    """CU-05.2 y CU-05.4: revisar la preplanilla, ingresar otros ingresos y aprobar y cerrar."""
    contexto = _mes(anio, mes)
    fachada = FachadaPlanilla()
    if request.method == "POST":
        try:
            if request.POST.get("accion") == "aprobar":
                fachada.aprobar_y_cerrar(fachada.generar_preplanilla(anio, mes).planilla, request.user)
                messages.success(request, "Planilla aprobada y cerrada; las boletas fueron generadas.")
                return redirect("planillas:detalle", anio=anio, mes=mes)
            form = OtrosIngresosForm(request.POST)
            if form.is_valid():
                planilla = fachada.generar_preplanilla(anio, mes).planilla
                fachada.registrar_otros_ingresos(planilla, form.cleaned_data["contrato"], form.cleaned_data["monto"])
                messages.success(request, "Otros ingresos guardados en el borrador de la planilla.")
            else:
                messages.error(request, "El monto de otros ingresos no es válido.")
        except (ParametroNoConfigurado, HaberNoConfigurado) as error:
            return _bloquear(request, error)
        except ERRORES_PROCESO as error:
            messages.error(request, str(error))
        return redirect("planillas:preplanilla", anio=anio, mes=mes)
    try:
        datos = fachada.generar_preplanilla(anio, mes)
    except PlanillaCerrada:
        return redirect("planillas:detalle", anio=anio, mes=mes)
    except (ParametroNoConfigurado, HaberNoConfigurado) as error:
        return _bloquear(request, error)
    return render(request, "planillas/preplanilla.html", {**contexto, "datos": datos})


@solo_pagos
def detalle(request, anio, mes):
    """CU-05: planilla cerrada con sus boletas (solo consulta)."""
    planilla = get_object_or_404(Planilla, gestion_id=anio, mes=mes)
    boletas = planilla.boletas.select_related("contrato__empleado").order_by("nro")
    return render(request, "planillas/detalle.html", {**_mes(anio, mes), "planilla": planilla, "boletas": boletas})


@solo_pagos
def boleta(request, nro):
    """CU-05.5: boleta de pago con el detalle de conceptos."""
    obj = get_object_or_404(BoletaPago.objects.select_related("planilla", "contrato__empleado"), nro=nro)
    return render(request, "planillas/boleta.html", {"boleta": obj, "detalles": exportacion.conceptos_boleta(obj)})


def _descarga(contenido, formato, nombre):
    respuesta = HttpResponse(contenido, content_type=exportacion.CONTENIDO[formato])
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre}.{formato}"'
    return respuesta


def _formato(formato):
    if formato not in exportacion.CONTENIDO:
        raise Http404
    return formato


@solo_pagos
def exportar_planilla(request, anio, mes, formato):
    """CU-05 paso 7: planilla consolidada en PDF o Excel (RF-16)."""
    planilla = get_object_or_404(Planilla, gestion_id=anio, mes=mes, estado=Planilla.Estado.CERRADA)
    formato = _formato(formato)
    genera = exportacion.planilla_pdf if formato == "pdf" else exportacion.planilla_excel
    return _descarga(genera(planilla), formato, f"planilla-{anio}-{mes:02d}")


@solo_pagos
def exportar_boleta(request, nro, formato):
    """CU-05.5: boleta en PDF o Excel (RF-16)."""
    obj = get_object_or_404(BoletaPago.objects.select_related("planilla", "contrato__empleado"), nro=nro)
    formato = _formato(formato)
    genera = exportacion.boleta_pdf if formato == "pdf" else exportacion.boleta_excel
    return _descarga(genera(obj), formato, f"boleta-{nro}")


@solo_pagos
def anticipos(request):
    """CU-06 Registrar anticipo (RF-15)."""
    form = AnticipoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        datos = form.cleaned_data
        try:
            contrato = contrato_vigente_por_ci(datos["ci"])
            ServicioAnticipos().registrar(contrato, datos["fecha"], datos["monto"], usuario=request.user)
        except (ContratoNoVigente, AnticipoRechazado, ParametroNoConfigurado, HaberNoConfigurado) as error:
            form.add_error(None, ValidationError(str(error)))
        else:
            messages.success(request, "Anticipo registrado.")
            return redirect("planillas:anticipos")
    recientes = Anticipo.objects.select_related("contrato__empleado").order_by("-nro")[:20]
    return render(request, "planillas/anticipos.html", {"form": form, "recientes": recientes})


@solo_pagos
def f110(request):
    """CU-07 Registrar formulario F110 (RF-13, RF-14)."""
    form = F110Form(request.POST or None)
    if request.method == "POST" and form.is_valid():
        datos = form.cleaned_data
        try:
            contrato = contrato_vigente_por_ci(datos["ci"])
            ServicioF110().registrar(contrato, datos["anio"], datos["mes"], datos["monto"], datos["fecha_pres"],
                                     usuario=request.user)
        except (ContratoNoVigente, F110Rechazado, ParametroNoConfigurado) as error:
            form.add_error(None, ValidationError(str(error)))
        else:
            messages.success(request, "Formulario F110 registrado.")
            return redirect("planillas:f110")
    recientes = [(f, ServicioF110.mes_de_aplicacion(f)) for f in
                 FormularioF110.objects.select_related("contrato__empleado").order_by("-nro")[:20]]
    return render(request, "planillas/f110.html", {"form": form, "recientes": recientes})
