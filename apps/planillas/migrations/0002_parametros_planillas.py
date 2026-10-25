"""Datos iniciales: los 5 parámetros de planillas de la gestión 2026 (docs/04; RF-22, RNF-19).

Es el único lugar de planillas donde se escriben los valores del caso: el código siempre los lee de
PARAMETRO con ``apps.core.parametros``.
"""

from decimal import Decimal

from django.db import migrations

GESTION = 2026

PARAMETROS = [
    ("UMBRAL_RCIVA", "2.00", 'Caso de estudio ("no aplica si no supera dos salarios mínimos").'),
    ("MNI_RCIVA", "2.00", "Caso de estudio y SIN: se resta del total ganado neto de AFP."),
    ("PORC_ANTICIPO", "50.00", "Caso de estudio."),
    ("DIA_ANTICIPO", "15.00", 'Caso de estudio ("después del día 15").'),
    ("DIA_F110", "15.00", "Caso de estudio."),
]


def cargar(apps, schema_editor):
    Parametro = apps.get_model("administracion", "Parametro")
    for clave, valor, fuente in PARAMETROS:
        Parametro.objects.get_or_create(
            gestion_id=GESTION, clave=clave, defaults={"valor": Decimal(valor), "fuente": fuente}
        )


class Migration(migrations.Migration):
    dependencies = [
        ("administracion", "0003_datos_iniciales"),
        ("planillas", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(cargar, migrations.RunPython.noop),
    ]
