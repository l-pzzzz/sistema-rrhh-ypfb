"""RNF-04: procesar 2.500 contratos en menos de 5 minutos."""

import time

import pytest

from apps.core.tests.fabricas import EmpleadoFactory
from apps.kardex.models import Categoria, Contrato
from apps.planillas.fachada import FachadaPlanilla
from apps.planillas.models import BoletaPago, Marcacion

from .utiles import ANIO, MES, encargado, fecha, haber

pytestmark = pytest.mark.django_db

CONTRATOS = 2500
LIMITE_SEGUNDOS = 5 * 60


def test_rnf_04_planilla_de_2500_contratos_en_menos_de_5_minutos():
    haber("8000")
    empleados = EmpleadoFactory.create_batch(CONTRATOS)
    categoria = Categoria.objects.get(cod="A")
    Contrato.objects.bulk_create(
        Contrato(empleado=e, categoria=categoria, fecha_inicio=fecha(5, mes=1)) for e in empleados
    )
    Marcacion.objects.bulk_create(
        Marcacion(contrato_id=nro, anio=ANIO, mes=MES, dias_trab=30)
        for nro in Contrato.objects.values_list("nro", flat=True)
    )
    fachada = FachadaPlanilla()
    usuario = encargado()

    inicio = time.perf_counter()
    preplanilla = fachada.generar_preplanilla(ANIO, MES)
    fachada.aprobar_y_cerrar(preplanilla.planilla, usuario)
    duracion = time.perf_counter() - inicio

    assert BoletaPago.objects.count() == CONTRATOS
    assert duracion < LIMITE_SEGUNDOS
