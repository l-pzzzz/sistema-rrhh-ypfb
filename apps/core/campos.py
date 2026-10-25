"""Campos con el tipo exacto del diseño relacional (docs/05) que Django no trae en MySQL."""

from django.db import models


class TinyIntegerField(models.SmallIntegerField):
    """TINYINT del informe (días, meses, años de antigüedad, intentos)."""

    def db_type(self, connection):
        if connection.vendor == "mysql":
            return "tinyint"
        return super().db_type(connection)


class CharFijoField(models.CharField):
    """CHAR(n) del informe (CATEGORIA.Cod, PERSONA.Sexo, EVALUACION.Trimestre)."""

    def db_type(self, connection):
        if connection.vendor == "mysql":
            return f"char({self.max_length})"
        return super().db_type(connection)
