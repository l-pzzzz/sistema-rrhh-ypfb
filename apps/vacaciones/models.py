"""Modelos del módulo Vacaciones y lactancias (docs/05): SOLICITUD VACACION y ENTREGA LACTANCIA."""

from django.db import models
from django.db.models import F, Q

from apps.core.campos import TinyIntegerField


class SolicitudVacacion(models.Model):
    """Vacaciones y licencias firmadas por el jefe inmediato (RF-17)."""

    class Tipo(models.TextChoices):
        VACACION = "VACACION", "Vacación"
        LICENCIA = "LICENCIA", "Licencia"

    nro = models.AutoField(primary_key=True, db_column="Nro")
    contrato = models.ForeignKey("kardex.Contrato", on_delete=models.PROTECT, db_column="NroCon",
                                 related_name="solicitudes_vacacion")
    tipo = models.CharField(max_length=10, choices=Tipo.choices, db_column="Tipo")
    fecha_sol = models.DateField("fecha de solicitud", db_column="FechaSol")
    fecha_firma = models.DateField("fecha de firma", db_column="FechaFirma")
    fecha_desde = models.DateField(db_column="FechaDesde")
    fecha_hasta = models.DateField(db_column="FechaHasta")
    dias = models.DecimalField(max_digits=4, decimal_places=1, db_column="Dias")

    class Meta:
        db_table = "solicitud_vacacion"
        constraints = [
            models.CheckConstraint(
                condition=Q(fecha_hasta__gte=F("fecha_desde")), name="solicitud_vacacion_fechas_check"
            ),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.fecha_desde:%d/%m/%Y} - {self.fecha_hasta:%d/%m/%Y}"


class EntregaLactancia(models.Model):
    """Entregas mensuales del subsidio de lactancia (en especie, 12 por hijo, RF-19).

    "Una por mes y por hijo" depende del mes de la fecha y lo valida el servicio de vacaciones.
    """

    nro = models.AutoField(primary_key=True, db_column="Nro")
    contrato = models.ForeignKey("kardex.Contrato", on_delete=models.PROTECT, db_column="NroCon",
                                 related_name="entregas_lactancia")
    beneficiaria = models.ForeignKey("kardex.Dependiente", on_delete=models.PROTECT, db_column="CIBenef",
                                     related_name="lactancias_recibidas")
    hijo = models.ForeignKey("kardex.Dependiente", on_delete=models.PROTECT, db_column="CIHijo",
                             related_name="lactancias")
    fecha = models.DateField(db_column="Fecha")
    nro_entrega = TinyIntegerField("número de entrega", db_column="NroEntrega")

    class Meta:
        db_table = "entrega_lactancia"
        constraints = [
            models.UniqueConstraint(fields=["hijo", "nro_entrega"], name="entrega_lactancia_hijo_nro_uniq"),
            models.CheckConstraint(
                condition=Q(nro_entrega__gte=1, nro_entrega__lte=12), name="entrega_lactancia_nro_check"
            ),
        ]

    def __str__(self):
        return f"Entrega {self.nro_entrega} de {self.hijo_id}"
