"""Carga datos de demostración para la defensa (solo desarrollo; orca/99_integracion.md, paso 6).

Uso: ``python manage.py cargar_datos_demo``. Es idempotente y se niega a correr con DEBUG = False.
Todo se registra con los servicios de cada módulo (Kardex, CPS y Planillas) para que se disparen las
señales del contrato y la bitácora. Los valores de ejemplo (haberes, personas) no son datos reales.
"""

import datetime
import secrets
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.administracion.models import Bitacora, Feriado, GestionSalarial, Rol, Usuario
from apps.core import auditoria
from apps.cps import services as cps
from apps.cps.models import AfiliacionCPS
from apps.kardex.models import (
    AjusteSalarial,
    Cargo,
    Categoria,
    Contrato,
    Empleado,
    Funcion,
    TipoDocumento,
    Ubicacion,
)
from apps.kardex.services import ServicioContrato, ServicioEmpleado
from apps.planillas.models import Anticipo, FormularioF110
from apps.planillas.services import ServicioAnticipos, ServicioF110

GESTION = 2026
MES_DEMO = 10  # mes de la planilla de la demostración (docs/demo/marcaciones_ejemplo.csv)

DEPARTAMENTOS = ["La Paz", "Cochabamba", "Santa Cruz", "Oruro", "Potosí", "Tarija", "Chuquisaca", "Beni", "Pando"]

# (cargo, departamento, funciones)
CARGOS = [
    ("Operador de planta", "Santa Cruz", ["Operar los equipos de la planta", "Registrar las lecturas de producción"]),
    ("Técnico de mantenimiento", "Tarija", ["Mantener los equipos de campo", "Atender las órdenes de trabajo"]),
    ("Analista de recursos humanos", "La Paz", ["Mantener el Kardex del personal", "Preparar las planillas"]),
    ("Asistente administrativo", "Cochabamba", ["Atender la correspondencia", "Archivar la documentación"]),
    ("Ingeniero de campo", "Santa Cruz", ["Supervisar las operaciones de campo", "Elaborar informes técnicos"]),
    ("Auxiliar de almacén", "Oruro", ["Recibir y despachar materiales", "Llevar el inventario"]),
]

TIPOS_DOCUMENTO = ["CI", "TITULO", "CERTIFICADO"]

# Haber básico 2026 de ejemplo por categoría (no son los haberes reales de la empresa).
HABERES = {"A": Decimal("3500.00"), "B": Decimal("4200.00"), "C": Decimal("5000.00")}

# Feriados nacionales de Bolivia 2026 (el Administrador los confirma en CU-13).
FERIADOS = [
    (datetime.date(2026, 1, 1), "Año Nuevo"),
    (datetime.date(2026, 1, 22), "Día del Estado Plurinacional"),
    (datetime.date(2026, 2, 16), "Carnaval (lunes)"),
    (datetime.date(2026, 2, 17), "Carnaval (martes)"),
    (datetime.date(2026, 4, 3), "Viernes Santo"),
    (datetime.date(2026, 5, 1), "Día del Trabajo"),
    (datetime.date(2026, 6, 4), "Corpus Christi"),
    (datetime.date(2026, 6, 21), "Año Nuevo Andino Amazónico"),
    (datetime.date(2026, 8, 6), "Día de la Patria"),
    (datetime.date(2026, 11, 2), "Día de Todos los Santos"),
    (datetime.date(2026, 12, 25), "Navidad"),
]

USUARIOS = [
    ("afiliador", "Afiliador"),
    ("pagos", "Encargado de Pagos"),
    ("vacaciones", "Responsable de Vacaciones y Lactancias"),
    ("admin", "Administrador del Sistema"),
    ("consulta", "Consulta"),
]

NOMBRES = ["Carlos", "María", "Luis", "Ana", "Jorge", "Rosa", "Pedro", "Elena", "Mario", "Lucía",
           "Raúl", "Carmen", "Hugo", "Sofía", "Daniel", "Paola", "Marco", "Teresa", "Iván", "Gabriela"]
APELLIDOS = ["Mamani", "Quispe", "Flores", "Rojas", "Vargas", "Condori", "Choque", "Salvatierra", "Gutiérrez", "Arce"]

CANTIDAD_EMPLEADOS = 20
CI_BASE = 9000000  # CI ficticios 9000001 … 9000020
# Antigüedad: ingresos antiguos (categorías A, B y C) y los últimos RECIENTES empleados recién contratados.
INGRESOS_ANTIGUOS = [datetime.date(2010, 3, 1), datetime.date(2014, 8, 1), datetime.date(2019, 5, 6),
                     datetime.date(2022, 2, 1), datetime.date(2025, 3, 3)]
INICIO_ANTIGUOS = datetime.date(2026, 1, 5)
INICIO_RECIENTES = datetime.date(2026, 10, 19)
RECIENTES = 5
CON_AFILIACION = 10  # los primeros empleados con la afiliación CPS ya registrada
CON_ANTICIPO = 5
CON_F110 = 8
FECHA_ANTICIPO = datetime.date(2026, MES_DEMO, 20)
FECHA_F110 = datetime.date(2026, MES_DEMO, 10)
DIAS_CON_FALTAS = {3: 28, 7: 25, 12: 29, 18: 27}


def ci_demo(n):
    return str(CI_BASE + n)


def dias_demo(n):
    """Días trabajados de ejemplo en el mes: la mayoría 30, con algunas faltas."""
    return DIAS_CON_FALTAS.get(n, 30)


class Command(BaseCommand):
    help = "Carga datos de demostración (solo desarrollo, DEBUG=True). Es idempotente."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("cargar_datos_demo solo corre en desarrollo (DEBUG=True).")
        if not GestionSalarial.objects.filter(anio=GESTION).exists():
            raise CommandError("Falta la gestión 2026: ejecute primero «manage.py migrate».")
        with transaction.atomic():
            self._catalogos()
            self._haberes()
            self._feriados()
            claves = self._usuarios()
            nuevos = self._empleados()
            self._anticipos_y_f110()
        self._resumen(claves, nuevos)

    def _catalogos(self):
        ubicaciones = {d: Ubicacion.objects.get_or_create(departamento=d)[0] for d in DEPARTAMENTOS}
        for nombre, departamento, funciones in CARGOS:
            cargo, _ = Cargo.objects.get_or_create(nombre=nombre, ubicacion=ubicaciones[departamento])
            for descripcion in funciones:
                Funcion.objects.get_or_create(cargo=cargo, descripcion=descripcion)
        for descripcion in TIPOS_DOCUMENTO:
            TipoDocumento.objects.get_or_create(descripcion=descripcion)

    def _haberes(self):
        for cod, monto in HABERES.items():
            _, creado = AjusteSalarial.objects.get_or_create(
                categoria=Categoria.objects.get(cod=cod), gestion_id=GESTION, defaults={"haber_basico": monto}
            )
            if creado:
                auditoria.registrar(
                    Bitacora.Operacion.ALTA, "ajuste_salarial",
                    valor_nuevo={"categoria": cod, "gestion": GESTION, "haber_basico": str(monto)},
                    motivo="DEMOSTRACIÓN: haber de ejemplo, no es el haber real.",
                )

    def _feriados(self):
        for fecha, descripcion in FERIADOS:
            Feriado.objects.get_or_create(
                fecha=fecha, alcance=Feriado.Alcance.NACIONAL, ubicacion=None, defaults={"descripcion": descripcion}
            )

    def _usuarios(self):
        """Crea un usuario por rol; devuelve {login: contraseña} solo de los creados ahora."""
        claves = {}
        for login, nombre_rol in USUARIOS:
            if Usuario.objects.filter(login=login).exists():
                continue
            clave = self._clave_nueva()
            usuario = Usuario.objects.create_user(login, clave, rol=Rol.objects.get(nombre=nombre_rol))
            auditoria.registrar(
                Bitacora.Operacion.ALTA, "usuario",
                valor_nuevo={"Login": usuario.login, "IdRol": usuario.rol_id, "Activo": usuario.activo},
            )
            claves[login] = clave
        return claves

    @staticmethod
    def _clave_nueva():
        while True:
            clave = f"Dm{secrets.token_urlsafe(9)}7"
            try:
                validate_password(clave)
            except ValidationError:
                continue
            return clave

    def _empleados(self):
        """Registra los empleados ficticios con contrato vigente (CU-01, CU-02) y afilia a los primeros."""
        cargos = list(Cargo.objects.order_by("id"))
        servicio_empleado, servicio_contrato = ServicioEmpleado(), ServicioContrato()
        nuevos = 0
        for n in range(1, CANTIDAD_EMPLEADOS + 1):
            ci = ci_demo(n)
            if Empleado.objects.filter(pk=ci).exists():
                continue
            reciente = n > CANTIDAD_EMPLEADOS - RECIENTES
            # Un contrato no puede iniciar en el futuro (la categoría sale de la antigüedad): se limita a hoy.
            inicio = min(INICIO_RECIENTES if reciente else INICIO_ANTIGUOS, timezone.localdate())
            ingreso = inicio if reciente else min(INGRESOS_ANTIGUOS[(n - 1) % len(INGRESOS_ANTIGUOS)], inicio)
            empleado = servicio_empleado.registrar({
                "ci": ci,
                "codigo": f"DEMO-{n:03d}",
                "nombres": NOMBRES[n - 1],
                "apellidos": f"{APELLIDOS[n % len(APELLIDOS)]} {APELLIDOS[(n * 3) % len(APELLIDOS)]}",
                "fecha_nac": datetime.date(1975 + n, 1 + n % 12, 1 + n),
                "sexo": "F" if NOMBRES[n - 1][-1] == "a" else "M",
                "fecha_ingreso": ingreso,
                "direccion": f"Calle Demo {n}",
            })
            contrato = servicio_contrato.registrar(empleado, inicio, None, [cargos[n % len(cargos)]])
            if n <= CON_AFILIACION:
                self._afiliar(contrato, n)
            nuevos += 1
        return nuevos

    @staticmethod
    def _afiliar(contrato, n):
        afil = AfiliacionCPS.objects.get(contrato=contrato)
        cps.registrar_afiliacion(afil, f"DEMO-{n:04d}", contrato.fecha_inicio + datetime.timedelta(days=1))

    def _anticipos_y_f110(self):
        vigentes = list(Contrato.objects.filter(
            estado=Contrato.Estado.VIGENTE,
            empleado_id__in=[ci_demo(n) for n in range(1, CANTIDAD_EMPLEADOS + 1)],
        ).order_by("nro"))
        for contrato in vigentes[:CON_ANTICIPO]:
            if not Anticipo.objects.filter(contrato=contrato, fecha=FECHA_ANTICIPO).exists():
                ServicioAnticipos().registrar(contrato, FECHA_ANTICIPO, Decimal("500.00"))
        for i, contrato in enumerate(vigentes[:CON_F110]):
            if not FormularioF110.objects.filter(contrato=contrato, anio=GESTION, mes=MES_DEMO).exists():
                ServicioF110().registrar(contrato, GESTION, MES_DEMO, Decimal(1000 + 250 * i), FECHA_F110)

    def _resumen(self, claves, nuevos):
        self.stdout.write(self.style.SUCCESS(f"Datos de demostración listos ({nuevos} empleados nuevos)."))
        if claves:
            self.stdout.write("Contraseñas generadas (se muestran una sola vez):")
            for login, clave in claves.items():
                self.stdout.write(f"  {login:<12} {clave}")
        else:
            self.stdout.write("Los usuarios ya existían: no se generaron contraseñas nuevas.")
