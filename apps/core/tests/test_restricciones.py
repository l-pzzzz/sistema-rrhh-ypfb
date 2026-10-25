"""Restricciones UNIQUE y CHECK de docs/05 (Meta.constraints) aplicadas por MySQL."""

import datetime
from decimal import Decimal

import pytest
from django.apps import apps
from django.db import IntegrityError, transaction
from django.db.models import CheckConstraint, UniqueConstraint

from apps.administracion.models import Usuario
from apps.kardex.models import Categoria, Contrato, Dependiente, Persona
from apps.planillas.models import Anticipo, BoletaPago, Marcacion, Planilla
from apps.vacaciones.models import EntregaLactancia, SolicitudVacacion

from .fabricas import ContratoFactory, DependienteFactory, PersonaFactory, UsuarioFactory, gestion

# (modelo, campos) de cada UNIQUE indicado en docs/05.
UNICAS = [
    ("kardex.Empleado", {"codigo"}),
    ("kardex.AjusteSalarial", {"categoria", "gestion"}),
    ("cps.AfiliacionCPS", {"contrato"}),
    ("planillas.Planilla", {"gestion", "mes"}),
    ("planillas.BoletaPago", {"planilla", "contrato"}),
    ("planillas.FormularioF110", {"contrato", "anio", "mes"}),
    ("planillas.Marcacion", {"contrato", "anio", "mes"}),
    ("vacaciones.EntregaLactancia", {"hijo", "nro_entrega"}),
    ("finiquitos.Finiquito", {"contrato"}),
    ("finiquitos.Evaluacion", {"contrato", "trimestre"}),
    ("administracion.Feriado", {"fecha", "alcance", "ubicacion"}),
]

# Modelos con al menos una CHECK según docs/05.
CON_CHECK = [
    "kardex.Persona",
    "kardex.Dependiente",
    "kardex.Categoria",
    "kardex.Contrato",
    "planillas.Planilla",
    "planillas.BoletaPago",
    "planillas.Anticipo",
    "planillas.Marcacion",
    "vacaciones.SolicitudVacacion",
    "vacaciones.EntregaLactancia",
    "finiquitos.Evaluacion",
    "administracion.Usuario",
]


@pytest.mark.parametrize(("modelo", "campos"), UNICAS)
def test_unique_declarada(modelo, campos):
    restricciones = apps.get_model(modelo)._meta.constraints
    assert any(
        isinstance(r, UniqueConstraint) and set(r.fields) == campos and r.condition is None
        for r in restricciones
    )


@pytest.mark.parametrize("modelo", CON_CHECK)
def test_check_declarada(modelo):
    assert any(isinstance(r, CheckConstraint) for r in apps.get_model(modelo)._meta.constraints)


def rechaza(fabricar):
    with pytest.raises(IntegrityError), transaction.atomic():
        fabricar()


con_bd = pytest.mark.django_db


@con_bd
def test_check_sexo():
    rechaza(lambda: PersonaFactory(sexo="X"))


@con_bd
def test_check_parentesco():
    rechaza(lambda: DependienteFactory(parentesco="PRIMO"))


@con_bd
def test_check_codigo_categoria():
    rechaza(lambda: Categoria.objects.create(cod="D", anios_min=30))


@con_bd
def test_check_fechas_contrato():
    inicio = datetime.date(2026, 3, 2)
    rechaza(lambda: ContratoFactory(fecha_inicio=inicio, fecha_fin=inicio))
    rechaza(lambda: ContratoFactory(fecha_inicio=inicio, fecha_retiro=inicio - datetime.timedelta(days=1)))
    contrato = ContratoFactory(fecha_inicio=inicio, fecha_fin=None, fecha_retiro=inicio)
    assert contrato.fecha_retiro == inicio


@con_bd
def test_check_mes_planilla():
    rechaza(lambda: Planilla.objects.create(gestion=gestion(), mes=13, estado=Planilla.Estado.PREPLANILLA))
    rechaza(lambda: Planilla.objects.create(gestion=gestion(), mes=0, estado=Planilla.Estado.PREPLANILLA))


@con_bd
def test_check_dias_trabajados():
    contrato = ContratoFactory()
    planilla = Planilla.objects.create(gestion=gestion(), mes=1, estado=Planilla.Estado.PREPLANILLA)
    importes = {"tot_ingresos": Decimal("0"), "tot_descuentos": Decimal("0"), "liquido": Decimal("0")}
    rechaza(lambda: BoletaPago.objects.create(planilla=planilla, contrato=contrato, dias_trab=31, **importes))
    rechaza(lambda: Marcacion.objects.create(contrato=contrato, anio=2026, mes=1, dias_trab=31))


@con_bd
def test_check_monto_anticipo():
    contrato = ContratoFactory()
    rechaza(lambda: Anticipo.objects.create(contrato=contrato, fecha=datetime.date(2026, 1, 20), monto=Decimal("0")))


@con_bd
def test_check_fechas_solicitud_vacacion():
    contrato = ContratoFactory()
    dia = datetime.date(2026, 5, 11)
    rechaza(
        lambda: SolicitudVacacion.objects.create(
            contrato=contrato,
            tipo=SolicitudVacacion.Tipo.VACACION,
            fecha_sol=dia,
            fecha_firma=dia,
            fecha_desde=dia,
            fecha_hasta=dia - datetime.timedelta(days=1),
            dias=Decimal("1.0"),
        )
    )


@con_bd
def test_check_numero_entrega_lactancia():
    contrato = ContratoFactory()
    madre = DependienteFactory(empleado=contrato.empleado, parentesco=Dependiente.Parentesco.CONYUGE,
                               sexo=Persona.Sexo.FEMENINO)
    hijo = DependienteFactory(empleado=contrato.empleado, parentesco=Dependiente.Parentesco.HIJO)
    rechaza(
        lambda: EntregaLactancia.objects.create(
            contrato=contrato, beneficiaria=madre, hijo=hijo, fecha=datetime.date(2026, 2, 1), nro_entrega=13
        )
    )


@con_bd
def test_check_valor_evaluacion():
    from apps.finiquitos.models import Evaluacion

    contrato = ContratoFactory()
    evaluador = UsuarioFactory()
    rechaza(
        lambda: Evaluacion.objects.create(
            contrato=contrato, trimestre="2026-T1", fecha=datetime.date(2026, 3, 31), valor=6, evaluador=evaluador
        )
    )


@con_bd
def test_check_intentos_usuario():
    usuario = UsuarioFactory()
    rechaza(lambda: Usuario.objects.filter(pk=usuario.pk).update(intentos=4))


@con_bd
def test_unique_bd_planilla_por_mes():
    Planilla.objects.create(gestion=gestion(), mes=1, estado=Planilla.Estado.PREPLANILLA)
    rechaza(lambda: Planilla.objects.create(gestion=gestion(), mes=1, estado=Planilla.Estado.PREPLANILLA))


@con_bd
def test_persona_puede_ser_empleado_y_dependiente():
    """Herencia multitabla: la madre empleada puede ser también dependiente de su cónyuge (RF-05)."""
    contrato = ContratoFactory()
    madre = ContratoFactory().empleado
    Dependiente.crear_desde_persona(madre, empleado=contrato.empleado, parentesco=Dependiente.Parentesco.CONYUGE)
    assert Persona.objects.filter(ci=madre.ci).count() == 1
    assert Dependiente.objects.get(pk=madre.ci).empleado == contrato.empleado
    assert Contrato.objects.filter(empleado=madre).exists()
