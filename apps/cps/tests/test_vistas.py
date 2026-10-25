"""Bandeja, formularios y permisos del módulo CPS (CU-04, RF-06 a RF-09, RNF-07)."""

import pytest
from django.urls import reverse

from apps.administracion.models import Bitacora
from apps.core.tests.fabricas import CargoFactory, EmpleadoFactory, UsuarioFactory
from apps.cps import services

from .conftest import fecha, nuevo_contrato, registrar, retirar

pytestmark = pytest.mark.django_db


@pytest.fixture
def cliente(client, afiliador):
    client.force_login(afiliador)
    return client


@pytest.fixture
def hoy(monkeypatch):
    dia = fecha("12/11/2026")
    monkeypatch.setattr("django.utils.timezone.localdate", lambda: dia)
    return dia


def nombres(respuesta):
    return [fila["empleado"].apellidos for fila in respuesta.context["filas"]]


def test_bandeja_muestra_el_semaforo(cliente, hoy):
    empleado = EmpleadoFactory(apellidos="Amarillo")
    registrar(nuevo_contrato("06/11/2026", empleado=empleado))  # vence el 13/11: amarillo
    registrar(nuevo_contrato("12/11/2026", empleado=EmpleadoFactory(apellidos="Verde")))
    registrar(nuevo_contrato("02/11/2026", empleado=EmpleadoFactory(apellidos="Rojo")))
    respuesta = cliente.get(reverse("cps:inicio"))
    colores = {f["empleado"].apellidos: f["color"] for f in respuesta.context["filas"]}
    assert colores == {"Amarillo": "amarillo", "Verde": "verde", "Rojo": "rojo"}


def test_bandeja_filtra_por_semaforo_busqueda_fechas_y_departamento(cliente, hoy):
    cargo = CargoFactory()
    registrar(nuevo_contrato("06/11/2026", empleado=EmpleadoFactory(apellidos="Pérez"), cargo=cargo))
    registrar(nuevo_contrato("02/11/2026", empleado=EmpleadoFactory(apellidos="Rojas")))
    url = reverse("cps:inicio")
    assert nombres(cliente.get(url, {"semaforo": "rojo"})) == ["Rojas"]
    assert nombres(cliente.get(url, {"q": "perez"})) == ["Pérez"]  # sin tildes ni mayúsculas
    assert nombres(cliente.get(url, {"departamento": cargo.ubicacion_id})) == ["Pérez"]
    assert nombres(cliente.get(url, {"desde": "2026-11-12", "hasta": "2026-11-30"})) == ["Pérez"]


def test_htmx_devuelve_solo_la_tabla(cliente):
    respuesta = cliente.get(reverse("cps:inicio"), headers={"HX-Request": "true"})
    assert "cps/_tabla.html" in [t.name for t in respuesta.templates]
    assert "cps/bandeja.html" not in [t.name for t in respuesta.templates]


def test_rf08_bandeja_de_bajas_con_el_contador(cliente):
    contrato = nuevo_contrato("05/01/2026")
    services.registrar_afiliacion(registrar(contrato), "V-1", fecha("06/01/2026"))
    retirar(contrato, "21/10/2026")
    respuesta = cliente.get(reverse("cps:inicio"), {"pestana": "bajas"})
    (fila,) = respuesta.context["filas"]
    assert fila["alerta"].startswith("Desafiliación pendiente. Quedan")
    assert "sigue obligada a pagar las cotizaciones" in respuesta.content.decode()


def test_retiro_sin_afiliacion_sale_de_la_bandeja_de_altas(cliente):
    contrato = nuevo_contrato("05/10/2026")
    registrar(contrato)
    retirar(contrato, "09/10/2026")
    assert nombres(cliente.get(reverse("cps:inicio"))) == []
    assert nombres(cliente.get(reverse("cps:inicio"), {"pestana": "bajas"})) == []


def test_flujo_afiliar_y_dar_de_baja(cliente):
    contrato = nuevo_contrato("23/10/2026")
    afil = registrar(contrato)
    respuesta = cliente.post(reverse("cps:afiliar", args=[afil.nro]), {"matricula": "Z-1", "fecha_afil": "2026-10-30"})
    assert respuesta.status_code == 302
    afil.refresh_from_db()
    assert afil.estado == "EN PLAZO"
    retirar(contrato, "30/11/2026")
    cliente.post(reverse("cps:baja", args=[afil.nro]), {"fecha_desafil": "2026-12-02"})
    afil.refresh_from_db()
    assert afil.estado == "DESAFILIADO"


def test_matricula_repetida_muestra_el_error(cliente):
    primera = registrar(nuevo_contrato("23/10/2026"))
    services.registrar_afiliacion(primera, "Z-2", fecha("26/10/2026"))
    otra = registrar(nuevo_contrato("23/10/2026"))
    respuesta = cliente.post(reverse("cps:afiliar", args=[otra.nro]), {"matricula": "Z-2", "fecha_afil": "2026-10-27"})
    assert respuesta.status_code == 200
    assert f"contrato {primera.contrato_id}" in respuesta.content.decode()


def test_aviso_se_descarga_en_pdf(cliente):
    contrato = nuevo_contrato("23/10/2026")
    contrato.empleado.direccion = "Av. Siempre Viva 123"
    contrato.empleado.save()
    afil = registrar(contrato)
    respuesta = cliente.post(reverse("cps:aviso", args=[afil.nro]), {"tipo": "NUEVO"})
    assert respuesta["Content-Type"] == "application/pdf"
    assert respuesta.content.startswith(b"%PDF")


def test_aviso_incompleto_no_genera_pdf(cliente):
    afil = registrar(nuevo_contrato("23/10/2026"))
    respuesta = cliente.post(reverse("cps:aviso", args=[afil.nro]), {"tipo": "NUEVO"})
    assert respuesta.status_code == 200
    assert "Domicilio" in respuesta.content.decode()


def test_correccion_por_la_vista_exige_motivo(cliente):
    afil = registrar(nuevo_contrato("23/10/2026"))
    services.registrar_afiliacion(afil, "Z-3", fecha("26/10/2026"))
    url = reverse("cps:corregir", args=[afil.nro])
    sin_motivo = cliente.post(url, {"operacion": "CORRECCION", "motivo": "", "matricula": "Z-4"})
    assert sin_motivo.status_code == 200
    cliente.post(url, {"operacion": "CORRECCION", "motivo": "Error de digitación", "matricula": "Z-4"})
    afil.refresh_from_db()
    assert afil.matricula == "Z-4"
    assert Bitacora.objects.filter(operacion="CORRECCION", tabla="afiliacion_cps").count() == 1


def test_historial_por_la_vista(cliente):
    contrato = nuevo_contrato("23/10/2026")
    services.registrar_afiliacion(registrar(contrato), "Z-5", fecha("26/10/2026"))
    respuesta = cliente.get(reverse("cps:historial", args=[contrato.empleado.ci]))
    assert [m["etiqueta"] for m in respuesta.context["movimientos"]] == ["Afiliación pendiente", "Alta"]


@pytest.mark.parametrize("rol", ["Encargado de Pagos", "Responsable de Vacaciones y Lactancias",
                                 "Administrador del Sistema", "Consulta"])
def test_otros_roles_reciben_403_y_queda_en_bitacora(client, rol):
    from apps.core.tests.fabricas import rol as buscar_rol

    client.force_login(UsuarioFactory(rol=buscar_rol(rol)))
    assert client.get(reverse("cps:inicio")).status_code == 403
    assert Bitacora.objects.filter(operacion="ACCESO DENEGADO").exists()


def test_sin_sesion_redirige_al_login(client):
    assert client.get(reverse("cps:inicio")).status_code == 302
