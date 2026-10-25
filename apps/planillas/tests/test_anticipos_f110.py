"""CU-06 Registrar anticipo (RF-15) y CU-07 Registrar F110 (RF-13, RF-14)."""

from decimal import Decimal

import pytest

from apps.administracion.models import Bitacora
from apps.kardex.models import Contrato
from apps.planillas.fachada import FachadaPlanilla
from apps.planillas.models import Marcacion
from apps.planillas.services import (
    AnticipoRechazado,
    ContratoNoVigente,
    F110Rechazado,
    ServicioAnticipos,
    ServicioF110,
    contrato_vigente_por_ci,
)

from .utiles import ANIO, MES, contrato_con_marcacion, encargado, fecha, haber

pytestmark = pytest.mark.django_db

D = Decimal


@pytest.fixture
def contrato():
    haber("3000")
    return contrato_con_marcacion(30)


def cerrar_mes(mes=MES):
    fachada = FachadaPlanilla()
    planilla = fachada.generar_preplanilla(ANIO, mes).planilla
    return fachada.aprobar_y_cerrar(planilla, encargado())


# --- Anticipos (RF-15) ---------------------------------------------------------------------------


def test_rf_15_anticipo_sobre_el_tope_se_rechaza(contrato):
    with pytest.raises(AnticipoRechazado, match=r"1\.500,00"):
        ServicioAnticipos().registrar(contrato, fecha(16), D("1600"))


def test_rf_15_anticipo_del_dia_10_se_rechaza(contrato):
    with pytest.raises(AnticipoRechazado):
        ServicioAnticipos().registrar(contrato, fecha(10), D("100"))


def test_rf_15_dia_15_aun_no_permite_anticipo(contrato):
    with pytest.raises(AnticipoRechazado):
        ServicioAnticipos().registrar(contrato, fecha(15), D("100"))


def test_rf_15_el_tope_suma_los_anticipos_del_mes(contrato):
    servicio = ServicioAnticipos()
    servicio.registrar(contrato, fecha(16), D("1000"))
    servicio.registrar(contrato, fecha(20), D("500"))
    with pytest.raises(AnticipoRechazado):
        servicio.registrar(contrato, fecha(25), D("0.01"))
    # El mes siguiente tiene su propio tope.
    servicio.registrar(contrato, fecha(16, mes=MES + 1), D("1500"))


def test_rf_15_anticipo_valido_queda_en_bitacora_con_el_usuario(contrato):
    usuario = encargado()
    anticipo = ServicioAnticipos().registrar(contrato, fecha(16), D("1500"), usuario=usuario)
    assert anticipo.planilla is None
    b = Bitacora.objects.get(operacion=Bitacora.Operacion.ALTA, tabla="ANTICIPO")
    assert b.usuario == usuario


def test_rf_15_monto_debe_ser_positivo(contrato):
    with pytest.raises(AnticipoRechazado):
        ServicioAnticipos().registrar(contrato, fecha(16), D("0"))


def test_rf_15_exige_contrato_vigente(contrato):
    contrato.estado = Contrato.Estado.CONCLUIDO
    contrato.save()
    with pytest.raises(ContratoNoVigente):
        ServicioAnticipos().registrar(contrato, fecha(16), D("100"))


def test_rf_15_anticipo_se_descuenta_una_sola_vez(contrato):
    ServicioAnticipos().registrar(contrato, fecha(16), D("1000"))
    planilla = cerrar_mes()
    anticipo = contrato.anticipos.get()
    assert anticipo.planilla == planilla
    assert ServicioAnticipos().pendientes(ANIO, MES) == {}


def test_rf_15_no_se_registra_en_un_mes_con_planilla_cerrada(contrato):
    cerrar_mes()
    with pytest.raises(AnticipoRechazado, match="cerrada"):
        ServicioAnticipos().registrar(contrato, fecha(20), D("100"))


def test_contrato_vigente_por_ci(contrato):
    assert contrato_vigente_por_ci(contrato.empleado.ci) == contrato
    with pytest.raises(ContratoNoVigente, match="no tiene un contrato vigente"):
        contrato_vigente_por_ci("999")


# --- F110 (RF-13, RF-14) -------------------------------------------------------------------------


def test_rf_14_presentado_hasta_el_15_se_aplica_al_mes_declarado(contrato):
    f110 = ServicioF110().registrar(contrato, ANIO, MES, D("500"), fecha(15))
    assert ServicioF110.mes_de_aplicacion(f110) == (ANIO, MES)
    assert ServicioF110().facturas_aplicables(ANIO, MES) == {contrato.nro: D("500.00")}


def test_rf_14_presentado_el_16_se_aplica_al_mes_siguiente(contrato):
    f110 = ServicioF110().registrar(contrato, ANIO, MES, D("500"), fecha(16))
    assert ServicioF110.mes_de_aplicacion(f110) == (ANIO, MES + 1)
    assert ServicioF110().facturas_aplicables(ANIO, MES) == {}
    assert ServicioF110().facturas_aplicables(ANIO, MES + 1) == {contrato.nro: D("500.00")}


def test_rf_14_diciembre_tardio_pasa_a_enero_de_la_gestion_siguiente(contrato):
    f110 = ServicioF110().registrar(contrato, ANIO, 12, D("500"), fecha(20, mes=12))
    assert ServicioF110.mes_de_aplicacion(f110) == (ANIO + 1, 1)


def test_rf_14_f110_tardio_aparece_en_la_planilla_del_mes_siguiente(contrato):
    haber("8000")
    Marcacion.objects.create(contrato=contrato, anio=ANIO, mes=MES + 1, dias_trab=30)
    ServicioF110().registrar(contrato, ANIO, MES, D("500"), fecha(16))

    marzo = FachadaPlanilla().generar_preplanilla(ANIO, MES).lineas[0]
    abril = FachadaPlanilla().generar_preplanilla(ANIO, MES + 1).lineas[0]

    assert marzo.calculo.credito == D("0.00")
    assert abril.calculo.credito == D("65.00")


def test_rf_14_una_sola_presentacion_por_contrato_y_mes(contrato):
    ServicioF110().registrar(contrato, ANIO, MES, D("500"), fecha(10))
    with pytest.raises(F110Rechazado, match="ya tiene"):
        ServicioF110().registrar(contrato, ANIO, MES, D("100"), fecha(12))


def test_rf_14_credito_lo_calcula_el_sistema(contrato):
    assert ServicioF110().credito(D("500"), ANIO) == D("65.00")


def test_rf_14_monto_no_negativo(contrato):
    with pytest.raises(F110Rechazado):
        ServicioF110().registrar(contrato, ANIO, MES, D("-1"), fecha(10))


def test_rf_14_no_se_aplica_a_una_planilla_cerrada(contrato):
    cerrar_mes()
    with pytest.raises(F110Rechazado, match="cerrada"):
        ServicioF110().registrar(contrato, ANIO, MES, D("500"), fecha(10))


def test_rf_14_queda_en_bitacora(contrato):
    ServicioF110().registrar(contrato, ANIO, MES, D("500"), fecha(10))
    assert Bitacora.objects.filter(operacion=Bitacora.Operacion.ALTA, tabla="FORMULARIO F110").exists()
