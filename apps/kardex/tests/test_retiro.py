"""CU-02.4 Registrar retiro del empleado (RF-28)."""

import datetime
import json

import pytest
from django.core.exceptions import ValidationError

from apps.administracion.models import Bitacora
from apps.core.tests.fabricas import ContratoFactory
from apps.kardex.models import Contrato, Empleado
from apps.kardex.services import ServicioContrato

pytestmark = pytest.mark.django_db

INICIO = datetime.date(2026, 1, 5)


def test_retiro_concluye_contrato_y_retira_empleado():
    """RF-28, regla 1: el empleado pasa a RETIRADO y su contrato a CONCLUIDO."""
    contrato = ContratoFactory(fecha_inicio=INICIO)
    ServicioContrato().registrar_retiro(
        contrato, datetime.date(2026, 10, 23), Contrato.TipoRetiro.DESPIDO_INJUSTIFICADO, "Reestructuración"
    )
    contrato.refresh_from_db()
    assert contrato.estado == Contrato.Estado.CONCLUIDO
    assert contrato.fecha_retiro == datetime.date(2026, 10, 23)
    assert contrato.tipo_retiro == Contrato.TipoRetiro.DESPIDO_INJUSTIFICADO
    assert contrato.motivo_retiro == "Reestructuración"
    assert contrato.empleado.estado == Empleado.Estado.RETIRADO
    # Su información sigue disponible para consulta.
    assert Empleado.objects.filter(pk=contrato.empleado_id).exists()


def test_retiro_queda_en_bitacora():
    contrato = ContratoFactory(fecha_inicio=INICIO)
    ServicioContrato().registrar_retiro(contrato, datetime.date(2026, 5, 4), Contrato.TipoRetiro.VOLUNTARIO, "Renuncia")
    b = Bitacora.objects.get(operacion=Bitacora.Operacion.BAJA, tabla="contrato")
    assert b.motivo == "Renuncia"
    assert json.loads(b.valor_ant)["estado"] == "VIGENTE"
    assert json.loads(b.valor_nuevo)["estado"] == "CONCLUIDO"
    assert Bitacora.objects.filter(operacion=Bitacora.Operacion.BAJA, tabla="empleado").exists()


def test_fecha_retiro_anterior_al_inicio_rechazada():
    """RF-28, regla 2."""
    contrato = ContratoFactory(fecha_inicio=INICIO)
    with pytest.raises(ValidationError, match="no puede ser anterior al inicio del contrato"):
        ServicioContrato().registrar_retiro(contrato, datetime.date(2026, 1, 4), Contrato.TipoRetiro.VOLUNTARIO, "x")
    contrato.refresh_from_db()
    assert contrato.estado == Contrato.Estado.VIGENTE


def test_retiro_el_mismo_dia_del_inicio():
    contrato = ContratoFactory(fecha_inicio=INICIO)
    ServicioContrato().registrar_retiro(contrato, INICIO, Contrato.TipoRetiro.VOLUNTARIO, "Renuncia")
    assert Contrato.objects.get(pk=contrato.pk).estado == Contrato.Estado.CONCLUIDO


def test_retiro_exige_tipo_y_motivo():
    contrato = ContratoFactory(fecha_inicio=INICIO)
    with pytest.raises(ValidationError, match="tipo de retiro"):
        ServicioContrato().registrar_retiro(contrato, datetime.date(2026, 5, 4), "JUBILACION", "x")
    with pytest.raises(ValidationError, match="motivo"):
        ServicioContrato().registrar_retiro(contrato, datetime.date(2026, 5, 4), Contrato.TipoRetiro.VOLUNTARIO, "")


def test_contrato_concluido_no_se_retira_de_nuevo():
    contrato = ContratoFactory(fecha_inicio=INICIO)
    servicio = ServicioContrato()
    servicio.registrar_retiro(contrato, datetime.date(2026, 5, 4), Contrato.TipoRetiro.VOLUNTARIO, "Renuncia")
    with pytest.raises(ValidationError, match="vigente"):
        servicio.registrar_retiro(contrato, datetime.date(2026, 5, 5), Contrato.TipoRetiro.VOLUNTARIO, "Otra")
