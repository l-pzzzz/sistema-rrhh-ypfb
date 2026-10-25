"""Comando cargar_datos_demo: idempotente, solo con DEBUG y listo para procesar la planilla completa."""

from io import StringIO
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.administracion.models import Feriado, Usuario
from apps.core.management.commands import cargar_datos_demo as demo
from apps.cps.models import AfiliacionCPS
from apps.kardex.models import AjusteSalarial, Cargo, Contrato, Empleado, Ubicacion
from apps.planillas.asistencia import AdaptadorArchivoAsistencia, ArchivoMarcacionesCSV
from apps.planillas.fachada import FachadaPlanilla
from apps.planillas.models import Anticipo, FormularioF110

pytestmark = pytest.mark.django_db

CSV = Path(__file__).resolve().parent.parent / "docs" / "demo" / "marcaciones_ejemplo.csv"


def cargar():
    salida = StringIO()
    call_command("cargar_datos_demo", stdout=salida)
    return salida.getvalue()


@pytest.fixture
def desarrollo(settings):
    settings.DEBUG = True


def test_se_niega_a_correr_sin_debug(settings):
    settings.DEBUG = False
    with pytest.raises(CommandError, match="DEBUG"):
        cargar()
    assert not Empleado.objects.exists()


def test_carga_los_datos_pedidos(desarrollo):
    salida = cargar()
    assert Ubicacion.objects.count() == 9
    assert Cargo.objects.exists()
    assert set(AjusteSalarial.objects.values_list("categoria_id", flat=True)) == {"A", "B", "C"}
    assert Feriado.objects.filter(fecha__year=2026).count() == len(demo.FERIADOS)
    assert sorted(Usuario.objects.values_list("login", flat=True)) == sorted(login for login, _ in demo.USUARIOS)
    assert Empleado.objects.count() == 20
    assert Contrato.objects.filter(estado=Contrato.Estado.VIGENTE).count() == 20
    assert AfiliacionCPS.objects.count() == 20
    assert Anticipo.objects.count() == demo.CON_ANTICIPO
    assert FormularioF110.objects.count() == demo.CON_F110
    # Las contraseñas salen una sola vez por consola y no quedan en claro en la base.
    for login in ("afiliador", "pagos", "vacaciones", "admin", "consulta"):
        assert login in salida
    assert not Usuario.objects.filter(password__in=salida.split()).exists()
    assert {c.categoria_id for c in Contrato.objects.all()} == {"A", "B", "C"}


def test_es_idempotente(desarrollo):
    cargar()
    conteos = (Empleado.objects.count(), Contrato.objects.count(), Usuario.objects.count(),
               Feriado.objects.count(), Anticipo.objects.count(), FormularioF110.objects.count(),
               AfiliacionCPS.objects.count(), Cargo.objects.count())
    segunda = cargar()
    assert (Empleado.objects.count(), Contrato.objects.count(), Usuario.objects.count(),
            Feriado.objects.count(), Anticipo.objects.count(), FormularioF110.objects.count(),
            AfiliacionCPS.objects.count(), Cargo.objects.count()) == conteos
    assert "no se generaron contraseñas nuevas" in segunda


def test_el_csv_de_ejemplo_cubre_a_los_20_y_procesa_la_planilla_completa(desarrollo):
    cargar()
    assert CSV.read_text(encoding="utf-8").splitlines()[1:] == [
        f"{demo.ci_demo(n)},{demo.dias_demo(n)}" for n in range(1, 21)
    ]
    archivo = SimpleUploadedFile("marcaciones_ejemplo.csv", CSV.read_bytes())
    fuente = AdaptadorArchivoAsistencia(ArchivoMarcacionesCSV(archivo))
    fachada = FachadaPlanilla()

    resultado = fachada.importar_asistencia(fuente, demo.GESTION, demo.MES_DEMO)
    preplanilla = fachada.generar_preplanilla(demo.GESTION, demo.MES_DEMO)

    assert resultado.inconsistencias == []
    assert len(preplanilla.lineas) == 20
    assert preplanilla.inconsistencias == []
