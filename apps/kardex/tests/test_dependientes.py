"""CU-03 Gestionar dependientes (RF-04, RF-05)."""

import datetime
import json

import pytest
from django.apps import apps
from django.core.exceptions import ValidationError

from apps.administracion.models import Bitacora
from apps.core.tests.fabricas import ContratoFactory, DependienteFactory, EmpleadoFactory
from apps.kardex.models import Dependiente, Documento, Persona
from apps.kardex.services import AVISO_SIN_AFILIACION, ServicioDependiente

from .archivos import MB, pdf

pytestmark = pytest.mark.django_db

HOY = datetime.date(2026, 10, 23)


def datos(**cambios):
    base = {
        "ci": "8888888",
        "nombres": "Lucía",
        "apellidos": "Mamani",
        "fecha_nac": datetime.date(2015, 3, 1),
        "sexo": Persona.Sexo.FEMENINO,
        "telefono": None,
    }
    return base | cambios


def registrar(empleado, parentesco=Dependiente.Parentesco.HIJO, fotocopia="nueva", **cambios):
    archivo = pdf("ci.pdf") if fotocopia == "nueva" else fotocopia
    return ServicioDependiente().registrar(empleado, datos(**cambios), parentesco, archivo, hoy=HOY)


def afiliar(contrato, estado):
    AfiliacionCPS = apps.get_model("cps", "AfiliacionCPS")
    return AfiliacionCPS.objects.create(
        contrato=contrato, tipo=AfiliacionCPS.Tipo.NUEVO, fecha_limite=HOY, estado=estado
    )


def test_registrar_con_fotocopia_del_ci(tipo_ci):
    empleado = EmpleadoFactory()
    dependiente, _ = registrar(empleado)
    assert dependiente.empleado == empleado
    documento = Documento.objects.get(persona_id=dependiente.ci)
    assert documento.tipo == tipo_ci and documento.vigente
    assert Bitacora.objects.filter(operacion=Bitacora.Operacion.ALTA, tabla="dependiente").exists()
    # RF-05, regla 5: los dependientes se listan en la ficha del empleado.
    assert list(empleado.dependientes.all()) == [dependiente]


def test_fotocopia_del_ci_obligatoria():
    """RF-05, regla 2."""
    with pytest.raises(ValidationError, match="La fotocopia del CI es obligatoria"):
        registrar(EmpleadoFactory(), fotocopia=None)
    assert not Dependiente.objects.exists()


def test_fotocopia_valida_tamanio():
    with pytest.raises(ValidationError, match="5 MB"):
        registrar(EmpleadoFactory(), fotocopia=pdf(tamanio=6 * MB))
    assert not Persona.objects.filter(ci="8888888").exists()


def test_hijo_ya_registrado_con_su_madre_empleada():
    """RF-05: "Ya está registrado como dependiente de [nombre]"."""
    madre = EmpleadoFactory(nombres="María", apellidos="Rojas")
    padre = EmpleadoFactory()
    registrar(madre)
    with pytest.raises(ValidationError, match="Ya está registrado como dependiente de María Rojas"):
        registrar(padre)
    assert Dependiente.objects.get(pk="8888888").empleado == madre


def test_empleada_como_conyuge_de_otro_empleado():
    esposa = EmpleadoFactory(ci="7777777", nombres="Rosa")
    esposo = EmpleadoFactory()
    dependiente, _ = registrar(esposo, Dependiente.Parentesco.CONYUGE, ci="7777777")
    assert dependiente.empleado == esposo
    assert dependiente.nombres == "Rosa"  # No se sobrescriben los datos de la persona.
    assert Persona.objects.filter(ci="7777777").count() == 1
    assert esposa.contratos.count() == 0


def test_no_es_dependiente_de_si_mismo():
    empleado = EmpleadoFactory(ci="6666666")
    with pytest.raises(ValidationError, match="de sí mismo"):
        registrar(empleado, ci="6666666")


def test_advertencia_hijo_supera_edad_maxima():
    """RF-05, regla 4: con EDAD_MAX_HIJO = 25, un hijo de 26 años registra con advertencia."""
    _, avisos = registrar(EmpleadoFactory(), fecha_nac=datetime.date(2000, 1, 1))
    assert "El hijo o hija supera la edad máxima de beneficiario (25 años)." in avisos
    assert Dependiente.objects.filter(pk="8888888").exists()


def test_sin_advertencia_de_edad():
    _, avisos = registrar(EmpleadoFactory(), fecha_nac=datetime.date(2001, 10, 23))  # 25 años cumplidos
    assert not any("edad" in a for a in avisos)
    _, avisos = registrar(
        EmpleadoFactory(), Dependiente.Parentesco.PADRE, ci="9999999", fecha_nac=datetime.date(1950, 1, 1)
    )
    assert not any("edad" in a for a in avisos)


def test_aviso_trabajador_sin_afiliacion_cps():
    """Decisión C1: no se bloquea, pero se avisa si el contrato vigente no está afiliado."""
    contrato = ContratoFactory()
    _, avisos = registrar(contrato.empleado)
    assert AVISO_SIN_AFILIACION in avisos
    assert AVISO_SIN_AFILIACION == "El trabajador aún no está afiliado a la CPS"


@pytest.mark.parametrize("estado", ["PENDIENTE", "DESAFILIADO"])
def test_aviso_con_afiliacion_no_vigente(estado):
    contrato = ContratoFactory()
    afiliar(contrato, estado)
    _, avisos = registrar(contrato.empleado)
    assert AVISO_SIN_AFILIACION in avisos


@pytest.mark.parametrize("estado", ["EN PLAZO", "FUERA DE PLAZO"])
def test_sin_aviso_si_esta_afiliado(estado):
    contrato = ContratoFactory()
    afiliar(contrato, estado)
    _, avisos = registrar(contrato.empleado)
    assert AVISO_SIN_AFILIACION not in avisos


def test_corregir_dependiente_en_bitacora():
    dependiente = DependienteFactory(apellidos="Mamni")
    ServicioDependiente().modificar(
        dependiente, {"apellidos": "Mamani", "parentesco": dependiente.parentesco},
        Bitacora.Operacion.CORRECCION, "Error de digitación", hoy=HOY,
    )
    dependiente.refresh_from_db()
    assert dependiente.apellidos == "Mamani"
    b = Bitacora.objects.get(operacion=Bitacora.Operacion.CORRECCION, tabla="dependiente")
    assert json.loads(b.valor_ant) == {"apellidos": "Mamni"}


def test_actualizar_parentesco_exige_motivo():
    dependiente = DependienteFactory(parentesco=Dependiente.Parentesco.CONVIVIENTE)
    with pytest.raises(ValidationError, match="motivo"):
        ServicioDependiente().modificar(
            dependiente, {"parentesco": Dependiente.Parentesco.CONYUGE}, Bitacora.Operacion.ACTUALIZACION, "", hoy=HOY
        )


def test_modificar_devuelve_advertencia_de_edad():
    dependiente = DependienteFactory(fecha_nac=datetime.date(2010, 1, 1))
    avisos = ServicioDependiente().modificar(
        dependiente, {"fecha_nac": datetime.date(1999, 1, 1)}, Bitacora.Operacion.CORRECCION, "Fecha errada", hoy=HOY
    )
    assert any("edad máxima" in a for a in avisos)
