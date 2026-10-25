"""Integración Kardex → Planillas: CU-05.2 preplanilla solo con contratos vigentes y marcaciones (RF-10)."""

import pytest

from apps.kardex.models import Contrato
from apps.planillas.fachada import FachadaPlanilla
from apps.planillas.models import Marcacion
from apps.planillas.tests.utiles import ANIO, MES, haber, usar_valores_vigentes

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _parametros():
    haber("3000")
    usar_valores_vigentes()


def _marcar(contrato, dias=30):
    Marcacion.objects.create(contrato=contrato, anio=ANIO, mes=MES, dias_trab=dias)


def test_contrato_vigente_con_marcaciones_aparece_en_la_preplanilla(registrar_contrato):
    contrato = registrar_contrato()
    _marcar(contrato)
    preplanilla = FachadaPlanilla().generar_preplanilla(ANIO, MES)
    assert [linea.contrato.nro for linea in preplanilla.lineas] == [contrato.nro]
    assert preplanilla.inconsistencias == []


def test_contrato_concluido_no_aparece_en_la_preplanilla(registrar_contrato):
    vigente, concluido = registrar_contrato(), registrar_contrato()
    _marcar(vigente)
    _marcar(concluido)
    Contrato.objects.filter(pk=concluido.pk).update(estado=Contrato.Estado.CONCLUIDO)
    preplanilla = FachadaPlanilla().generar_preplanilla(ANIO, MES)
    assert [linea.contrato.nro for linea in preplanilla.lineas] == [vigente.nro]


def test_contrato_vigente_sin_marcacion_se_reporta_como_inconsistencia(registrar_contrato):
    contrato = registrar_contrato()
    preplanilla = FachadaPlanilla().generar_preplanilla(ANIO, MES)
    assert preplanilla.lineas == []
    assert [i.ci for i in preplanilla.inconsistencias] == [contrato.empleado_id]
