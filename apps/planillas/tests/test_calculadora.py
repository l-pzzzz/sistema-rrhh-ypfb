"""CalculadoraDescuentos: RN-01 a RN-05 y RN-07 con los criterios de aceptación de RF-11, RF-12 y RF-13."""

from decimal import Decimal

import pytest

from apps.administracion.models import Parametro
from apps.core.parametros import ParametroNoConfigurado
from apps.planillas.fachada import CalculadoraDescuentos

from .utiles import ANIO, usar_valores_vigentes

pytestmark = pytest.mark.django_db

D = Decimal


def test_rf_11_sueldo_ganado_proporcional_a_los_dias():
    calculo = CalculadoraDescuentos(ANIO).calcular(haber_basico=D("3000"), dias=25)
    assert calculo.sueldo_ganado == D("2500.00")


def test_rn_02_y_rn_07_totales_con_otros_ingresos():
    calculo = CalculadoraDescuentos(ANIO).calcular(haber_basico=D("3000"), dias=30, otros_ingresos=D("200"),
                                                   anticipos=D("500"))
    assert calculo.total_ganado == D("3200.00")
    assert calculo.tot_ingresos == D("3200.00")
    assert calculo.tot_descuentos == D("500.00")
    assert calculo.liquido == D("2700.00")


@pytest.mark.parametrize(("total", "afp"), [("3000", "0.00"), ("4000", "488.40")])
def test_rf_12_afp_con_valores_del_caso(total, afp):
    calculo = CalculadoraDescuentos(ANIO).calcular(haber_basico=D(total), dias=30)
    assert calculo.afp == D(afp)


def test_rf_12_afp_con_valores_vigentes_sin_umbral():
    usar_valores_vigentes()
    calculo = CalculadoraDescuentos(ANIO).calcular(haber_basico=D("4000"), dias=30)
    assert calculo.afp == D("508.40")
    assert calculo.porc_afp == D("12.71")


def test_rf_12_umbral_se_compara_con_el_total_ganado():
    # Haber 4.000 con 20 días: total ganado 2.666,67, no supera 2 × 1.656.
    calculo = CalculadoraDescuentos(ANIO).calcular(haber_basico=D("4000"), dias=20)
    assert calculo.afp == D("0.00")


def test_rf_13_rc_iva_cero_si_el_haber_no_supera_dos_smn():
    calculo = CalculadoraDescuentos(ANIO).calcular(haber_basico=D("3000"), dias=30)
    assert calculo.base_rc_iva == D("0.00")
    assert calculo.rc_iva == D("0.00")


def test_rf_13_credito_mayor_al_impuesto_deja_saldo_a_favor():
    calculo = CalculadoraDescuentos(ANIO).calcular(haber_basico=D("5000"), dias=30, facturas=D("2000"))
    # Base = 5.000 − 610,50 − 3.312 = 1.077,50; impuesto 140,08; crédito 260,00.
    assert calculo.base_rc_iva == D("1077.50")
    assert calculo.impuesto == D("140.08")
    assert calculo.credito == D("260.00")
    assert calculo.rc_iva == D("0.00")
    assert calculo.saldo_favor == D("119.92")


def test_rn_05_saldo_anterior_se_resta_de_la_retencion():
    calculo = CalculadoraDescuentos(ANIO).calcular(haber_basico=D("8000"), dias=30, facturas=D("500"),
                                                   saldo_anterior=D("100"))
    assert calculo.rc_iva == D("317.46")
    assert calculo.saldo_favor == D("0.00")


def test_rn_05_sin_f110_credito_cero_mas_saldo_anterior():
    calculo = CalculadoraDescuentos(ANIO).calcular(haber_basico=D("8000"), dias=30, saldo_anterior=D("15.18"))
    assert calculo.credito == D("0.00")
    assert calculo.rc_iva == D("467.28")


def test_rn_05_saldo_se_conserva_cuando_no_aplica_rc_iva():
    calculo = CalculadoraDescuentos(ANIO).calcular(haber_basico=D("3000"), dias=30, facturas=D("100"),
                                                   saldo_anterior=D("5"))
    assert calculo.rc_iva == D("0.00")
    assert calculo.saldo_favor == D("18.00")


def test_rf_11_regla_4_sin_parametros_no_se_procesa():
    Parametro.objects.filter(gestion_id=ANIO, clave="PORC_AFP").delete()
    with pytest.raises(ParametroNoConfigurado):
        CalculadoraDescuentos(ANIO)
