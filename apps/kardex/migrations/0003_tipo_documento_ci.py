"""Tipo de documento "CI" para la fotocopia obligatoria del dependiente (RF-05, decisión C1 en docs/06)."""

from django.db import migrations


def cargar(apps, schema_editor):
    TipoDocumento = apps.get_model("kardex", "TipoDocumento")
    TipoDocumento.objects.get_or_create(descripcion="CI")


class Migration(migrations.Migration):
    dependencies = [
        ("kardex", "0002_categorias"),
    ]

    operations = [
        migrations.RunPython(cargar, migrations.RunPython.noop),
    ]
