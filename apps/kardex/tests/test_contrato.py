"""CU-02.1, CU-02.2 y CU-02.3: registrar, actualizar y corregir contratos (RF-02, RF-03; CO-01)."""

import datetime
import json
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.administracion.models import Bitacora
from apps.core.tests.fabricas import CargoFactory, ContratoFactory, EmpleadoFactory, gestion
from apps.kardex.models import AjusteSalarial, Categoria, Contrato, ContratoCargo, Empleado
from apps.kardex.services import ServicioContrato

pytestmark = pytest.mark.django_db

HOY = datetime.date(2026, 10, 23)


def registrar(empleado, cargos, inicio=datetime.date(2026, 10, 1), fin=None):
    return ServicioContrato().registrar(empleado, inicio, fin, cargos, hoy=HOY)


def test_co01_segundo_contrato_vigente_rechazado():
    """CO-01: un empleado no puede tener dos contratos vigentes."""
    empleado = EmpleadoFactory()
    registrar(empleado, [CargoFactory()])
    with pytest.raises(ValidationError, match="un empleado no puede tener dos contratos vigentes"):
        registrar(empleado, [CargoFactory()])
    assert Contrato.objects.filter(empleado=empleado, estado=Contrato.Estado.VIGENTE).count() == 1


def test_contrato_con_dos_cargos_guarda_dos_contrato_cargo():
    """RF-02: al crear un contrato con dos cargos, se guardan dos registros en CONTRATO CARGO."""
    contrato = registrar(EmpleadoFactory(), [CargoFactory(), CargoFactory()])
    assert ContratoCargo.objects.filter(contrato=contrato).count() == 2
    assert contrato.estado == Contrato.Estado.VIGENTE


def test_contrato_sin_cargo_rechazado():
    with pytest.raises(ValidationError, match="al menos un cargo"):
        registrar(EmpleadoFactory(), [])
    assert not Contrato.objects.exists()


@pytest.mark.parametrize("fin", [datetime.date(2026, 10, 1), datetime.date(2026, 9, 30)])
def test_fecha_fin_debe_ser_posterior_al_inicio(fin):
    with pytest.raises(ValidationError, match="posterior a la fecha de inicio"):
        registrar(EmpleadoFactory(), [CargoFactory()], fin=fin)


def test_contrato_indefinido_sin_fecha_fin():
    contrato = registrar(EmpleadoFactory(), [CargoFactory()])
    assert contrato.fecha_fin is None


def test_categoria_asignada_por_antiguedad_desde_fecha_ingreso():
    """CU-02.2: con 16 años cumplidos desde EMPLEADO.FechaIngreso, la categoría es C."""
    empleado = EmpleadoFactory(fecha_ingreso=datetime.date(2010, 10, 23))
    assert registrar(empleado, [CargoFactory()]).categoria_id == "C"


def test_registro_queda_en_bitacora():
    contrato = registrar(EmpleadoFactory(), [CargoFactory()])
    b = Bitacora.objects.get(operacion=Bitacora.Operacion.ALTA, tabla="contrato")
    assert json.loads(b.valor_nuevo)["nro"] == contrato.nro


def test_reingreso_vuelve_activo_al_empleado():
    """Decisión C1 (docs/06): un contrato nuevo de un empleado RETIRADO lo vuelve ACTIVO."""
    empleado = EmpleadoFactory(estado=Empleado.Estado.RETIRADO)
    ContratoFactory(empleado=empleado, estado=Contrato.Estado.CONCLUIDO, fecha_retiro=datetime.date(2026, 3, 1))
    registrar(empleado, [CargoFactory()])
    empleado.refresh_from_db()
    assert empleado.estado == Empleado.Estado.ACTIVO
    assert Bitacora.objects.filter(operacion=Bitacora.Operacion.ALTA, tabla="empleado").exists()


def test_haber_basico_de_la_categoria():
    AjusteSalarial.objects.create(
        categoria=Categoria.objects.get(cod="B"), gestion=gestion(), haber_basico=Decimal("4500.00")
    )
    assert ServicioContrato().haber_basico("B", 2026) == Decimal("4500.00")
    assert ServicioContrato().haber_basico("A", 2026) is None


def test_actualizar_cargo_queda_en_bitacora_con_valor_anterior_y_nuevo():
    """RF-02, regla 4: cambio de cargo con motivo; la bitácora guarda el valor anterior y el nuevo."""
    anterior, nuevo = CargoFactory(nombre="Operador"), CargoFactory(nombre="Supervisor")
    contrato = registrar(EmpleadoFactory(), [anterior])
    ServicioContrato().modificar(
        contrato, {"fecha_inicio": contrato.fecha_inicio, "fecha_fin": None}, [nuevo],
        Bitacora.Operacion.ACTUALIZACION, "Ascenso",
    )
    assert list(contrato.cargos.all()) == [nuevo]
    b = Bitacora.objects.get(operacion=Bitacora.Operacion.ACTUALIZACION, tabla="contrato")
    assert b.motivo == "Ascenso"
    assert json.loads(b.valor_ant) == {"cargos": ["Operador"]}
    assert json.loads(b.valor_nuevo) == {"cargos": ["Supervisor"]}


def test_corregir_fechas_queda_como_correccion():
    contrato = registrar(EmpleadoFactory(), [CargoFactory()])
    ServicioContrato().modificar(
        contrato, {"fecha_inicio": datetime.date(2026, 10, 2), "fecha_fin": datetime.date(2027, 10, 1)},
        list(contrato.cargos.all()), Bitacora.Operacion.CORRECCION, "Error de digitación",
    )
    contrato.refresh_from_db()
    assert contrato.fecha_inicio == datetime.date(2026, 10, 2)
    b = Bitacora.objects.get(operacion=Bitacora.Operacion.CORRECCION)
    assert json.loads(b.valor_ant) == {"fecha_inicio": "2026-10-01", "fecha_fin": None}


def test_modificar_contrato_exige_motivo():
    contrato = registrar(EmpleadoFactory(), [CargoFactory()])
    with pytest.raises(ValidationError, match="motivo"):
        ServicioContrato().modificar(
            contrato, {"fecha_inicio": contrato.fecha_inicio, "fecha_fin": datetime.date(2027, 1, 1)},
            list(contrato.cargos.all()), Bitacora.Operacion.ACTUALIZACION, "  ",
        )


def test_modificar_contrato_valida_fechas_y_cargos():
    contrato = registrar(EmpleadoFactory(), [CargoFactory()])
    with pytest.raises(ValidationError, match="al menos un cargo"):
        ServicioContrato().modificar(
            contrato, {"fecha_inicio": contrato.fecha_inicio, "fecha_fin": None}, [],
            Bitacora.Operacion.ACTUALIZACION, "Cambio",
        )
    with pytest.raises(ValidationError, match="posterior"):
        ServicioContrato().modificar(
            contrato, {"fecha_inicio": contrato.fecha_inicio, "fecha_fin": contrato.fecha_inicio},
            list(contrato.cargos.all()), Bitacora.Operacion.ACTUALIZACION, "Cambio",
        )


def test_modificar_sin_cambios_rechazado():
    contrato = registrar(EmpleadoFactory(), [CargoFactory()])
    with pytest.raises(ValidationError, match="ningún cambio"):
        ServicioContrato().modificar(
            contrato, {"fecha_inicio": contrato.fecha_inicio, "fecha_fin": None},
            list(contrato.cargos.all()), Bitacora.Operacion.ACTUALIZACION, "Nada",
        )


def test_contrato_concluido_no_se_modifica():
    contrato = ContratoFactory(estado=Contrato.Estado.CONCLUIDO, fecha_retiro=datetime.date(2026, 3, 1))
    with pytest.raises(ValidationError, match="vigente"):
        ServicioContrato().modificar(
            contrato, {"fecha_inicio": contrato.fecha_inicio, "fecha_fin": None}, [CargoFactory()],
            Bitacora.Operacion.CORRECCION, "Error",
        )
