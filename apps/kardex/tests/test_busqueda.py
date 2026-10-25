"""CU-01.1 Buscar empleado por CI, código o nombre (RF-29)."""

import datetime

import pytest

from apps.core.tests.fabricas import CargoFactory, ContratoFactory, EmpleadoFactory, UbicacionFactory
from apps.kardex.models import Categoria, Contrato, Empleado
from apps.kardex.services import buscar_empleados

pytestmark = pytest.mark.django_db


def cis(resultado):
    return {e.ci for e in resultado}


def test_perez_encuentra_perez_con_tilde():
    """RF-29: al escribir "perez", el sistema lista también a los empleados de apellido "Pérez"."""
    con_tilde = EmpleadoFactory(apellidos="Pérez Mamani")
    sin_tilde = EmpleadoFactory(apellidos="PEREZ")
    EmpleadoFactory(apellidos="Rojas")
    assert cis(buscar_empleados("perez")) == {con_tilde.ci, sin_tilde.ci}


def test_nombre_completo_y_parcial():
    empleado = EmpleadoFactory(nombres="José Luis", apellidos="Quispe")
    EmpleadoFactory(nombres="Ana", apellidos="Rojas")
    assert cis(buscar_empleados("jose luis quispe")) == {empleado.ci}
    assert cis(buscar_empleados("quispe jose")) == {empleado.ci}
    assert cis(buscar_empleados("qui")) == {empleado.ci}


def test_por_ci_y_por_codigo():
    empleado = EmpleadoFactory(ci="4455667-1B", codigo="EMP-0777")
    EmpleadoFactory()
    assert cis(buscar_empleados("4455667")) == {empleado.ci}
    assert cis(buscar_empleados("emp-0777")) == {empleado.ci}


def test_resultado_resumido_con_cargo_del_contrato_vigente():
    """RF-29, regla 2: lista resumida (CI, nombre, cargo y estado)."""
    empleado = EmpleadoFactory()
    contrato = ContratoFactory(empleado=empleado)
    contrato.cargos.add(CargoFactory(nombre="Perforador"))
    (resultado,) = buscar_empleados(empleado.ci)
    assert resultado.cargos == ["Perforador"]
    assert resultado.estado == Empleado.Estado.ACTIVO


def test_filtros_departamento_categoria_estado():
    santa_cruz = UbicacionFactory(departamento="Santa Cruz")
    en_sc = ContratoFactory(categoria=Categoria.objects.get(cod="B"))
    en_sc.cargos.add(CargoFactory(ubicacion=santa_cruz))
    otro = ContratoFactory()
    otro.cargos.add(CargoFactory())
    retirado = EmpleadoFactory(estado=Empleado.Estado.RETIRADO)
    ContratoFactory(
        empleado=retirado, estado=Contrato.Estado.CONCLUIDO, fecha_retiro=datetime.date(2026, 3, 2)
    ).cargos.add(CargoFactory(ubicacion=santa_cruz))

    assert cis(buscar_empleados("", departamento=santa_cruz)) == {en_sc.empleado_id}
    assert cis(buscar_empleados("", categoria="B")) == {en_sc.empleado_id}
    assert cis(buscar_empleados("", estado=Empleado.Estado.RETIRADO)) == {retirado.ci}
    assert len(buscar_empleados("")) == 3
