"""CU-01.4 y CU-03.2: adjuntar, reemplazar y consultar documentos (RF-04)."""

import json

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.administracion.models import Bitacora
from apps.core.tests.fabricas import DependienteFactory, EmpleadoFactory
from apps.kardex.models import Documento, TipoDocumento
from apps.kardex.services import ServicioDocumento

from .archivos import MB, jpg, pdf, png

pytestmark = pytest.mark.django_db


@pytest.fixture
def titulo(db):
    return TipoDocumento.objects.create(descripcion="Diploma")


def test_tipos_cargados_por_migracion(tipo_ci):
    """Decisión C1: CI, y TITULO y CERTIFICADO para los datos académicos (RF-01)."""
    assert tipo_ci.descripcion == "CI"
    assert set(TipoDocumento.objects.values_list("descripcion", flat=True)) >= {"CI", "TITULO", "CERTIFICADO"}


@pytest.mark.parametrize("archivo", [pdf, png, jpg])
def test_adjuntar_pdf_jpg_png(archivo, titulo):
    documento = ServicioDocumento().adjuntar(EmpleadoFactory(), titulo, archivo())
    assert documento.vigente
    assert documento.fecha_carga is not None
    assert Bitacora.objects.filter(operacion=Bitacora.Operacion.ALTA, tabla="documento").exists()


def test_pdf_de_6_mb_rechazado(titulo):
    """RF-04: al subir un PDF de 6 MB, "El archivo supera el tamaño máximo de 5 MB"."""
    with pytest.raises(ValidationError, match="El archivo supera el tamaño máximo de 5 MB"):
        ServicioDocumento().adjuntar(EmpleadoFactory(), titulo, pdf(tamanio=6 * MB))
    assert not Documento.objects.exists()


def test_pdf_de_5_mb_aceptado(titulo):
    assert ServicioDocumento().adjuntar(EmpleadoFactory(), titulo, pdf(tamanio=5 * MB)).vigente


@pytest.mark.parametrize(
    "archivo",
    [
        SimpleUploadedFile("planilla.xlsx", b"PK\x03\x04datos"),
        SimpleUploadedFile("falso.pdf", b"MZ ejecutable"),
        SimpleUploadedFile("sin_extension", b"%PDF-1.4"),
    ],
)
def test_solo_pdf_jpg_png(archivo, titulo):
    with pytest.raises(ValidationError, match="Solo se aceptan archivos PDF, JPG o PNG"):
        ServicioDocumento().adjuntar(EmpleadoFactory(), titulo, archivo)


def test_reemplazar_deja_la_version_anterior_en_el_historial(titulo):
    """RF-04, regla 3: un documento no se elimina; la versión anterior queda con Vigente = False."""
    empleado = EmpleadoFactory()
    servicio = ServicioDocumento()
    anterior = servicio.adjuntar(empleado, titulo, pdf("v1.pdf"))
    nuevo = servicio.reemplazar(anterior, pdf("v2.pdf"), "Título legalizado")
    anterior.refresh_from_db()
    assert not anterior.vigente
    assert nuevo.vigente
    assert nuevo.tipo == titulo and nuevo.persona_id == empleado.ci
    assert Documento.objects.filter(persona=empleado).count() == 2
    b = Bitacora.objects.get(operacion=Bitacora.Operacion.ACTUALIZACION, tabla="documento")
    assert b.motivo == "Título legalizado"
    assert json.loads(b.valor_ant)["nro"] == anterior.nro
    assert json.loads(b.valor_nuevo)["nro"] == nuevo.nro


def test_reemplazar_valida_archivo_y_motivo(titulo):
    servicio = ServicioDocumento()
    anterior = servicio.adjuntar(EmpleadoFactory(), titulo, pdf())
    with pytest.raises(ValidationError, match="5 MB"):
        servicio.reemplazar(anterior, pdf(tamanio=6 * MB), "Nuevo")
    with pytest.raises(ValidationError, match="motivo"):
        servicio.reemplazar(anterior, pdf(), "")
    anterior.refresh_from_db()
    assert anterior.vigente


def test_documento_reemplazado_no_se_reemplaza_otra_vez(titulo):
    servicio = ServicioDocumento()
    anterior = servicio.adjuntar(EmpleadoFactory(), titulo, pdf())
    servicio.reemplazar(anterior, pdf(), "Nuevo")
    with pytest.raises(ValidationError, match="vigente"):
        servicio.reemplazar(anterior, pdf(), "Otra vez")


def test_documentos_de_un_dependiente(titulo):
    dependiente = DependienteFactory()
    documento = ServicioDocumento().adjuntar(dependiente, titulo, png())
    assert documento.persona_id == dependiente.ci
