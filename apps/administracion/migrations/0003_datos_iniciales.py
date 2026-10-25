"""Datos iniciales: roles con su nivel (RNF-07) y gestión 2026 con los parámetros del caso (docs/04).

Es el único lugar donde se escriben los valores del caso: el sistema siempre los lee de PARAMETRO.
El haber básico por categoría (AJUSTE SALARIAL) lo registra el Administrador (CU-13.3).
"""

from decimal import Decimal

from django.db import migrations

ROLES = [
    ("Afiliador", "OPERADOR"),
    ("Encargado de Pagos", "OPERADOR"),
    ("Responsable de Vacaciones y Lactancias", "OPERADOR"),
    ("Administrador del Sistema", "ADMINISTRADOR"),
    ("Consulta", "CONSULTA"),
]

GESTION = 2026

PARAMETROS = [
    ("SMN", "1656.00", "Caso de estudio. Vigente: Bs 3.300 desde el 01/01/2026 (DS 5516)."),
    ("PORC_AFP", "12.21", "Caso de estudio. Vigente: 12,71 % del total ganado (Gestora Pública)."),
    ("UMBRAL_AFP", "2.00", "Caso de estudio. Vigente: 0 (sin umbral)."),
    ("PORC_IVA", "13.00", "Caso de estudio y SIN."),
    ("PLAZO_AFIL", "6.00", 'Caso ("seis días de trabajo"). DL 13214, Art. 6: 5 días hábiles.'),
    ("PLAZO_BAJA", "5.00", 'DL 13214, Art. 8 (el caso solo indica "cuanto antes").'),
    ("EDAD_MAX_HIJO", "25.00", "Propuesta del equipo; a confirmar con la CPS."),
    ("DIAS_LAB", "5.00", "Lunes a viernes; ajustable según el régimen de cada área."),
    ("VALOR_LACT", "1.00", "Múltiplos del SMN (1 = 1 SMN). Subsidio en especie durante 12 meses."),
    ("PLAZO_FINIQ", "15.00", "Normativa laboral; a confirmar si son días hábiles o calendario."),
    ("ANTIG_MIN_INDEM", "90.00", "DS 110, Art. 2: más de 90 días de trabajo continuo."),
]


def cargar(apps, schema_editor):
    Rol = apps.get_model("administracion", "Rol")
    GestionSalarial = apps.get_model("administracion", "GestionSalarial")
    Parametro = apps.get_model("administracion", "Parametro")

    for nombre, nivel in ROLES:
        Rol.objects.get_or_create(nombre=nombre, defaults={"nivel": nivel})
    gestion, _ = GestionSalarial.objects.get_or_create(anio=GESTION, defaults={"estado": "ABIERTA"})
    for clave, valor, fuente in PARAMETROS:
        Parametro.objects.get_or_create(
            gestion=gestion, clave=clave, defaults={"valor": Decimal(valor), "fuente": fuente}
        )


class Migration(migrations.Migration):
    dependencies = [
        ("administracion", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(cargar, migrations.RunPython.noop),
    ]
