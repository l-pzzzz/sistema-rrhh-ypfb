"""Modelos del módulo Finiquitos y evaluaciones (docs/05): FINIQUITO, DETALLE FINIQUITO y EVALUACION."""

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.campos import CharFijoField, TinyIntegerField


class Finiquito(models.Model):
    """Liquidación de un contrato concluido (patrón Strategy según el tipo de retiro)."""

    class Estado(models.TextChoices):
        CALCULADO = "CALCULADO"
        APROBADO = "APROBADO"
        PAGADO = "PAGADO"

    nro = models.AutoField(primary_key=True, db_column="Nro")
    contrato = models.ForeignKey("kardex.Contrato", on_delete=models.PROTECT, db_column="NroCon",
                                 related_name="finiquitos")
    fecha_calc = models.DateField("fecha de cálculo", db_column="FechaCalc")
    total = models.DecimalField(max_digits=10, decimal_places=2, db_column="Total")
    fecha_lim_pago = models.DateField("fecha límite de pago", db_column="FechaLimPago")
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.CALCULADO, db_column="Estado")

    class Meta:
        db_table = "finiquito"
        constraints = [models.UniqueConstraint(fields=["contrato"], name="finiquito_contrato_uniq")]

    def __str__(self):
        return f"Finiquito {self.nro} ({self.estado})"


class DetalleFiniquito(models.Model):
    """Conceptos del finiquito con su importe (negativo si es descuento)."""

    class Concepto(models.TextChoices):
        INDEMNIZACION = "INDEMNIZACION", "Indemnización"
        DESAHUCIO = "DESAHUCIO", "Desahucio"
        VACACIONES = "VACACIONES", "Vacaciones"
        AGUINALDO = "AGUINALDO", "Aguinaldo"
        DEVENGADOS = "DEVENGADOS", "Devengados"
        DESC_LICENCIAS = "DESC. LICENCIAS", "Descuento de licencias"

    pk = models.CompositePrimaryKey("finiquito", "concepto")
    finiquito = models.ForeignKey(Finiquito, on_delete=models.CASCADE, db_column="NroFin", related_name="detalles")
    concepto = models.CharField(max_length=25, choices=Concepto.choices, db_column="Concepto")
    monto = models.DecimalField(max_digits=10, decimal_places=2, db_column="Monto")

    class Meta:
        db_table = "detalle_finiquito"

    def __str__(self):
        return f"{self.concepto}: {self.monto}"


class Evaluacion(models.Model):
    """Evaluación trimestral de desempeño (RF-21)."""

    class Accion(models.TextChoices):
        RETIRO = "RETIRO", "Retiro"
        LLAMADA_DE_ATENCION = "LLAMADA DE ATENCION", "Llamada de atención"
        VALE = "VALE", "Vale"

    nro = models.AutoField(primary_key=True, db_column="Nro")
    contrato = models.ForeignKey("kardex.Contrato", on_delete=models.PROTECT, db_column="NroCon",
                                 related_name="evaluaciones")
    trimestre = CharFijoField(max_length=7, help_text="AAAA-T#", db_column="Trimestre")
    fecha = models.DateField(db_column="Fecha")
    valor = TinyIntegerField(db_column="Valor")
    evaluador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, db_column="Evaluador",
                                  related_name="evaluaciones_registradas")
    accion_prop = models.CharField("acción propuesta", max_length=30, choices=Accion.choices, null=True, blank=True,
                                   db_column="AccionProp")
    decision = models.CharField("decisión", max_length=30, null=True, blank=True, db_column="Decision")

    class Meta:
        db_table = "evaluacion"
        constraints = [
            models.UniqueConstraint(fields=["contrato", "trimestre"], name="evaluacion_con_trimestre_uniq"),
            models.CheckConstraint(condition=Q(valor__gte=1, valor__lte=5), name="evaluacion_valor_check"),
        ]

    def __str__(self):
        return f"Evaluación {self.trimestre}: {self.valor}"
