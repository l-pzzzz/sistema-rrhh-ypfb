"""Bitácora de auditoría inalterable (RNF-09, RF-31)."""

import pytest
from django.test import RequestFactory

from apps.administracion.models import Bitacora
from apps.core import auditoria

from .fabricas import UsuarioFactory

pytestmark = pytest.mark.django_db


def test_registra_alta_con_usuario_e_ip():
    usuario = UsuarioFactory()
    b = auditoria.registrar(Bitacora.Operacion.ALTA, tabla="CONTRATO", valor_nuevo={"Nro": 1},
                            usuario=usuario, ip="10.0.0.5")
    b.refresh_from_db()
    assert b.usuario == usuario
    assert b.ip == "10.0.0.5"
    assert b.tabla == "CONTRATO"
    assert b.valor_nuevo == '{"Nro": 1}'
    assert b.fecha_hora is not None


@pytest.mark.parametrize("operacion", [Bitacora.Operacion.ACTUALIZACION, Bitacora.Operacion.CORRECCION])
def test_actualizacion_y_correccion_exigen_motivo(operacion):
    with pytest.raises(ValueError, match="motivo"):
        auditoria.registrar(operacion, tabla="EMPLEADO", valor_ant={"Apellidos": "Peres"},
                            valor_nuevo={"Apellidos": "Pérez"}, ip="10.0.0.5")
    with pytest.raises(ValueError, match="motivo"):
        auditoria.registrar(operacion, tabla="EMPLEADO", motivo="   ", ip="10.0.0.5")
    b = auditoria.registrar(operacion, tabla="EMPLEADO", valor_ant={"Apellidos": "Peres"},
                            valor_nuevo={"Apellidos": "Pérez"}, motivo="Error de tipeo", ip="10.0.0.5")
    assert b.motivo == "Error de tipeo"
    assert b.valor_ant == '{"Apellidos": "Peres"}'


def test_operacion_invalida():
    with pytest.raises(ValueError):
        auditoria.registrar("MODIFICACION", ip="10.0.0.5")


def test_toma_usuario_e_ip_de_la_peticion():
    usuario = UsuarioFactory()
    request = RequestFactory().get("/", REMOTE_ADDR="192.168.1.20")
    request.user = usuario

    def vista(req):
        auditoria.registrar(Bitacora.Operacion.ALTA, tabla="CARGO")
        return None

    auditoria.AuditoriaMiddleware(vista)(request)
    b = Bitacora.objects.get()
    assert b.usuario == usuario
    assert b.ip == "192.168.1.20"
    # Fuera de la petición el contexto se limpia.
    assert auditoria.contexto_actual() == (None, None)


def test_sin_peticion_usa_ip_local():
    b = auditoria.registrar(Bitacora.Operacion.ALTA, tabla="CATEGORIA")
    assert b.ip == auditoria.IP_SISTEMA
    assert b.usuario is None


def test_bitacora_no_se_modifica_ni_se_borra():
    b = auditoria.registrar(Bitacora.Operacion.ALTA, tabla="CARGO", ip="10.0.0.5")
    b.tabla = "OTRA"
    with pytest.raises(PermissionError):
        b.save()
    with pytest.raises(PermissionError):
        b.delete()
    with pytest.raises(PermissionError):
        Bitacora.objects.filter(pk=b.pk).update(tabla="OTRA")
    with pytest.raises(PermissionError):
        Bitacora.objects.filter(pk=b.pk).delete()
    b.refresh_from_db()
    assert b.tabla == "CARGO"
