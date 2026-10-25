"""Vistas de CU-05 a CU-07: acceso por rol (RNF-07) y flujo de la planilla."""

import datetime
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.administracion.models import Bitacora
from apps.core.tests.fabricas import ContratoFactory, UsuarioFactory, rol
from apps.planillas.models import BoletaPago, Planilla

from .utiles import ANIO, MES, encargado, haber

pytestmark = pytest.mark.django_db

RUTAS = [
    ("planillas:inicio", {}),
    ("planillas:procesar", {"anio": ANIO, "mes": MES}),
    ("planillas:preplanilla", {"anio": ANIO, "mes": MES}),
    ("planillas:anticipos", {}),
    ("planillas:f110", {}),
]


@pytest.fixture
def cliente(client):
    client.force_login(encargado())
    return client


@pytest.mark.parametrize(("nombre", "kwargs"), RUTAS)
def test_anonimo_va_al_inicio_de_sesion(client, nombre, kwargs):
    respuesta = client.get(reverse(nombre, kwargs=kwargs))
    assert respuesta.status_code == 302
    assert "/login/" in respuesta.url


@pytest.mark.parametrize(
    "nombre_rol",
    ["Afiliador", "Responsable de Vacaciones y Lactancias", "Consulta", "Administrador del Sistema"],
)
@pytest.mark.parametrize(("nombre", "kwargs"), RUTAS)
def test_otros_roles_reciben_403_y_queda_en_bitacora(client, nombre_rol, nombre, kwargs):
    client.force_login(UsuarioFactory(rol=rol(nombre_rol)))
    assert client.get(reverse(nombre, kwargs=kwargs)).status_code == 403
    assert Bitacora.objects.filter(operacion=Bitacora.Operacion.ACCESO_DENEGADO).exists()


def test_inicio_lista_los_doce_meses(cliente):
    respuesta = cliente.get(reverse("planillas:inicio"))
    assert respuesta.status_code == 200
    assert len(respuesta.context["meses"]) == 12


def test_flujo_importar_revisar_aprobar_y_consultar(cliente):
    haber("3000")
    contrato = ContratoFactory()
    archivo = SimpleUploadedFile("m.csv", f"CI,DiasTrab\n{contrato.empleado.ci},25\n999999,30\n".encode())

    respuesta = cliente.post(reverse("planillas:procesar", args=[ANIO, MES]), {"archivo": archivo})
    assert [i.ci for i in respuesta.context["resultado"].inconsistencias] == ["999999"]

    respuesta = cliente.get(reverse("planillas:preplanilla", args=[ANIO, MES]))
    assert respuesta.context["datos"].lineas[0].calculo.sueldo_ganado == Decimal("2500.00")

    cliente.post(reverse("planillas:preplanilla", args=[ANIO, MES]), {"contrato": contrato.nro, "monto": "100"})
    cliente.post(reverse("planillas:preplanilla", args=[ANIO, MES]), {"accion": "aprobar"})

    assert Planilla.objects.get().estado == Planilla.Estado.CERRADA
    boleta = BoletaPago.objects.get()
    assert boleta.liquido == Decimal("2600.00")
    assert cliente.get(reverse("planillas:detalle", args=[ANIO, MES])).status_code == 200
    assert cliente.get(reverse("planillas:boleta", args=[boleta.nro])).status_code == 200
    # Una planilla cerrada solo se consulta (CU-05, extensión 2a).
    assert cliente.get(reverse("planillas:procesar", args=[ANIO, MES])).status_code == 302


def test_mes_invalido_da_404(cliente):
    assert cliente.get(reverse("planillas:procesar", args=[ANIO, 13])).status_code == 404


def test_sin_parametros_de_la_gestion_se_redirige_con_aviso(cliente):
    assert cliente.get(reverse("planillas:preplanilla", args=[2031, 1])).status_code == 302


def test_registrar_anticipo_por_ci(cliente):
    haber("3000")
    contrato = ContratoFactory()
    url = reverse("planillas:anticipos")
    cliente.post(url, {"ci": contrato.empleado.ci, "fecha": "2026-03-20", "monto": "1000"})
    assert contrato.anticipos.count() == 1
    respuesta = cliente.post(url, {"ci": contrato.empleado.ci, "fecha": "2026-03-21", "monto": "1000"})
    assert respuesta.status_code == 200  # supera el 50 %: el formulario vuelve con el error
    assert "50 %" in respuesta.content.decode()
    assert contrato.anticipos.count() == 1


def test_registrar_f110_por_ci(cliente):
    contrato = ContratoFactory()
    url = reverse("planillas:f110")
    datos = {"ci": contrato.empleado.ci, "anio": ANIO, "mes": MES, "monto": "500", "fecha_pres": "2026-03-16"}
    cliente.post(url, datos)
    assert contrato.formularios_f110.get().fecha_pres == datetime.date(2026, 3, 16)
    assert "ya tiene" in cliente.post(url, datos).content.decode()


def test_ci_sin_contrato_vigente(cliente):
    respuesta = cliente.post(reverse("planillas:anticipos"), {"ci": "000", "fecha": "2026-03-20", "monto": "10"})
    assert "no tiene un contrato vigente" in respuesta.content.decode()
