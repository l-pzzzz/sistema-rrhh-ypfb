"""Modelos del módulo Planillas de sueldos (docs/05): PLANILLA, BOLETA PAGO, DETALLE BOLETA, ANTICIPO,
FORMULARIO F110 y MARCACION.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.campos import TinyIntegerField


class Planilla(models.Model):
    """Planilla mensual de sueldos (12 por gestión)."""

    class Estado(models.TextChoices):
        PREPLANILLA = "PREPLANILLA"
        CERRADA = "CERRADA"

    nro = models.AutoField(primary_key=True, db_column="Nro")
    gestion = models.ForeignKey("administracion.GestionSalarial", on_delete=models.PROTECT, db_column="Año",
                                related_name="planillas")
    mes = TinyIntegerField(db_column="Mes")
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PREPLANILLA, db_column="Estado")
    fecha_cierre = models.DateField(null=True, blank=True, db_column="FechaCierre")
    aprobado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                     db_column="AprobadoPor", related_name="planillas_aprobadas")

    class Meta:
        db_table = "planilla"
        constraints = [
            models.UniqueConstraint(fields=["gestion", "mes"], name="planilla_anio_mes_uniq"),
            models.CheckConstraint(condition=Q(mes__gte=1, mes__lte=12), name="planilla_mes_check"),
        ]

    def __str__(self):
        return f"Planilla {self.mes:02d}/{self.gestion_id}"


class BoletaPago(models.Model):
    """Boleta de pago de cada trabajador en una planilla."""

    nro = models.AutoField(primary_key=True, db_column="NroB")
    planilla = models.ForeignKey(Planilla, on_delete=models.PROTECT, db_column="NroPla", related_name="boletas")
    contrato = models.ForeignKey("kardex.Contrato", on_delete=models.PROTECT, db_column="NroCon",
                                 related_name="boletas")
    dias_trab = TinyIntegerField("días trabajados", db_column="DiasTrab")
    tot_ingresos = models.DecimalField(max_digits=10, decimal_places=2, db_column="TotIngresos")
    tot_descuentos = models.DecimalField(max_digits=10, decimal_places=2, db_column="TotDescuentos")
    liquido = models.DecimalField(max_digits=10, decimal_places=2, db_column="Liquido")

    class Meta:
        db_table = "boleta_pago"
        constraints = [
            models.UniqueConstraint(fields=["planilla", "contrato"], name="boleta_pago_pla_con_uniq"),
            models.CheckConstraint(condition=Q(dias_trab__gte=0, dias_trab__lte=30), name="boleta_pago_dias_check"),
        ]

    def __str__(self):
        return f"Boleta {self.nro}"


class DetalleBoleta(models.Model):
    """Conceptos de cada boleta con la base y el porcentaje aplicados (fotografía histórica, RN-08)."""

    class Concepto(models.TextChoices):
        SUELDO_GANADO = "SUELDO GANADO"
        OTROS_INGRESOS = "OTROS INGRESOS"
        ANTICIPO = "ANTICIPO"
        AFP = "AFP"
        RC_IVA = "RC-IVA"
        SALDO_RC_IVA = "SALDO RC-IVA"

    pk = models.CompositePrimaryKey("boleta", "concepto")
    boleta = models.ForeignKey(BoletaPago, on_delete=models.CASCADE, db_column="NroB", related_name="detalles")
    concepto = models.CharField(max_length=20, choices=Concepto.choices, db_column="Concepto")
    base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column="Base")
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, db_column="Porcentaje")
    monto = models.DecimalField(max_digits=10, decimal_places=2, db_column="Monto")

    class Meta:
        db_table = "detalle_boleta"

    def __str__(self):
        return f"{self.concepto}: {self.monto}"


class Anticipo(models.Model):
    """Anticipos de sueldo (RN-06)."""

    nro = models.AutoField(primary_key=True, db_column="Nro")
    contrato = models.ForeignKey("kardex.Contrato", on_delete=models.PROTECT, db_column="NroCon",
                                 related_name="anticipos")
    fecha = models.DateField(db_column="Fecha")
    monto = models.DecimalField(max_digits=10, decimal_places=2, db_column="Monto")
    planilla = models.ForeignKey(Planilla, on_delete=models.PROTECT, null=True, blank=True, db_column="NroPla",
                                 related_name="anticipos")

    class Meta:
        db_table = "anticipo"
        constraints = [models.CheckConstraint(condition=Q(monto__gt=0), name="anticipo_monto_check")]

    def __str__(self):
        return f"Anticipo {self.nro}: {self.monto}"


class FormularioF110(models.Model):
    """Descargo de facturas para el crédito fiscal del RC-IVA (RF-14)."""

    nro = models.AutoField(primary_key=True, db_column="Nro")
    contrato = models.ForeignKey("kardex.Contrato", on_delete=models.PROTECT, db_column="NroCon",
                                 related_name="formularios_f110")
    anio = models.SmallIntegerField("año", db_column="Año")
    mes = TinyIntegerField(db_column="Mes")
    monto_fact = models.DecimalField(max_digits=10, decimal_places=2, db_column="MontoFact")
    fecha_pres = models.DateField(db_column="FechaPres")

    class Meta:
        db_table = "formulario_f110"
        constraints = [
            models.UniqueConstraint(fields=["contrato", "anio", "mes"], name="formulario_f110_con_anio_mes_uniq"),
        ]

    def __str__(self):
        return f"F110 {self.mes:02d}/{self.anio}: {self.monto_fact}"


class Marcacion(models.Model):
    """Días trabajados importados del control de asistencia (patrón Adapter)."""

    id = models.AutoField(primary_key=True, db_column="Id")
    contrato = models.ForeignKey("kardex.Contrato", on_delete=models.PROTECT, db_column="NroCon",
                                 related_name="marcaciones")
    anio = models.SmallIntegerField("año", db_column="Año")
    mes = TinyIntegerField(db_column="Mes")
    dias_trab = TinyIntegerField("días trabajados", db_column="DiasTrab")

    class Meta:
        db_table = "marcacion"
        constraints = [
            models.UniqueConstraint(fields=["contrato", "anio", "mes"], name="marcacion_con_anio_mes_uniq"),
            models.CheckConstraint(condition=Q(dias_trab__gte=0, dias_trab__lte=30), name="marcacion_dias_check"),
        ]

    def __str__(self):
        return f"{self.mes:02d}/{self.anio}: {self.dias_trab} días"
