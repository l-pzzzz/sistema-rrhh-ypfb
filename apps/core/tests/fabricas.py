"""Fábricas de prueba (factory_boy) compartidas por todas las apps.

Usan la gestión 2026 y las categorías que crea la migración de datos iniciales.
"""

import datetime
import secrets

import factory

from apps.administracion.models import Feriado, GestionSalarial, Rol, Usuario
from apps.kardex.models import Cargo, Categoria, Contrato, Dependiente, Empleado, Persona, Ubicacion

# Se genera en cada ejecución: no hay contraseñas escritas en el repositorio.
CLAVE_PRUEBA = f"Pr{secrets.token_hex(8)}9"


class UbicacionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ubicacion

    departamento = factory.Sequence(lambda n: f"Departamento {n}")


class CargoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Cargo

    nombre = factory.Sequence(lambda n: f"Cargo {n}")
    ubicacion = factory.SubFactory(UbicacionFactory)


class PersonaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Persona

    ci = factory.Sequence(lambda n: f"{1000000 + n}")
    nombres = "Juan"
    apellidos = "Pérez"
    fecha_nac = datetime.date(1990, 1, 1)
    sexo = Persona.Sexo.MASCULINO


class EmpleadoFactory(PersonaFactory):
    class Meta:
        model = Empleado

    codigo = factory.Sequence(lambda n: f"EMP-{n:04d}")
    fecha_ingreso = datetime.date(2020, 1, 6)
    estado = Empleado.Estado.ACTIVO


class DependienteFactory(PersonaFactory):
    class Meta:
        model = Dependiente

    empleado = factory.SubFactory(EmpleadoFactory)
    parentesco = Dependiente.Parentesco.HIJO


class ContratoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contrato

    empleado = factory.SubFactory(EmpleadoFactory)
    categoria = factory.LazyFunction(lambda: Categoria.objects.get(cod="A"))
    fecha_inicio = datetime.date(2026, 1, 5)
    estado = Contrato.Estado.VIGENTE


def gestion(anio=2026):
    return GestionSalarial.objects.get(anio=anio)


def rol(nombre):
    return Rol.objects.get(nombre=nombre)


class UsuarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Usuario
        skip_postgeneration_save = True

    login = factory.Sequence(lambda n: f"usuario{n}")
    rol = factory.LazyFunction(lambda: Rol.objects.get(nombre="Afiliador"))
    activo = True
    intentos = 0

    @factory.post_generation
    def clave(self, create, extracted, **kwargs):
        self.set_password(extracted or CLAVE_PRUEBA)
        if create:
            self.save()


class FeriadoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Feriado

    descripcion = "Feriado"
    alcance = Feriado.Alcance.NACIONAL

