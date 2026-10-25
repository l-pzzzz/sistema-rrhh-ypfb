"""Parámetros de planillas (docs/04): UMBRAL_RCIVA, MNI_RCIVA, PORC_ANTICIPO, DIA_ANTICIPO y DIA_F110,
y el aviso al Administrador cuando faltan (CU-05, extensión 2b)."""

from decimal import Decimal

import pytest
from django.core import mail
from django.urls import reverse

from apps.administracion.models import Parametro
from apps.core.parametros import parametros
from apps.planillas.fachada import CalculadoraDescuentos
from apps.planillas.models import Planilla
from apps.planillas.services import AnticipoRechazado, ServicioAnticipos, ServicioF110, avisar_administrador

from .utiles import ANIO, MES, contrato_con_marcacion, encargado, fecha, haber

pytestmark = pytest.mark.django_db

D = Decimal
CLAVES = {"UMBRAL_RCIVA": "2.00", "MNI_RCIVA": "2.00", "PORC_ANTICIPO": "50.00", "DIA_ANTICIPO": "15.00",
          "DIA_F110": "15.00"}


def cambiar(clave, valor, anio=ANIO):
    Parametro.objects.filter(gestion_id=anio, clave=clave).update(valor=D(valor))
    parametros.invalidar(anio)


def test_la_migracion_carga_los_cinco_parametros_de_2026():
    cargados = {p.clave: str(p.valor) for p in Parametro.objects.filter(gestion_id=ANIO, clave__in=CLAVES)}
    assert cargados == CLAVES


def test_umbral_rciva_decide_si_se_retiene_y_mni_rciva_es_el_monto_que_se_resta():
    # Haber 8.000 con el umbral en 3 SMN sigue reteniendo; con 5 SMN (16.560 > 8.000) ya no.
    cambiar("MNI_RCIVA", "1")
    calculo = CalculadoraDescuentos(ANIO).calcular(haber_basico=D("8000"), dias=30)
    assert calculo.base_rc_iva == D("8000.00") - D("976.80") - D("1656.00")
    cambiar("UMBRAL_RCIVA", "5")
    assert CalculadoraDescuentos(ANIO).calcular(haber_basico=D("8000"), dias=30).rc_iva == D("0.00")


def test_umbral_y_mni_son_independientes():
    cambiar("UMBRAL_RCIVA", "5")
    cambiar("MNI_RCIVA", "0")
    assert CalculadoraDescuentos(ANIO).calcular(haber_basico=D("3000"), dias=30).base_rc_iva == D("0.00")
    cambiar("UMBRAL_RCIVA", "1")
    calculo = CalculadoraDescuentos(ANIO).calcular(haber_basico=D("3000"), dias=30)
    assert calculo.base_rc_iva == D("3000.00")  # sin monto no imponible; el total no supera el umbral de AFP


def test_porc_y_dia_anticipo_se_leen_de_parametro():
    haber("3000")
    contrato = contrato_con_marcacion(30)
    cambiar("DIA_ANTICIPO", "20")
    with pytest.raises(AnticipoRechazado, match="después del día 20"):
        ServicioAnticipos().registrar(contrato, fecha(18), D("100"))
    cambiar("PORC_ANTICIPO", "10")
    with pytest.raises(AnticipoRechazado, match=r"10 %.*300,00"):
        ServicioAnticipos().registrar(contrato, fecha(25), D("301"))
    ServicioAnticipos().registrar(contrato, fecha(25), D("300"))


def test_dia_f110_se_lee_de_parametro():
    contrato = contrato_con_marcacion(30)
    cambiar("DIA_F110", "10")
    f110 = ServicioF110().registrar(contrato, ANIO, MES, D("500"), fecha(12))
    assert ServicioF110.mes_de_aplicacion(f110) == (ANIO, MES + 1)


def test_aviso_al_administrador_por_correo(settings):
    settings.CORREO_ADMINISTRADOR = ["admin@ypfb.test", "otro@ypfb.test"]
    assert avisar_administrador("Faltan parámetros", "Detalle")
    assert mail.outbox[0].to == ["admin@ypfb.test", "otro@ypfb.test"]
    assert not avisar_administrador("Faltan parámetros", "Detalle")  # no se repite en la misma hora
    assert len(mail.outbox) == 1


def test_sin_correo_configurado_solo_pantalla(settings):
    settings.CORREO_ADMINISTRADOR = []
    assert not avisar_administrador("Faltan parámetros", "Detalle")
    assert mail.outbox == []


def test_faltan_parametros_bloquea_en_pantalla_y_avisa(client, settings):
    settings.CORREO_ADMINISTRADOR = ["admin@ypfb.test"]
    haber("3000")
    contrato_con_marcacion(30)
    Parametro.objects.filter(gestion_id=ANIO, clave="MNI_RCIVA").delete()
    parametros.invalidar(ANIO)
    client.force_login(encargado())

    respuesta = client.get(reverse("planillas:preplanilla", args=[ANIO, MES]), follow=True)

    assert "MNI_RCIVA" in respuesta.content.decode()
    assert not Planilla.objects.exists()
    assert len(mail.outbox) == 1
    assert "MNI_RCIVA" in mail.outbox[0].body
