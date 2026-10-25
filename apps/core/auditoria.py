"""Bitácora de auditoría (RNF-09, RF-31).

``registrar()`` guarda en BITACORA el usuario, la IP, la operación, la tabla, el motivo y los
valores anterior y nuevo. ``AuditoriaMiddleware`` deja el usuario y la IP de la petición en un
contexto para que los servicios no tengan que pasarlos.
"""

import json
from contextvars import ContextVar

from django.utils import timezone

IP_SISTEMA = "127.0.0.1"  # Tareas programadas y comandos, sin petición HTTP.

_contexto = ContextVar("auditoria", default=(None, None))


def contexto_actual():
    """(usuario, ip) de la petición en curso, o (None, None)."""
    return _contexto.get()


def ip_de(request):
    reenviada = request.META.get("HTTP_X_FORWARDED_FOR")
    if reenviada:
        return reenviada.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or IP_SISTEMA


class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = getattr(request, "user", None)
        if usuario is not None and not usuario.is_authenticated:
            usuario = None
        token = _contexto.set((usuario, ip_de(request)))
        try:
            return self.get_response(request)
        finally:
            _contexto.reset(token)


def _texto(valor):
    if valor is None or isinstance(valor, str):
        return valor
    return json.dumps(valor, ensure_ascii=False, default=str)


def registrar(
    operacion,
    tabla=None,
    valor_ant=None,
    valor_nuevo=None,
    motivo=None,
    usuario=None,
    ip=None,
    login_intento=None,
):
    """Registra una operación en BITACORA.

    ACTUALIZACION y CORRECCION exigen ``motivo`` (AGENTS.md §5). ``valor_ant`` y ``valor_nuevo``
    aceptan texto o cualquier valor serializable a JSON (por ejemplo, un diccionario de columnas).
    """
    from apps.administracion.models import Bitacora

    if operacion not in Bitacora.Operacion.values:
        raise ValueError(f"Operación de bitácora no válida: {operacion}")
    motivo = (motivo or "").strip() or None
    if operacion in Bitacora.OPERACIONES_CON_MOTIVO and motivo is None:
        raise ValueError(f"La operación {operacion} exige indicar el motivo.")

    usuario_ctx, ip_ctx = contexto_actual()
    return Bitacora.objects.create(
        usuario=usuario or usuario_ctx,
        login_intento=login_intento,
        fecha_hora=timezone.now(),
        operacion=operacion,
        tabla=tabla,
        valor_ant=_texto(valor_ant),
        valor_nuevo=_texto(valor_nuevo),
        motivo=motivo,
        ip=ip or ip_ctx or IP_SISTEMA,
    )
