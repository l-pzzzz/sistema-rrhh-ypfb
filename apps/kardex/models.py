"""Modelos del módulo Kardex y contratos (docs/05): PERSONA, EMPLEADO, DEPENDIENTE, TIPO DOCUMENTO,
DOCUMENTO, CATEGORIA, AJUSTE SALARIAL, CONTRATO, CONTRATO CARGO, CARGO, FUNCION y UBICACION.
"""

from django.db import models
from django.db.models import F, Q

from apps.core.campos import CharFijoField, TinyIntegerField


class Persona(models.Model):
    """Datos comunes de empleados y dependientes (superclase)."""

    class Sexo(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMENINO = "F", "Femenino"

    ci = models.CharField("CI", primary_key=True, max_length=15, db_column="CI")
    nombres = models.CharField(max_length=60, db_column="Nombres")
    apellidos = models.CharField(max_length=60, db_column="Apellidos")
    fecha_nac = models.DateField("fecha de nacimiento", db_column="FechaNac")
    sexo = CharFijoField(max_length=1, choices=Sexo.choices, db_column="Sexo")
    telefono = models.CharField(max_length=15, null=True, blank=True, db_column="Telefono")

    class Meta:
        db_table = "persona"
        constraints = [
            models.CheckConstraint(condition=Q(sexo__in=["M", "F"]), name="persona_sexo_check"),
        ]

    def __str__(self):
        return f"{self.apellidos}, {self.nombres} ({self.ci})"


class Empleado(Persona):
    """Expediente laboral del trabajador (Kardex)."""

    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO"
        RETIRADO = "RETIRADO"

    persona = models.OneToOneField(
        Persona, parent_link=True, primary_key=True, db_column="CI", on_delete=models.CASCADE,
        related_name="como_empleado",
    )
    codigo = models.CharField(max_length=10, db_column="Codigo")
    fecha_ingreso = models.DateField(db_column="FechaIngreso")
    direccion = models.CharField(max_length=120, null=True, blank=True, db_column="Direccion")
    nom_emerg = models.CharField(max_length=80, null=True, blank=True, db_column="NomEmerg")
    par_emerg = models.CharField(max_length=20, null=True, blank=True, db_column="ParEmerg")
    tel_emerg = models.CharField(max_length=15, null=True, blank=True, db_column="TelEmerg")
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ACTIVO, db_column="Estado")

    class Meta:
        db_table = "empleado"
        constraints = [models.UniqueConstraint(fields=["codigo"], name="empleado_codigo_uniq")]


class Dependiente(Persona):
    """Familiar del trabajador; se registra con un solo trabajador (RF-05)."""

    class Parentesco(models.TextChoices):
        CONYUGE = "CONYUGE", "Cónyuge"
        CONVIVIENTE = "CONVIVIENTE", "Conviviente"
        HIJO = "HIJO", "Hijo o hija"
        PADRE = "PADRE", "Padre"
        MADRE = "MADRE", "Madre"

    persona = models.OneToOneField(
        Persona, parent_link=True, primary_key=True, db_column="CI", on_delete=models.CASCADE,
        related_name="como_dependiente",
    )
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, db_column="CIEmp", related_name="dependientes")
    parentesco = models.CharField(max_length=20, choices=Parentesco.choices, db_column="Parentesco")

    class Meta:
        db_table = "dependiente"
        constraints = [
            models.CheckConstraint(
                condition=Q(parentesco__in=["CONYUGE", "CONVIVIENTE", "HIJO", "PADRE", "MADRE"]),
                name="dependiente_parentesco_check",
            ),
        ]

    @classmethod
    def crear_desde_persona(cls, persona, **campos):
        """Registra como dependiente a una PERSONA que ya existe (por ejemplo, una empleada).

        La herencia multitabla de Django no permite crear el hijo sin volver a escribir el padre;
        aquí solo se inserta la fila de DEPENDIENTE.
        """
        dependiente = cls(persona_id=persona.pk, **campos)
        dependiente.save_base(raw=True)
        return cls.objects.get(pk=persona.pk)


class TipoDocumento(models.Model):
    id = models.AutoField(primary_key=True, db_column="Id")
    descripcion = models.CharField(max_length=40, db_column="Descripcion")

    class Meta:
        db_table = "tipo_documento"

    def __str__(self):
        return self.descripcion


class Documento(models.Model):
    """Documentos digitalizados de empleados y dependientes (RF-04)."""

    nro = models.AutoField(primary_key=True, db_column="Nro")
    persona = models.ForeignKey(Persona, on_delete=models.PROTECT, db_column="CIPer", related_name="documentos")
    tipo = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT, db_column="IdTipo")
    fecha_emision = models.DateField(null=True, blank=True, db_column="FechaEmision")
    archivo = models.FileField(upload_to="documentos/%Y/%m/", max_length=200, db_column="Archivo")
    fecha_carga = models.DateTimeField(db_column="FechaCarga")
    vigente = models.BooleanField(default=True, db_column="Vigente")

    class Meta:
        db_table = "documento"

    def __str__(self):
        return f"{self.tipo} de {self.persona_id}"


class Categoria(models.Model):
    """Categorías salariales por antigüedad en años cumplidos (RF-03)."""

    cod = CharFijoField(primary_key=True, max_length=1, db_column="Cod")
    anios_min = TinyIntegerField("años mínimos", db_column="AñosMin")
    anios_max = TinyIntegerField("años máximos", null=True, blank=True, db_column="AñosMax")

    class Meta:
        db_table = "categoria"
        constraints = [
            models.CheckConstraint(condition=Q(cod__in=["A", "B", "C"]), name="categoria_cod_check"),
        ]

    def __str__(self):
        return self.cod


class AjusteSalarial(models.Model):
    """Haber básico de cada categoría por gestión (CU-13.3)."""

    id = models.AutoField(primary_key=True, db_column="Id")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, db_column="CodCat")
    gestion = models.ForeignKey("administracion.GestionSalarial", on_delete=models.PROTECT, db_column="Año")
    haber_basico = models.DecimalField(max_digits=10, decimal_places=2, db_column="HaberBasico")

    class Meta:
        db_table = "ajuste_salarial"
        constraints = [
            models.UniqueConstraint(fields=["categoria", "gestion"], name="ajuste_salarial_cat_anio_uniq"),
        ]

    def __str__(self):
        return f"{self.categoria_id} {self.gestion_id}: {self.haber_basico}"


class Ubicacion(models.Model):
    id = models.AutoField(primary_key=True, db_column="Id")
    departamento = models.CharField(max_length=60, db_column="Departamento")

    class Meta:
        db_table = "ubicacion"

    def __str__(self):
        return self.departamento


class Cargo(models.Model):
    id = models.AutoField(primary_key=True, db_column="Id")
    nombre = models.CharField(max_length=60, db_column="Nombre")
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT, db_column="IdUbi", related_name="cargos")

    class Meta:
        db_table = "cargo"

    def __str__(self):
        return self.nombre


class Funcion(models.Model):
    id = models.AutoField(primary_key=True, db_column="Id")
    descripcion = models.CharField(max_length=150, db_column="Descripcion")
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, db_column="IdCargo", related_name="funciones")

    class Meta:
        db_table = "funcion"

    def __str__(self):
        return self.descripcion


class Contrato(models.Model):
    """Contrato del trabajador: eje del sistema (AGENTS.md §4).

    "Un solo contrato VIGENTE por empleado" no se puede declarar en MySQL (UNIQUE condicional):
    lo valida el servicio de kardex (CO-01).
    """

    class Estado(models.TextChoices):
        VIGENTE = "VIGENTE"
        CONCLUIDO = "CONCLUIDO"

    class TipoRetiro(models.TextChoices):
        VOLUNTARIO = "VOLUNTARIO", "Voluntario"
        DESPIDO_JUSTIFICADO = "DESPIDO JUSTIFICADO", "Despido justificado"
        DESPIDO_INJUSTIFICADO = "DESPIDO INJUSTIFICADO", "Despido injustificado"

    nro = models.AutoField(primary_key=True, db_column="Nro")
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, db_column="CIEmp", related_name="contratos")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, db_column="CodCat")
    fecha_inicio = models.DateField(db_column="FechaInicio")
    fecha_fin = models.DateField(null=True, blank=True, db_column="FechaFin")
    fecha_retiro = models.DateField(null=True, blank=True, db_column="FechaRetiro")
    tipo_retiro = models.CharField(
        max_length=25, choices=TipoRetiro.choices, null=True, blank=True, db_column="TipoRetiro"
    )
    motivo_retiro = models.CharField(max_length=200, null=True, blank=True, db_column="MotivoRetiro")
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.VIGENTE, db_column="Estado")
    cargos = models.ManyToManyField(Cargo, through="ContratoCargo", related_name="contratos")

    class Meta:
        db_table = "contrato"
        constraints = [
            models.CheckConstraint(
                condition=Q(fecha_fin__isnull=True) | Q(fecha_fin__gt=F("fecha_inicio")),
                name="contrato_fecha_fin_check",
            ),
            models.CheckConstraint(
                condition=Q(fecha_retiro__isnull=True) | Q(fecha_retiro__gte=F("fecha_inicio")),
                name="contrato_fecha_retiro_check",
            ),
        ]

    def __str__(self):
        return f"Contrato {self.nro}"


class ContratoCargo(models.Model):
    """Tabla intermedia: un contrato tiene uno o varios cargos."""

    pk = models.CompositePrimaryKey("contrato", "cargo")
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, db_column="NroCon")
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, db_column="IdCargo")

    class Meta:
        db_table = "contrato_cargo"

    def __str__(self):
        return f"{self.contrato_id} - {self.cargo_id}"
