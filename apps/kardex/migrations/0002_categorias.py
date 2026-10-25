"""Categorías por antigüedad en años cumplidos: A de 0 a 5, B de 6 a 15 y C de 16 en adelante (RF-03)."""

from django.db import migrations

CATEGORIAS = [("A", 0, 5), ("B", 6, 15), ("C", 16, None)]


def cargar(apps, schema_editor):
    Categoria = apps.get_model("kardex", "Categoria")
    for cod, minimo, maximo in CATEGORIAS:
        Categoria.objects.get_or_create(cod=cod, defaults={"anios_min": minimo, "anios_max": maximo})


class Migration(migrations.Migration):
    dependencies = [
        ("kardex", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(cargar, migrations.RunPython.noop),
    ]
