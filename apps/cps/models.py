"""Modelo del módulo Seguro de salud CPS (docs/05): AFILIACION CPS."""

from django.db import models


class AfiliacionCPS(models.Model):
    """Afiliación y desafiliación a la CPS de cada contrato (no se eliminan registros)."""

    class Tipo(models.TextChoices):
        NUEVO = "NUEVO"
        REINGRESO = "REINGRESO"

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE"
        EN_PLAZO = "EN PLAZO"
        FUERA_DE_PLAZO = "FUERA DE PLAZO"
        DESAFILIADO = "DESAFILIADO"

    nro = models.AutoField(primary_key=True, db_column="Nro")
    contrato = models.ForeignKey("kardex.Contrato", on_delete=models.PROTECT, db_column="NroCon",
                                 related_name="afiliaciones")
    tipo = models.CharField(max_length=10, choices=Tipo.choices, db_column="Tipo")
    fecha_limite = models.DateField(db_column="FechaLimite")
    fecha_afil = models.DateField(null=True, blank=True, db_column="FechaAfil")
    matricula = models.CharField(max_length=20, null=True, blank=True, db_column="Matricula")
    fecha_lim_baja = models.DateField(null=True, blank=True, db_column="FechaLimBaja")
    fecha_desafil = models.DateField(null=True, blank=True, db_column="FechaDesafil")
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE, db_column="Estado")

    class Meta:
        db_table = "afiliacion_cps"
        constraints = [models.UniqueConstraint(fields=["contrato"], name="afiliacion_cps_contrato_uniq")]

    def __str__(self):
        return f"Afiliación {self.nro} ({self.estado})"
