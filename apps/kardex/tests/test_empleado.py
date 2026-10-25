"""CU-01.2 y CU-01.3: registrar, actualizar y corregir el Kardex del empleado (RF-01)."""

import datetime
import json

import pytest
from django.core.exceptions import ValidationError

from apps.administracion.models import Bitacora
from apps.core.tests.fabricas import DependienteFactory, EmpleadoFactory
from apps.kardex.models import Dependiente, Empleado, Persona
from apps.kardex.services import ServicioEmpleado

pytestmark = pytest.mark.django_db


def datos(**cambios):
    base = {
        "ci": "1234567",
        "nombres": "Ana",
        "apellidos": "Pérez Rojas",
        "fecha_nac": datetime.date(1990, 5, 2),
        "sexo": Persona.Sexo.FEMENINO,
        "telefono": "70000000",
        "codigo": "EMP-0100",
        "fecha_ingreso": datetime.date(2026, 10, 1),
        "direccion": "Av. Busch 123",
        "nom_emerg": "Luis Pérez",
        "par_emerg": "Hermano",
        "tel_emerg": "71111111",
    }
    return base | cambios


def test_registrar_empleado_activo_en_bitacora():
    empleado = ServicioEmpleado().registrar(datos())
    assert empleado.estado == Empleado.Estado.ACTIVO
    b = Bitacora.objects.get(operacion=Bitacora.Operacion.ALTA, tabla="empleado")
    assert json.loads(b.valor_nuevo)["ci"] == "1234567"


def test_ci_repetido():
    """RF-01: al registrar un CI repetido, el sistema muestra "El CI ya está registrado"."""
    ServicioEmpleado().registrar(datos())
    with pytest.raises(ValidationError, match="El CI ya está registrado"):
        ServicioEmpleado().registrar(datos(codigo="EMP-0101"))


def test_codigo_repetido():
    ServicioEmpleado().registrar(datos())
    with pytest.raises(ValidationError, match="El código ya está registrado"):
        ServicioEmpleado().registrar(datos(ci="7654321"))


@pytest.mark.parametrize("ci", ["1234567-1A", "1234567-1a", " 1234567-1A "])
def test_ci_con_complemento(ci):
    """RF-01, regla 2: el CI acepta el complemento (1234567-1A)."""
    assert ServicioEmpleado().registrar(datos(ci=ci)).ci == "1234567-1A"


@pytest.mark.parametrize("ci", ["ABC", "12-", "1234567-1A2B", "12 34"])
def test_ci_invalido(ci):
    with pytest.raises(ValidationError, match="CI no válido"):
        ServicioEmpleado().registrar(datos(ci=ci))


def test_dependiente_contratado_se_registra_como_empleado():
    """Una persona registrada como dependiente puede ser contratada (herencia PERSONA)."""
    dependiente = DependienteFactory(ci="5555555")
    empleado = ServicioEmpleado().registrar(datos(ci="5555555", nombres="Ana"))
    assert Persona.objects.filter(ci="5555555").count() == 1
    assert Empleado.objects.get(pk="5555555").codigo == "EMP-0100"
    assert Dependiente.objects.get(pk="5555555").empleado == dependiente.empleado
    assert empleado.nombres == "Ana"


def test_editar_apellido_bitacora_con_valor_anterior_y_nuevo():
    """RF-01: al editar un apellido, la bitácora muestra el valor anterior y el nuevo."""
    empleado = EmpleadoFactory(apellidos="Perez")
    ServicioEmpleado().modificar(
        empleado, {"apellidos": "Pérez"}, Bitacora.Operacion.CORRECCION, "Faltaba la tilde"
    )
    empleado.refresh_from_db()
    assert empleado.apellidos == "Pérez"
    b = Bitacora.objects.get(operacion=Bitacora.Operacion.CORRECCION, tabla="empleado")
    assert json.loads(b.valor_ant) == {"apellidos": "Perez"}
    assert json.loads(b.valor_nuevo) == {"apellidos": "Pérez"}
    assert b.motivo == "Faltaba la tilde"


def test_actualizar_direccion():
    empleado = EmpleadoFactory(direccion="Calle 1")
    ServicioEmpleado().modificar(
        empleado, {"direccion": "Calle 2", "telefono": empleado.telefono}, Bitacora.Operacion.ACTUALIZACION, "Mudanza"
    )
    b = Bitacora.objects.get(operacion=Bitacora.Operacion.ACTUALIZACION)
    assert json.loads(b.valor_nuevo) == {"direccion": "Calle 2"}


def test_modificar_exige_motivo():
    empleado = EmpleadoFactory()
    with pytest.raises(ValidationError, match="motivo"):
        ServicioEmpleado().modificar(empleado, {"apellidos": "Otro"}, Bitacora.Operacion.ACTUALIZACION, "")
    empleado.refresh_from_db()
    assert empleado.apellidos == "Pérez"


def test_modificar_exige_actualizacion_o_correccion():
    with pytest.raises(ValidationError, match="actualización o corrección"):
        ServicioEmpleado().modificar(EmpleadoFactory(), {"apellidos": "Otro"}, Bitacora.Operacion.ALTA, "x")


def test_modificar_codigo_repetido():
    EmpleadoFactory(codigo="EMP-9999")
    empleado = EmpleadoFactory()
    with pytest.raises(ValidationError, match="El código ya está registrado"):
        ServicioEmpleado().modificar(empleado, {"codigo": "EMP-9999"}, Bitacora.Operacion.CORRECCION, "Error")


def test_ci_no_se_modifica():
    with pytest.raises(ValidationError, match="no se puede modificar"):
        ServicioEmpleado().modificar(EmpleadoFactory(), {"ci": "1"}, Bitacora.Operacion.CORRECCION, "Error")
