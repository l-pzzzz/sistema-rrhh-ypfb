"""CU-05.1 Importar días trabajados y CU-05.3 Reportar inconsistencias (RF-10), patrón Adapter."""

import io

import openpyxl
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.administracion.models import Bitacora
from apps.core.tests.fabricas import ContratoFactory, EmpleadoFactory
from apps.kardex.models import Contrato
from apps.planillas.asistencia import (
    AdaptadorArchivoAsistencia,
    ArchivoInvalido,
    ArchivoMarcacionesCSV,
    IFuenteAsistencia,
)
from apps.planillas.fachada import FachadaPlanilla
from apps.planillas.models import Marcacion
from apps.planillas.services import PlanillaCerrada

from .utiles import ANIO, MES, encargado, haber

pytestmark = pytest.mark.django_db


def csv(texto, nombre="marcaciones.csv"):
    return SimpleUploadedFile(nombre, texto.encode("utf-8"))


def excel(filas):
    libro = openpyxl.Workbook()
    hoja = libro.active
    for fila in filas:
        hoja.append(fila)
    salida = io.BytesIO()
    libro.save(salida)
    return SimpleUploadedFile("marcaciones.xlsx", salida.getvalue())


def importar(archivo, motivo=None):
    fuente = AdaptadorArchivoAsistencia(ArchivoMarcacionesCSV(archivo))
    return FachadaPlanilla().importar_asistencia(fuente, ANIO, MES, motivo=motivo)


def test_adaptador_implementa_la_interfaz():
    assert issubclass(AdaptadorArchivoAsistencia, IFuenteAsistencia)


def test_rf_10_ci_inexistente_es_inconsistencia_y_el_resto_se_importa():
    contrato = ContratoFactory()
    resultado = importar(csv(f"CI,DiasTrab\n{contrato.empleado.ci},25\n999999,30\n"))

    assert resultado.importados == 1
    assert Marcacion.objects.get(contrato=contrato, anio=ANIO, mes=MES).dias_trab == 25
    assert [(i.ci, i.motivo) for i in resultado.inconsistencias] == [("999999", "CI no registrado")]


def test_rf_10_empleado_sin_contrato_vigente():
    sin_contrato = EmpleadoFactory()
    concluido = ContratoFactory(estado=Contrato.Estado.CONCLUIDO)
    resultado = importar(csv(f"CI,DiasTrab\n{sin_contrato.ci},30\n{concluido.empleado.ci},30\n"))
    assert resultado.importados == 0
    assert {i.motivo for i in resultado.inconsistencias} == {"Sin contrato vigente"}


@pytest.mark.parametrize("dias", ["31", "-1", "abc", "12.5", ""])
def test_rf_10_dias_fuera_de_0_a_30(dias):
    contrato = ContratoFactory()
    resultado = importar(csv(f"CI,DiasTrab\n{contrato.empleado.ci},{dias}\n"))
    assert resultado.importados == 0
    assert resultado.inconsistencias[0].motivo == "Días trabajados fuera de 0 a 30"


def test_rf_10_cero_dias_es_valido():
    contrato = ContratoFactory()
    assert importar(csv(f"CI,DiasTrab\n{contrato.empleado.ci},0\n")).importados == 1


def test_rf_10_ci_repetido_en_el_archivo():
    contrato = ContratoFactory()
    resultado = importar(csv(f"CI,DiasTrab\n{contrato.empleado.ci},20\n{contrato.empleado.ci},22\n"))
    assert resultado.importados == 0
    assert resultado.inconsistencias[0].motivo == "CI repetido en el archivo"


def test_rf_10_contrato_vigente_sin_marcacion_es_inconsistencia():
    con_marcacion = ContratoFactory()
    sin_marcacion = ContratoFactory()
    resultado = importar(csv(f"CI,DiasTrab\n{con_marcacion.empleado.ci},30\n"))
    assert [(i.ci, i.motivo) for i in resultado.inconsistencias] == [
        (sin_marcacion.empleado.ci, "Contrato vigente sin marcación")
    ]


def test_rf_10_excel_con_ci_numerico_y_complemento():
    contrato = ContratoFactory(empleado=EmpleadoFactory(ci="7654321-1A"))
    otro = ContratoFactory(empleado=EmpleadoFactory(ci="5550001"))
    resultado = importar(excel([("CI", "DiasTrab"), ("7654321-1A", 30), (5550001, 28)]))
    assert resultado.importados == 2
    assert Marcacion.objects.get(contrato=contrato).dias_trab == 30
    assert Marcacion.objects.get(contrato=otro).dias_trab == 28


def test_rf_10_csv_con_punto_y_coma():
    contrato = ContratoFactory()
    assert importar(csv(f"CI;DiasTrab\n{contrato.empleado.ci};30\n")).importados == 1


@pytest.mark.parametrize(
    "archivo",
    [
        csv("CI,Dias\n1,30\n"),
        csv("", nombre="vacio.csv"),
        csv("CI,DiasTrab\n1,30\n", nombre="marcaciones.txt"),
        SimpleUploadedFile("roto.xlsx", b"no es un excel"),
    ],
)
def test_rf_10_regla_1_estructura_invalida(archivo):
    with pytest.raises(ArchivoInvalido):
        importar(archivo)
    assert not Marcacion.objects.exists()


def test_rf_10_regla_4_reimportar_reemplaza_y_exige_motivo():
    contrato = ContratoFactory()
    importar(csv(f"CI,DiasTrab\n{contrato.empleado.ci},20\n"))
    with pytest.raises(ValueError, match="motivo"):
        importar(csv(f"CI,DiasTrab\n{contrato.empleado.ci},25\n"))

    resultado = importar(csv(f"CI,DiasTrab\n{contrato.empleado.ci},25\n"), motivo="Archivo corregido por RRHH")

    assert resultado.reemplazados == 1
    assert Marcacion.objects.get(contrato=contrato).dias_trab == 25
    b = Bitacora.objects.get(operacion=Bitacora.Operacion.ACTUALIZACION, tabla="MARCACION")
    assert b.motivo == "Archivo corregido por RRHH"


def test_rf_10_regla_4_no_se_reimporta_con_planilla_cerrada():
    haber("3000")
    contrato = ContratoFactory()
    importar(csv(f"CI,DiasTrab\n{contrato.empleado.ci},20\n"))
    fachada = FachadaPlanilla()
    fachada.aprobar_y_cerrar(fachada.generar_preplanilla(ANIO, MES).planilla, encargado())

    with pytest.raises(PlanillaCerrada):
        importar(csv(f"CI,DiasTrab\n{contrato.empleado.ci},30\n"), motivo="Cambio")
    assert Marcacion.objects.get(contrato=contrato).dias_trab == 20


def test_obtener_dias_trabajados():
    contrato = ContratoFactory()
    otro = ContratoFactory()
    fuente = AdaptadorArchivoAsistencia(ArchivoMarcacionesCSV(csv(f"CI,DiasTrab\n{contrato.empleado.ci},18\n")))
    assert fuente.obtener_dias_trabajados(contrato, ANIO, MES) == 18
    assert fuente.obtener_dias_trabajados(otro, ANIO, MES) is None
