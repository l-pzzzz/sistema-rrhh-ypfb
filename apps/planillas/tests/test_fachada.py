"""FachadaPlanilla: CU-05.2 preplanilla, CU-05.4 aprobar y cerrar y CU-05.5 boletas (RF-11, RF-13, RF-16)."""

import json
from decimal import Decimal

import pytest
from django.core.cache import cache

from apps.administracion.models import Bitacora, GestionSalarial, Parametro
from apps.core.parametros import ParametroNoConfigurado, parametros
from apps.kardex.models import Contrato
from apps.planillas.fachada import FachadaPlanilla, GeneradorBoletas
from apps.planillas.models import BoletaPago, DetalleBoleta, Marcacion, Planilla
from apps.planillas.services import HaberNoConfigurado, PlanillaCerrada, ServicioAnticipos, ServicioF110

from .utiles import ANIO, MES, contrato_con_marcacion, encargado, fecha, haber

pytestmark = pytest.mark.django_db

D = Decimal
C = DetalleBoleta.Concepto


@pytest.fixture
def fachada():
    return FachadaPlanilla()


def cerrar(fachada, anio=ANIO, mes=MES, usuario=None):
    planilla = fachada.generar_preplanilla(anio, mes).planilla
    return fachada.aprobar_y_cerrar(planilla, usuario or encargado())


def test_preplanilla_solo_incluye_contratos_vigentes_con_marcacion(fachada):
    haber("3000")
    vigente = contrato_con_marcacion(30)
    contrato_con_marcacion(30, estado=Contrato.Estado.CONCLUIDO)
    sin_marcacion = contrato_con_marcacion(30, mes=MES + 1)

    preplanilla = fachada.generar_preplanilla(ANIO, MES)

    assert [linea.contrato for linea in preplanilla.lineas] == [vigente]
    assert [(i.ci, i.motivo) for i in preplanilla.inconsistencias] == [
        (sin_marcacion.empleado.ci, "Contrato vigente sin marcación")
    ]
    assert preplanilla.planilla.estado == Planilla.Estado.PREPLANILLA
    assert not BoletaPago.objects.exists()  # RF-16, regla 1: sin boletas hasta el cierre.


def test_preplanilla_usa_el_haber_de_la_categoria_del_contrato(fachada):
    haber("3000", categoria="A")
    haber("4500", categoria="B")
    contrato = contrato_con_marcacion(30, categoria_id="B")
    linea = fachada.generar_preplanilla(ANIO, MES).lineas[0]
    assert linea.contrato == contrato
    assert linea.calculo.haber_basico == D("4500.00")


def test_totales_generales(fachada):
    haber("3000")
    contrato_con_marcacion(30)
    contrato_con_marcacion(15)
    preplanilla = fachada.generar_preplanilla(ANIO, MES)
    assert preplanilla.totales["tot_ingresos"] == D("4500.00")
    assert preplanilla.totales["liquido"] == D("4500.00")


def test_rf_11_regla_4_sin_parametros_no_se_procesa(fachada):
    haber("3000")
    contrato_con_marcacion(30)
    Parametro.objects.filter(gestion_id=ANIO, clave="SMN").delete()
    parametros.invalidar(ANIO)
    with pytest.raises(ParametroNoConfigurado):
        fachada.generar_preplanilla(ANIO, MES)
    assert not Planilla.objects.exists()


def test_gestion_inexistente_no_se_procesa(fachada):
    with pytest.raises(ParametroNoConfigurado):
        fachada.generar_preplanilla(ANIO + 5, MES)


def test_sin_haber_basico_de_la_categoria_no_se_procesa(fachada):
    contrato_con_marcacion(30)
    with pytest.raises(HaberNoConfigurado, match="categoría A"):
        fachada.generar_preplanilla(ANIO, MES)


def test_mes_invalido(fachada):
    with pytest.raises(ValueError):
        fachada.generar_preplanilla(ANIO, 13)


def test_alta_de_la_planilla_queda_una_sola_vez_en_bitacora(fachada):
    haber("3000")
    contrato_con_marcacion(30)
    fachada.generar_preplanilla(ANIO, MES)
    fachada.generar_preplanilla(ANIO, MES)
    assert Bitacora.objects.filter(operacion=Bitacora.Operacion.ALTA, tabla="PLANILLA").count() == 1


# --- Otros ingresos (borrador en caché hasta el cierre) ------------------------------------------


def test_otros_ingresos_se_guardan_como_borrador_y_pasan_a_la_boleta(fachada):
    haber("3000")
    contrato = contrato_con_marcacion(30)
    planilla = fachada.generar_preplanilla(ANIO, MES).planilla

    fachada.registrar_otros_ingresos(planilla, contrato.nro, D("250.50"))

    linea = fachada.generar_preplanilla(ANIO, MES).lineas[0]
    assert linea.calculo.otros_ingresos == D("250.50")
    assert linea.calculo.tot_ingresos == D("3250.50")

    fachada.aprobar_y_cerrar(planilla, encargado())
    detalle = DetalleBoleta.objects.get(boleta__contrato=contrato, concepto=C.OTROS_INGRESOS)
    assert detalle.monto == D("250.50")
    assert cache.get(fachada.clave_borrador(planilla)) is None


def test_otros_ingresos_en_cero_se_quitan_del_borrador(fachada):
    haber("3000")
    contrato = contrato_con_marcacion(30)
    planilla = fachada.generar_preplanilla(ANIO, MES).planilla
    fachada.registrar_otros_ingresos(planilla, contrato.nro, D("100"))
    fachada.registrar_otros_ingresos(planilla, contrato.nro, D("0"))
    assert fachada.otros_ingresos(planilla) == {}


@pytest.mark.parametrize("monto", [D("-1"), D("100000000")])
def test_otros_ingresos_invalidos(fachada, monto):
    haber("3000")
    contrato = contrato_con_marcacion(30)
    planilla = fachada.generar_preplanilla(ANIO, MES).planilla
    with pytest.raises(ValueError):
        fachada.registrar_otros_ingresos(planilla, contrato.nro, monto)


def test_otros_ingresos_de_un_contrato_fuera_de_la_planilla(fachada):
    haber("3000")
    contrato_con_marcacion(30)
    otro = contrato_con_marcacion(30, mes=MES + 1)
    planilla = fachada.generar_preplanilla(ANIO, MES).planilla
    with pytest.raises(ValueError, match="no está en la planilla"):
        fachada.registrar_otros_ingresos(planilla, otro.nro, D("10"))


# --- Aprobar y cerrar (CU-05.4) y boletas (CU-05.5) ----------------------------------------------


def test_cierre_registra_quien_aprobo_y_genera_boletas(fachada):
    haber("3000")
    contrato_con_marcacion(30)
    contrato_con_marcacion(20)
    usuario = encargado()

    planilla = cerrar(fachada, usuario=usuario)

    planilla.refresh_from_db()
    assert planilla.estado == Planilla.Estado.CERRADA
    assert planilla.aprobado_por == usuario
    assert planilla.fecha_cierre is not None
    assert planilla.boletas.count() == 2
    assert DetalleBoleta.objects.filter(boleta__planilla=planilla).count() == 2 * len(C)


def test_detalle_guarda_base_y_porcentaje_aplicados(fachada):
    haber("8000")
    contrato = contrato_con_marcacion(30)
    ServicioF110().registrar(contrato, ANIO, MES, D("500"), fecha(10))
    cerrar(fachada)

    detalle = {d.concepto: d for d in DetalleBoleta.objects.filter(boleta__contrato=contrato)}
    assert (detalle[C.SUELDO_GANADO].base, detalle[C.SUELDO_GANADO].monto) == (D("8000.00"), D("8000.00"))
    assert (detalle[C.AFP].base, detalle[C.AFP].porcentaje, detalle[C.AFP].monto) == (
        D("8000.00"), D("12.21"), D("976.80"))
    assert (detalle[C.RC_IVA].base, detalle[C.RC_IVA].porcentaje, detalle[C.RC_IVA].monto) == (
        D("3711.20"), D("13.00"), D("417.46"))
    assert (detalle[C.SALDO_RC_IVA].base, detalle[C.SALDO_RC_IVA].monto) == (D("500.00"), D("0.00"))


def test_afp_no_aplicada_no_guarda_porcentaje(fachada):
    haber("3000")
    contrato = contrato_con_marcacion(30)
    cerrar(fachada)
    afp = DetalleBoleta.objects.get(boleta__contrato=contrato, concepto=C.AFP)
    assert (afp.porcentaje, afp.monto) == (None, D("0.00"))


def test_rf_13_saldo_a_favor_pasa_al_mes_siguiente(fachada):
    from .utiles import usar_valores_vigentes

    usar_valores_vigentes()
    haber("8000")
    contrato = contrato_con_marcacion(30)
    Marcacion.objects.create(contrato=contrato, anio=ANIO, mes=MES + 1, dias_trab=30)
    ServicioF110().registrar(contrato, ANIO, MES, D("500"), fecha(10))
    cerrar(fachada)

    abril = fachada.generar_preplanilla(ANIO, MES + 1).lineas[0]

    assert abril.calculo.saldo_anterior == D("15.18")
    assert abril.calculo.rc_iva == D("34.64")  # 49,82 − 15,18


def test_rf_13_saldo_de_diciembre_pasa_a_enero(fachada):
    haber("3000")
    GestionSalarial.objects.create(anio=ANIO + 1)
    for p in Parametro.objects.filter(gestion_id=ANIO):
        Parametro.objects.create(gestion_id=ANIO + 1, clave=p.clave, valor=p.valor)
    haber("3000", anio=ANIO + 1)
    contrato = contrato_con_marcacion(30, mes=12)
    Marcacion.objects.create(contrato=contrato, anio=ANIO + 1, mes=1, dias_trab=30)
    ServicioF110().registrar(contrato, ANIO, 12, D("100"), fecha(5, mes=12))
    cerrar(fachada, mes=12)

    enero = fachada.generar_preplanilla(ANIO + 1, 1).lineas[0]
    assert enero.calculo.saldo_anterior == D("13.00")


def test_anticipos_quedan_descontados(fachada):
    haber("3000")
    contrato = contrato_con_marcacion(30)
    ServicioAnticipos().registrar(contrato, fecha(16), D("700"))
    planilla = cerrar(fachada)
    assert contrato.anticipos.get().planilla == planilla
    assert BoletaPago.objects.get(contrato=contrato).liquido == D("2300.00")


def test_planilla_cerrada_no_se_modifica(fachada):
    haber("3000")
    contrato = contrato_con_marcacion(30)
    planilla = cerrar(fachada)

    with pytest.raises(PlanillaCerrada):
        fachada.generar_preplanilla(ANIO, MES)
    with pytest.raises(PlanillaCerrada):
        fachada.aprobar_y_cerrar(planilla, encargado())
    with pytest.raises(PlanillaCerrada):
        fachada.registrar_otros_ingresos(planilla, contrato.nro, D("10"))
    assert BoletaPago.objects.count() == 1


def test_no_se_cierra_una_planilla_sin_contratos(fachada):
    haber("3000")
    planilla = fachada.generar_preplanilla(ANIO, MES).planilla
    with pytest.raises(ValueError, match="no tiene contratos"):
        fachada.aprobar_y_cerrar(planilla, encargado())


def test_cierre_en_bitacora_actualizacion_y_un_solo_alta_de_boletas(fachada):
    haber("3000")
    contrato_con_marcacion(30)
    contrato_con_marcacion(20)
    usuario = encargado()
    cerrar(fachada, usuario=usuario)

    cierre = Bitacora.objects.get(operacion=Bitacora.Operacion.ACTUALIZACION, tabla="PLANILLA")
    assert cierre.motivo == "Aprobación y cierre"
    assert cierre.usuario == usuario
    assert json.loads(cierre.valor_ant)["Estado"] == "PREPLANILLA"
    assert json.loads(cierre.valor_nuevo)["Estado"] == "CERRADA"
    boletas = Bitacora.objects.get(operacion=Bitacora.Operacion.ALTA, tabla="BOLETA PAGO")
    assert json.loads(boletas.valor_nuevo) == {"Planilla": cierre_nro(), "Boletas": 2, "TotalLiquido": "5000.00"}


def cierre_nro():
    return Planilla.objects.get().nro


def test_rf_16_cambio_posterior_de_parametros_no_altera_las_boletas(fachada):
    haber("4000")
    contrato = contrato_con_marcacion(30)
    cerrar(fachada)

    Parametro.objects.filter(gestion_id=ANIO, clave="PORC_AFP").update(valor=D("20.00"))
    parametros.invalidar(ANIO)

    afp = DetalleBoleta.objects.get(boleta__contrato=contrato, concepto=C.AFP)
    assert (afp.porcentaje, afp.monto) == (D("12.21"), D("488.40"))


def test_generador_boletas_devuelve_cantidad_y_total(fachada):
    haber("3000")
    contrato_con_marcacion(30)
    preplanilla = fachada.generar_preplanilla(ANIO, MES)
    assert GeneradorBoletas().generar(preplanilla.planilla, preplanilla.lineas) == (1, D("3000.00"))
