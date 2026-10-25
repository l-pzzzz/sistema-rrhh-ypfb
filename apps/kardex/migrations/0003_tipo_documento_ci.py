"""Tipos de documento CI (fotocopia obligatoria del dependiente, RF-05) y TITULO y CERTIFICADO (datos
académicos del RF-01 como documentos, RF-04). Decisiones de C1 en docs/06."""

from django.db import migrations


TIPOS = ["CI", "TITULO", "CERTIFICADO"]


def cargar(apps, schema_editor):
    TipoDocumento = apps.get_model("kardex", "TipoDocumento")
    for descripcion in TIPOS:
        TipoDocumento.objects.get_or_create(descripcion=descripcion)


class Migration(migrations.Migration):
    dependencies = [
        ("kardex", "0002_categorias"),
    ]

    operations = [
        migrations.RunPython(cargar, migrations.RunPython.noop),
    ]
