"""Pantallas de CU-01 a CU-03 y acceso por nivel y rol (RNF-07, AGENTS.md §7)."""

import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.administracion.models import Bitacora, Rol
from apps.core.tests.fabricas import (
    CargoFactory,
    ContratoFactory,
    DependienteFactory,
    EmpleadoFactory,
    UsuarioFactory,
    rol,
)
from apps.kardex.models import Contrato, Dependiente, Documento, Empleado, TipoDocumento
from apps.kardex.services import ServicioDocumento

from .archivos import MB, pdf

pytestmark = pytest.mark.django_db

LECTORES = [Rol.ENCARGADO_DE_PAGOS, Rol.RESPONSABLE_VACACIONES, Rol.CONSULTA]


@pytest.fixture
def afiliador(client):
    client.force_login(UsuarioFactory(rol=rol(Rol.AFILIADOR)))
    return client


def login_como(client, nombre_rol):
    client.force_login(UsuarioFactory(rol=rol(nombre_rol)))
    return client


def test_inicio_requiere_sesion(client):
    respuesta = client.get(reverse("kardex:inicio"))
    assert respuesta.status_code == 302
    assert "/login/" in respuesta.url


@pytest.mark.parametrize("nombre_rol", [Rol.AFILIADOR, *LECTORES])
def test_roles_con_acceso_al_kardex_consultan(client, nombre_rol):
    empleado = EmpleadoFactory()
    login_como(client, nombre_rol)
    assert client.get(reverse("kardex:inicio")).status_code == 200
    assert client.get(reverse("kardex:ficha", args=[empleado.ci])).status_code == 200


def test_administrador_no_entra_al_kardex(client):
    login_como(client, Rol.ADMINISTRADOR_DEL_SISTEMA)
    assert client.get(reverse("kardex:inicio")).status_code == 403


@pytest.mark.parametrize("nombre_rol", LECTORES)
def test_solo_lectura_no_registra_y_queda_en_bitacora(client, nombre_rol):
    login_como(client, nombre_rol)
    respuesta = client.post(reverse("kardex:empleado_nuevo"), {"ci": "1234567"})
    assert respuesta.status_code == 403
    assert not Empleado.objects.filter(pk="1234567").exists()
    assert Bitacora.objects.filter(operacion=Bitacora.Operacion.ACCESO_DENEGADO).exists()


def test_solo_lectura_no_ve_botones_de_escritura(client):
    empleado = EmpleadoFactory()
    login_como(client, Rol.CONSULTA)
    contenido = client.get(reverse("kardex:ficha", args=[empleado.ci])).content.decode()
    assert "Nuevo contrato" not in contenido
    assert "Actualizar o corregir" not in contenido


def test_busqueda_htmx_devuelve_solo_resultados(afiliador):
    EmpleadoFactory(apellidos="Pérez")
    respuesta = afiliador.get(reverse("kardex:inicio"), {"q": "perez"}, HTTP_HX_REQUEST="true")
    contenido = respuesta.content.decode()
    assert "Pérez" in contenido
    assert "<html" not in contenido


def test_alertas_en_inicio_del_afiliador(afiliador):
    from apps.kardex.services import ServicioContrato

    hoy = timezone.localdate()
    ContratoFactory(empleado=EmpleadoFactory(fecha_ingreso=hoy - datetime.timedelta(days=7 * 366)))
    ServicioContrato().recalcular_categorias(hoy)
    assert "Cambio de categoría: A → B" in afiliador.get(reverse("kardex:inicio")).content.decode()


def datos_empleado(**cambios):
    return {
        "ci": "1234567-1A", "nombres": "Ana", "apellidos": "Pérez", "fecha_nac": "1990-05-02", "sexo": "F",
        "telefono": "", "codigo": "EMP-0100", "fecha_ingreso": "2026-10-01", "direccion": "",
        "nom_emerg": "", "par_emerg": "", "tel_emerg": "",
    } | cambios


def test_registrar_empleado_y_ci_repetido(afiliador):
    respuesta = afiliador.post(reverse("kardex:empleado_nuevo"), datos_empleado())
    assert respuesta.status_code == 302
    assert Empleado.objects.get(pk="1234567-1A").estado == Empleado.Estado.ACTIVO
    respuesta = afiliador.post(reverse("kardex:empleado_nuevo"), datos_empleado(codigo="EMP-0101"))
    assert respuesta.status_code == 200
    assert "El CI ya está registrado" in respuesta.content.decode()


def test_editar_empleado_con_motivo(afiliador):
    empleado = EmpleadoFactory(apellidos="Perez")
    datos = datos_empleado(apellidos="Pérez", codigo=empleado.codigo, fecha_ingreso="2020-01-06",
                           fecha_nac="1990-01-01", sexo="M", nombres="Juan")
    datos.pop("ci")
    respuesta = afiliador.post(reverse("kardex:empleado_editar", args=[empleado.ci]), datos)
    assert respuesta.status_code == 200  # Sin motivo no se guarda.
    respuesta = afiliador.post(
        reverse("kardex:empleado_editar", args=[empleado.ci]),
        datos | {"operacion": "CORRECCION", "motivo": "Faltaba la tilde"},
    )
    assert respuesta.status_code == 302
    empleado.refresh_from_db()
    assert empleado.apellidos == "Pérez"


def test_registrar_contrato_con_dos_cargos(afiliador):
    empleado = EmpleadoFactory()
    cargos = [CargoFactory(), CargoFactory()]
    url = reverse("kardex:contrato_nuevo", args=[empleado.ci])
    assert "Categoría por antigüedad" in afiliador.get(url).content.decode()
    respuesta = afiliador.post(url, {"fecha_inicio": "2026-10-01", "cargos": [c.pk for c in cargos]})
    assert respuesta.status_code == 302
    contrato = Contrato.objects.get(empleado=empleado)
    assert contrato.cargos.count() == 2


def test_contrato_sin_cargo_muestra_error(afiliador):
    empleado = EmpleadoFactory()
    respuesta = afiliador.post(reverse("kardex:contrato_nuevo", args=[empleado.ci]), {"fecha_inicio": "2026-10-01"})
    assert respuesta.status_code == 200
    assert not Contrato.objects.exists()


def test_segundo_contrato_vigente_redirige_con_error(afiliador):
    contrato = ContratoFactory()
    respuesta = afiliador.get(reverse("kardex:contrato_nuevo", args=[contrato.empleado_id]), follow=True)
    assert "un empleado no puede tener dos contratos vigentes" in respuesta.content.decode()


def test_editar_contrato(afiliador):
    contrato = ContratoFactory()
    contrato.cargos.add(CargoFactory())
    nuevo = CargoFactory()
    respuesta = afiliador.post(
        reverse("kardex:contrato_editar", args=[contrato.nro]),
        {"fecha_inicio": "2026-01-05", "cargos": [nuevo.pk], "operacion": "ACTUALIZACION", "motivo": "Ascenso"},
    )
    assert respuesta.status_code == 302
    assert list(contrato.cargos.all()) == [nuevo]


def test_registrar_retiro(afiliador):
    contrato = ContratoFactory()
    url = reverse("kardex:contrato_retiro", args=[contrato.nro])
    respuesta = afiliador.post(url, {"fecha_retiro": "2026-01-01", "tipo_retiro": "VOLUNTARIO", "motivo_retiro": "x"})
    assert "no puede ser anterior al inicio del contrato" in respuesta.content.decode()
    respuesta = afiliador.post(
        url, {"fecha_retiro": "2026-10-23", "tipo_retiro": "DESPIDO INJUSTIFICADO", "motivo_retiro": "Cierre"}
    )
    assert respuesta.status_code == 302
    contrato.refresh_from_db()
    assert contrato.estado == Contrato.Estado.CONCLUIDO
    assert contrato.empleado.estado == Empleado.Estado.RETIRADO
    # El contrato concluido ya no se retira ni se edita.
    assert afiliador.get(url).status_code == 404


def test_registrar_dependiente_con_avisos(afiliador):
    empleado = ContratoFactory().empleado
    respuesta = afiliador.post(
        reverse("kardex:dependiente_nuevo", args=[empleado.ci]),
        {"ci": "8888888", "nombres": "Luis", "apellidos": "Pérez", "fecha_nac": "1990-01-01", "sexo": "M",
         "parentesco": "HIJO", "fotocopia_ci": pdf("ci.pdf")},
        follow=True,
    )
    contenido = respuesta.content.decode()
    assert Dependiente.objects.filter(pk="8888888", empleado=empleado).exists()
    assert "supera la edad máxima de beneficiario" in contenido
    assert "El trabajador aún no está afiliado a la CPS" in contenido


def test_dependiente_sin_fotocopia(afiliador):
    empleado = EmpleadoFactory()
    respuesta = afiliador.post(
        reverse("kardex:dependiente_nuevo", args=[empleado.ci]),
        {"ci": "8888888", "nombres": "Luis", "apellidos": "Pérez", "fecha_nac": "2015-01-01", "sexo": "M",
         "parentesco": "HIJO"},
    )
    assert respuesta.status_code == 200
    assert not Dependiente.objects.exists()


def test_dependiente_de_otro_trabajador(afiliador):
    otro = DependienteFactory(ci="8888888", empleado=EmpleadoFactory(nombres="María", apellidos="Rojas"))
    empleado = EmpleadoFactory()
    respuesta = afiliador.post(
        reverse("kardex:dependiente_nuevo", args=[empleado.ci]),
        {"ci": otro.ci, "nombres": "Luis", "apellidos": "Pérez", "fecha_nac": "2015-01-01", "sexo": "M",
         "parentesco": "HIJO", "fotocopia_ci": pdf("ci.pdf")},
    )
    assert "Ya está registrado como dependiente de María Rojas" in respuesta.content.decode()


def test_editar_dependiente(afiliador):
    dependiente = DependienteFactory(apellidos="Mamni")
    respuesta = afiliador.post(
        reverse("kardex:dependiente_editar", args=[dependiente.ci]),
        {"nombres": dependiente.nombres, "apellidos": "Mamani", "fecha_nac": "1990-01-01", "sexo": "M",
         "telefono": "", "parentesco": "HIJO", "operacion": "CORRECCION", "motivo": "Error"},
    )
    assert respuesta.status_code == 302
    dependiente.refresh_from_db()
    assert dependiente.apellidos == "Mamani"


def test_adjuntar_reemplazar_y_ver_documento(afiliador):
    empleado = EmpleadoFactory()
    titulo = TipoDocumento.objects.create(descripcion="Título")
    url = reverse("kardex:documento_adjuntar", args=[empleado.ci])
    respuesta = afiliador.post(url, {"tipo": titulo.pk, "archivo": pdf(tamanio=6 * MB)})
    assert "El archivo supera el tamaño máximo de 5 MB" in respuesta.content.decode()
    assert afiliador.post(url, {"tipo": titulo.pk, "archivo": pdf()}).status_code == 302
    documento = Documento.objects.get(persona_id=empleado.ci)

    respuesta = afiliador.post(
        reverse("kardex:documento_reemplazar", args=[documento.nro]), {"archivo": pdf("v2.pdf"), "motivo": "Nuevo"}
    )
    assert respuesta.status_code == 302
    assert Documento.objects.filter(persona_id=empleado.ci, vigente=True).count() == 1

    respuesta = afiliador.get(reverse("kardex:documento_ver", args=[documento.nro]))
    assert respuesta.status_code == 200
    assert b"".join(respuesta.streaming_content).startswith(b"%PDF")


def test_documento_de_dependiente(afiliador):
    dependiente = DependienteFactory()
    titulo = TipoDocumento.objects.create(descripcion="Certificado de nacimiento")
    respuesta = afiliador.post(
        reverse("kardex:documento_adjuntar", args=[dependiente.ci]), {"tipo": titulo.pk, "archivo": pdf()}
    )
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("kardex:ficha", args=[dependiente.empleado_id])


def test_consulta_puede_ver_documentos(client):
    empleado = EmpleadoFactory()
    documento = ServicioDocumento().adjuntar(empleado, TipoDocumento.objects.get(descripcion="CI"), pdf())
    login_como(client, Rol.CONSULTA)
    assert client.get(reverse("kardex:documento_ver", args=[documento.nro])).status_code == 200
    assert client.get(reverse("kardex:documento_reemplazar", args=[documento.nro])).status_code == 403


def test_todas_las_pantallas_se_muestran(afiliador):
    contrato = ContratoFactory()
    contrato.cargos.add(CargoFactory())
    dependiente = DependienteFactory(empleado=contrato.empleado)
    documento = ServicioDocumento().adjuntar(dependiente, TipoDocumento.objects.get(descripcion="CI"), pdf())
    ci = contrato.empleado_id
    urls = [
        reverse("kardex:empleado_nuevo"),
        reverse("kardex:ficha", args=[ci]),
        reverse("kardex:empleado_editar", args=[ci]),
        reverse("kardex:documento_adjuntar", args=[ci]),
        reverse("kardex:documento_reemplazar", args=[documento.nro]),
        reverse("kardex:contrato_editar", args=[contrato.nro]),
        reverse("kardex:contrato_retiro", args=[contrato.nro]),
        reverse("kardex:dependiente_nuevo", args=[ci]),
        reverse("kardex:dependiente_editar", args=[dependiente.ci]),
    ]
    for url in urls:
        assert afiliador.get(url).status_code == 200, url
