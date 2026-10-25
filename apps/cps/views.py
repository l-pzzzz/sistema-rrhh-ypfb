"""Vistas del módulo Seguro de salud CPS (CU-04).

CU-04 Gestionar afiliación / desafiliación CPS (RF-06, RF-07, RF-08, RF-09). Solo el Afiliador (operador).
"""

from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.administracion.models import Rol
from apps.core.permisos import requiere_nivel
from apps.kardex.models import ContratoCargo, Empleado

from . import services
from .forms import AfiliacionForm, BajaForm, CorreccionForm, FiltroBandejaForm, TipoAvisoForm
from .models import AfiliacionCPS

solo_afiliador = requiere_nivel(Rol.Nivel.OPERADOR, rol=Rol.AFILIADOR)
COLORES = {"verde": "success", "amarillo": "warning", "rojo": "danger"}


def _filtrar(filtro):
    """Consulta de la bandeja según la pestaña, la búsqueda (CU-01.1) y los filtros de RF-07."""
    datos = filtro.cleaned_data
    pestana = datos.get("pestana") or "altas"
    consulta = {
        "altas": services.altas_pendientes,
        "bajas": services.bajas_pendientes,
        "todas": AfiliacionCPS.objects.all,
    }[pestana]()
    consulta = consulta.select_related("contrato__empleado", "contrato__categoria")
    for termino in (datos.get("q") or "").split():
        consulta = consulta.filter(
            Q(contrato__empleado__ci__icontains=termino)
            | Q(contrato__empleado__codigo__icontains=termino)
            | Q(contrato__empleado__nombres__icontains=termino)
            | Q(contrato__empleado__apellidos__icontains=termino)
        )
    if datos.get("estado"):
        consulta = consulta.filter(estado=datos["estado"])
    campo = "fecha_lim_baja" if pestana == "bajas" else "fecha_limite"
    if datos.get("desde"):
        consulta = consulta.filter(**{f"{campo}__gte": datos["desde"]})
    if datos.get("hasta"):
        consulta = consulta.filter(**{f"{campo}__lte": datos["hasta"]})
    if datos.get("departamento"):
        consulta = consulta.filter(contrato__cargos__ubicacion=datos["departamento"]).distinct()
    return pestana, consulta.order_by("fecha_limite", "nro")


def _filas(consulta, semaforo):
    """Filas de la bandeja con su semáforo (de la caché de la tarea diaria o calculado al momento)."""
    guardado, hoy, filas = services.semaforos_en_cache(), timezone.localdate(), []
    for afil in consulta:
        clave = services.clave_semaforo(afil)
        color = restantes = alerta = None
        if clave:
            color, restantes = guardado.get(clave) or services.semaforo_de(afil, hoy)
            if clave.startswith("B"):
                alerta = services.mensaje_baja(restantes)
        if semaforo and color != semaforo:
            continue
        filas.append({
            "afil": afil, "empleado": afil.contrato.empleado, "color": color, "bootstrap": COLORES.get(color),
            "restantes": restantes, "alerta": alerta,
            "limite": afil.fecha_lim_baja if clave and clave.startswith("B") else afil.fecha_limite,
        })
    return filas


@solo_afiliador
def inicio(request):
    """CU-04.1 Consultar bandeja de control (semáforo); HTMX actualiza solo la tabla."""
    filtro = FiltroBandejaForm(request.GET)
    if not filtro.is_valid():  # filtros inválidos: se vuelve a la bandeja sin filtros
        filtro = FiltroBandejaForm({})
        filtro.is_valid()
    pestana, consulta = _filtrar(filtro)
    filas = _filas(consulta, filtro.cleaned_data.get("semaforo"))
    contexto = {"filtro": filtro, "pestana": pestana, "filas": filas,
                "alertas": [fila for fila in filas if fila["alerta"]]}
    plantilla = "cps/_tabla.html" if request.headers.get("HX-Request") else "cps/bandeja.html"
    return render(request, plantilla, contexto)


def _afiliacion(nro):
    return get_object_or_404(AfiliacionCPS.objects.select_related("contrato__empleado", "contrato__categoria"), nro=nro)


@solo_afiliador
def detalle(request, nro):
    """CU-04 paso 2: datos del trabajador, del contrato y la fecha límite en días hábiles."""
    afil = _afiliacion(nro)
    clave = services.clave_semaforo(afil)
    color, restantes = services.semaforo_de(afil) if clave else (None, None)
    return render(request, "cps/detalle.html", {
        "afil": afil, "empleado": afil.contrato.empleado, "contrato": afil.contrato,
        "cargos": [f.cargo for f in ContratoCargo.objects.filter(contrato=afil.contrato).select_related("cargo")],
        "color": color, "bootstrap": COLORES.get(color), "restantes": restantes,
        "alerta": services.mensaje_baja(restantes) if clave and clave.startswith("B") else None,
        "puede_afiliar": clave is not None and clave.startswith("A"),
        "puede_baja": clave is not None and clave.startswith("B"),
        "puede_corregir": afil.estado != AfiliacionCPS.Estado.PENDIENTE,
    })


def _formulario(request, afil, formulario, titulo, accion):
    """Plantilla común de los formularios de CU-04: ejecuta ``accion(datos)`` y vuelve al detalle."""
    if request.method == "POST" and formulario.is_valid():
        try:
            accion(formulario.cleaned_data)
        except services.AfiliacionRechazada as error:
            formulario.add_error(None, str(error))
        else:
            messages.success(request, f"{titulo}: registrado.")
            return redirect("cps:detalle", nro=afil.nro)
    return render(request, "cps/formulario.html", {"afil": afil, "form": formulario, "titulo": titulo})


@solo_afiliador
def aviso(request, nro):
    """CU-04.3 Generar aviso de afiliación (RF-06): descarga el parte de ingreso en PDF."""
    afil = _afiliacion(nro)
    formulario = TipoAvisoForm(request.POST or None, initial={"tipo": afil.tipo})
    if request.method == "POST" and formulario.is_valid():
        try:
            pdf = services.generar_aviso(afil, formulario.cleaned_data["tipo"])
        except services.AfiliacionRechazada as error:
            formulario.add_error(None, str(error))
        else:
            respuesta = HttpResponse(pdf, content_type="application/pdf")
            respuesta["Content-Disposition"] = f'attachment; filename="aviso-afiliacion-{afil.nro}.pdf"'
            return respuesta
    return render(request, "cps/formulario.html", {"afil": afil, "form": formulario,
                                                   "titulo": "Generar aviso de afiliación"})


@solo_afiliador
def afiliar(request, nro):
    """CU-04.2 Registrar afiliación y matrícula (RF-06, RF-07)."""
    afil = _afiliacion(nro)
    formulario = AfiliacionForm(request.POST or None)
    return _formulario(request, afil, formulario, "Registrar afiliación y matrícula",
                       lambda d: services.registrar_afiliacion(afil, d["matricula"], d["fecha_afil"]))


@solo_afiliador
def baja(request, nro):
    """CU-04.4 Registrar aviso de baja (RF-08)."""
    afil = _afiliacion(nro)
    formulario = BajaForm(request.POST or None)
    return _formulario(request, afil, formulario, "Registrar aviso de baja",
                       lambda d: services.registrar_baja(afil, d["fecha_desafil"]))


@solo_afiliador
def corregir(request, nro):
    """RF-09 Actualizar o corregir la afiliación, con motivo y valor anterior y nuevo en la bitácora."""
    afil = _afiliacion(nro)
    formulario = CorreccionForm(request.POST or None)

    def accion(d):
        campos = {c: d[c] for c in ("matricula", "fecha_afil", "fecha_desafil", "tipo")}
        services.corregir(afil, d["operacion"], d["motivo"], **campos)

    return _formulario(request, afil, formulario, "Actualizar o corregir la afiliación", accion)


@solo_afiliador
def historial(request, ci):
    """RF-09 Historial de afiliaciones y desafiliaciones del trabajador, en orden cronológico."""
    empleado = get_object_or_404(Empleado, ci=ci)
    return render(request, "cps/historial.html", {"empleado": empleado, "movimientos": services.historial(empleado)})
