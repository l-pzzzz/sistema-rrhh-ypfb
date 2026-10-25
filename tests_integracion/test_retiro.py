"""Integración al registrar el retiro: CU-02.4 (RF-28), CU-04 (RF-08) y CU-10/CU-12 (C2)."""

import datetime

import pytest

from apps.administracion.models import Usuario
from apps.core.senales import contrato_retirado
from apps.core.tests.fabricas import UsuarioFactory
from apps.cps import services
from apps.cps.models import AfiliacionCPS
from apps.kardex.models import Contrato, Empleado
from apps.kardex.services import ServicioContrato

pytestmark = pytest.mark.django_db

RETIRO = datetime.date(2026, 4, 10)


def _retirar(contrato):
    return ServicioContrato().registrar_retiro(contrato, RETIRO, Contrato.TipoRetiro.VOLUNTARIO, "Renuncia")


def test_retiro_fija_fecha_limite_de_baja_en_cps(registrar_contrato):
    contrato = registrar_contrato()
    afil = AfiliacionCPS.objects.get(contrato=contrato)
    services.registrar_afiliacion(afil, "MAT-1", datetime.date(2026, 3, 3))

    _retirar(contrato)

    afil.refresh_from_db()
    assert afil.fecha_lim_baja == services.fecha_limite(RETIRO, "PLAZO_BAJA", services.ubicacion_de(contrato))
    assert afil in services.bajas_pendientes()
    contrato.refresh_from_db()
    assert contrato.estado == Contrato.Estado.CONCLUIDO
    assert contrato.empleado.estado == Empleado.Estado.RETIRADO


def test_retiro_sin_afiliacion_deja_la_afiliacion_pendiente_sin_plazo_de_baja(registrar_contrato):
    contrato = registrar_contrato()
    _retirar(contrato)
    afil = AfiliacionCPS.objects.get(contrato=contrato)
    assert afil.estado == AfiliacionCPS.Estado.PENDIENTE
    assert afil.fecha_lim_baja is None


def test_retiro_emite_contrato_retirado_con_los_datos_del_finiquito(registrar_contrato):
    """Base del finiquito habilitado (RF-20): el evento lleva el contrato con retiro, tipo y motivo."""
    recibidos = []

    def receptor(sender, contrato, **kwargs):
        recibidos.append((contrato.fecha_retiro, contrato.tipo_retiro, contrato.motivo_retiro))

    contrato_retirado.connect(receptor, weak=False, dispatch_uid="prueba-integracion")
    try:
        _retirar(registrar_contrato())
    finally:
        contrato_retirado.disconnect(dispatch_uid="prueba-integracion")
    assert recibidos == [(RETIRO, Contrato.TipoRetiro.VOLUNTARIO, "Renuncia")]


@pytest.mark.xfail(reason="Pendiente de C2: DesactivadorCuenta (Administración, CU-12) aún no existe.", strict=True)
def test_retiro_desactiva_la_cuenta_de_usuario(registrar_contrato):
    contrato = registrar_contrato()
    usuario = UsuarioFactory(empleado=contrato.empleado)
    _retirar(contrato)
    assert Usuario.objects.get(pk=usuario.pk).activo is False


@pytest.mark.xfail(reason="Pendiente de C2: HabilitadorFiniquito (Finiquitos, CU-10) aún no existe.", strict=True)
def test_retiro_habilita_el_finiquito(registrar_contrato):
    from apps.finiquitos.models import Finiquito

    contrato = registrar_contrato()
    _retirar(contrato)
    assert Finiquito.objects.filter(contrato=contrato).exists()
