"""Casos de prueba de aceptación de docs/07: PL-01, PL-02, PL-03, AN-01 y AN-02.

Los valores esperados se calcularon a mano en el informe y no se cambian para que la prueba pase.
"""

from decimal import Decimal

import pytest

from apps.planillas.fachada import FachadaPlanilla
from apps.planillas.models import BoletaPago, DetalleBoleta
from apps.planillas.services import AnticipoRechazado, ServicioAnticipos, ServicioF110

from .utiles import ANIO, MES, contrato_con_marcacion, encargado, fecha, haber, usar_valores_vigentes

pytestmark = pytest.mark.django_db

D = Decimal


def linea_de(contrato):
    preplanilla = FachadaPlanilla().generar_preplanilla(ANIO, MES)
    return next(linea for linea in preplanilla.lineas if linea.contrato.nro == contrato.nro)


def test_pl_01_valores_del_caso():
    """PL-01: haber 8.000; 30 días; anticipo 1.000; F110 500 → líquido Bs 5.605,74."""
    haber("8000")
    contrato = contrato_con_marcacion(30)
    ServicioAnticipos().registrar(contrato, fecha(20), D("1000"))
    ServicioF110().registrar(contrato, ANIO, MES, D("500"), fecha(10))

    linea = linea_de(contrato)

    assert linea.calculo.afp == D("976.80")
    assert linea.calculo.impuesto == D("482.46")
    assert linea.calculo.credito == D("65.00")
    assert linea.calculo.rc_iva == D("417.46")
    assert linea.calculo.tot_descuentos == D("2394.26")
    assert linea.calculo.liquido == D("5605.74")


def test_pl_01_boleta_cerrada_guarda_los_mismos_valores():
    haber("8000")
    contrato = contrato_con_marcacion(30)
    ServicioAnticipos().registrar(contrato, fecha(20), D("1000"))
    ServicioF110().registrar(contrato, ANIO, MES, D("500"), fecha(10))
    fachada = FachadaPlanilla()
    planilla = fachada.generar_preplanilla(ANIO, MES).planilla

    fachada.aprobar_y_cerrar(planilla, encargado())

    boleta = BoletaPago.objects.get(planilla=planilla, contrato=contrato)
    assert boleta.liquido == D("5605.74")
    assert boleta.tot_descuentos == D("2394.26")
    detalle = {d.concepto: d for d in boleta.detalles.all()}
    assert detalle[DetalleBoleta.Concepto.AFP].monto == D("976.80")
    assert detalle[DetalleBoleta.Concepto.RC_IVA].monto == D("417.46")


def test_pl_02_haber_que_no_supera_dos_smn():
    """PL-02: haber 3.000; 20 días → sueldo ganado 2.000,00; sin AFP ni RC-IVA; líquido Bs 2.000,00."""
    haber("3000")
    contrato = contrato_con_marcacion(20)

    linea = linea_de(contrato)

    assert linea.calculo.sueldo_ganado == D("2000.00")
    assert linea.calculo.afp == D("0.00")
    assert linea.calculo.rc_iva == D("0.00")
    assert linea.calculo.liquido == D("2000.00")


def test_pl_03_valores_vigentes():
    """PL-03: haber 8.000; 30 días; F110 500 con valores vigentes → saldo a favor 15,18; líquido Bs 6.983,20."""
    usar_valores_vigentes()
    haber("8000")
    contrato = contrato_con_marcacion(30)
    ServicioF110().registrar(contrato, ANIO, MES, D("500"), fecha(10))

    linea = linea_de(contrato)

    assert linea.calculo.afp == D("1016.80")
    assert linea.calculo.impuesto == D("49.82")
    assert linea.calculo.credito == D("65.00")
    assert linea.calculo.rc_iva == D("0.00")
    assert linea.calculo.saldo_favor == D("15.18")
    assert linea.calculo.liquido == D("6983.20")


def test_an_01_anticipo_supera_el_50_por_ciento():
    """AN-01: anticipo de 3.500 con haber 6.000 el día 20 → rechazado, supera el 50 % (Bs 3.000)."""
    haber("6000")
    contrato = contrato_con_marcacion(30)

    with pytest.raises(AnticipoRechazado, match=r"50 %.*3\.000,00"):
        ServicioAnticipos().registrar(contrato, fecha(20), D("3500"))
    assert not contrato.anticipos.exists()


def test_an_02_anticipo_antes_del_dia_15():
    """AN-02: anticipo de 1.000 el día 10 → rechazado, solo después del día 15."""
    haber("6000")
    contrato = contrato_con_marcacion(30)

    with pytest.raises(AnticipoRechazado, match="después del día 15"):
        ServicioAnticipos().registrar(contrato, fecha(10), D("1000"))
    assert not contrato.anticipos.exists()
