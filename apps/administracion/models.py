"""Modelos del módulo Administración (docs/05): GESTION SALARIAL, PARAMETRO, FERIADO, ROL, USUARIO y BITACORA."""

import bcrypt
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models import Q

from apps.core.campos import TinyIntegerField


class GestionSalarial(models.Model):
    """Gestión anual de planillas; cerrada, sus parámetros no se editan (RF-22, regla 3)."""

    class Estado(models.TextChoices):
        ABIERTA = "ABIERTA"
        CERRADA = "CERRADA"

    anio = models.SmallIntegerField("año", primary_key=True, db_column="Año")
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ABIERTA, db_column="Estado")

    class Meta:
        db_table = "gestion_salarial"

    def __str__(self):
        return str(self.anio)


class Parametro(models.Model):
    """Parámetros legales y de negocio por gestión (clave-valor). Se leen con apps.core.parametros."""

    class Clave(models.TextChoices):
        SMN = "SMN", "Salario mínimo nacional"
        PORC_AFP = "PORC_AFP", "Aporte laboral AFP (%)"
        UMBRAL_AFP = "UMBRAL_AFP", "Umbral AFP (salarios mínimos)"
        PORC_IVA = "PORC_IVA", "Alícuota RC-IVA (%)"
        PLAZO_AFIL = "PLAZO_AFIL", "Plazo de afiliación CPS (días hábiles)"
        PLAZO_BAJA = "PLAZO_BAJA", "Plazo del aviso de baja (días hábiles)"
        EDAD_MAX_HIJO = "EDAD_MAX_HIJO", "Edad máxima de hijo beneficiario"
        DIAS_LAB = "DIAS_LAB", "Días laborables por semana"
        VALOR_LACT = "VALOR_LACT", "Valor de la lactancia (múltiplos del SMN)"
        PLAZO_FINIQ = "PLAZO_FINIQ", "Plazo de pago del finiquito (días calendario)"
        ANTIG_MIN_INDEM = "ANTIG_MIN_INDEM", "Días continuos para la indemnización"
        UMBRAL_RCIVA = "UMBRAL_RCIVA", "Umbral RC-IVA (salarios mínimos)"
        MNI_RCIVA = "MNI_RCIVA", "Monto no imponible RC-IVA (salarios mínimos)"
        PORC_ANTICIPO = "PORC_ANTICIPO", "Tope mensual de anticipos (%)"
        DIA_ANTICIPO = "DIA_ANTICIPO", "Día desde el cual se registran anticipos"
        DIA_F110 = "DIA_F110", "Último día para aplicar el F110 en el mes"

    pk = models.CompositePrimaryKey("gestion", "clave")
    gestion = models.ForeignKey(GestionSalarial, on_delete=models.PROTECT, db_column="Año", related_name="parametros")
    clave = models.CharField(max_length=20, choices=Clave.choices, db_column="Clave")
    valor = models.DecimalField(max_digits=12, decimal_places=2, db_column="Valor")
    fuente = models.CharField(max_length=80, null=True, blank=True, db_column="Fuente")

    class Meta:
        db_table = "parametro"

    def __str__(self):
        return f"{self.clave} {self.gestion_id}: {self.valor}"


class Feriado(models.Model):
    """Feriados para el cálculo de días hábiles (RF-30).

    MySQL no compara NULL en un UNIQUE: que no se repita un feriado NACIONAL en la misma fecha lo
    valida el servicio de administración.
    """

    class Alcance(models.TextChoices):
        NACIONAL = "NACIONAL"
        DEPARTAMENTAL = "DEPARTAMENTAL"

    id = models.AutoField(primary_key=True, db_column="Id")
    fecha = models.DateField(db_column="Fecha")
    descripcion = models.CharField(max_length=60, db_column="Descripcion")
    alcance = models.CharField(max_length=15, choices=Alcance.choices, db_column="Alcance")
    ubicacion = models.ForeignKey("kardex.Ubicacion", on_delete=models.PROTECT, null=True, blank=True,
                                  db_column="IdUbi", related_name="feriados")

    class Meta:
        db_table = "feriado"
        constraints = [
            models.UniqueConstraint(fields=["fecha", "alcance", "ubicacion"], name="feriado_fecha_alcance_ubi_uniq"),
        ]

    def __str__(self):
        return f"{self.fecha:%d/%m/%Y} {self.descripcion}"


class Rol(models.Model):
    """Roles de acceso con su nivel (RNF-07)."""

    class Nivel(models.TextChoices):
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
        OPERADOR = "OPERADOR", "Operador"
        CONSULTA = "CONSULTA", "Consulta"

    AFILIADOR = "Afiliador"
    ENCARGADO_DE_PAGOS = "Encargado de Pagos"
    RESPONSABLE_VACACIONES = "Responsable de Vacaciones y Lactancias"
    ADMINISTRADOR_DEL_SISTEMA = "Administrador del Sistema"
    CONSULTA = "Consulta"

    id = models.AutoField(primary_key=True, db_column="Id")
    nombre = models.CharField(max_length=40, db_column="Nombre")
    nivel = models.CharField(max_length=15, choices=Nivel.choices, db_column="Nivel")

    class Meta:
        db_table = "rol"

    def __str__(self):
        return self.nombre


def cifrar_clave(clave):
    """Hash BCrypt puro ($2b$, 60 caracteres) para USUARIO.Clave (RNF-06)."""
    return bcrypt.hashpw(clave.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")


def verificar_clave(clave, cifrada):
    if not clave or not cifrada:
        return False
    try:
        return bcrypt.checkpw(clave.encode("utf-8"), cifrada.encode("ascii"))
    except ValueError:  # hash no válido (clave inutilizable) o clave de más de 72 bytes
        return False


class UsuarioManager(BaseUserManager):
    def create_user(self, login, password=None, rol=None, **campos):
        if rol is None:
            raise ValueError("Todo usuario tiene un rol (RF-23).")
        usuario = self.model(login=login, rol=rol, **campos)
        if password:
            usuario.set_password(password)
        else:
            usuario.set_unusable_password()
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, login, password=None, **campos):
        rol = Rol.objects.get(nombre=Rol.ADMINISTRADOR_DEL_SISTEMA)
        return self.create_user(login, password, rol=rol, **campos)


class Usuario(AbstractBaseUser):
    """Cuenta de acceso al sistema (AUTH_USER_MODEL); un único rol por usuario (RF-23)."""

    login = models.CharField(primary_key=True, max_length=30, db_column="Login")
    password = models.CharField("clave", max_length=60, db_column="Clave")
    last_login = None  # USUARIO no tiene esa columna (docs/05).
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, db_column="IdRol", related_name="usuarios")
    empleado = models.ForeignKey("kardex.Empleado", on_delete=models.PROTECT, null=True, blank=True,
                                 db_column="CIEmp", related_name="usuarios")
    activo = models.BooleanField(default=True, db_column="Activo")
    intentos = TinyIntegerField(default=0, db_column="Intentos")
    bloq_hasta = models.DateTimeField("bloqueado hasta", null=True, blank=True, db_column="BloqHasta")

    objects = UsuarioManager()

    USERNAME_FIELD = "login"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "usuario"
        constraints = [
            models.CheckConstraint(condition=Q(intentos__gte=0, intentos__lte=3), name="usuario_intentos_check"),
        ]

    def __str__(self):
        return self.login

    @property
    def is_active(self):
        return self.activo

    @property
    def nivel(self):
        return self.rol.nivel

    def set_password(self, raw_password):
        self.password = cifrar_clave(raw_password)
        self._password = raw_password

    def check_password(self, raw_password):
        return verificar_clave(raw_password, self.password)


class BitacoraQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise PermissionError("La bitácora es de solo lectura (RF-31).")

    def delete(self):
        raise PermissionError("La bitácora es de solo lectura (RF-31).")


class Bitacora(models.Model):
    """Auditoría de operaciones, de solo lectura (RNF-09, RF-31). Se escribe con apps.core.auditoria."""

    class Operacion(models.TextChoices):
        ALTA = "ALTA"
        ACTUALIZACION = "ACTUALIZACION"
        CORRECCION = "CORRECCION"
        BAJA = "BAJA"
        LOGIN_FALLIDO = "LOGIN FALLIDO"
        BLOQUEO = "BLOQUEO"
        ACCESO_DENEGADO = "ACCESO DENEGADO"

    OPERACIONES_CON_MOTIVO = (Operacion.ACTUALIZACION, Operacion.CORRECCION)

    id = models.BigAutoField(primary_key=True, db_column="Id")
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, null=True, blank=True, db_column="Login",
                                related_name="bitacora")
    login_intento = models.CharField(max_length=30, null=True, blank=True, db_column="LoginIntento")
    fecha_hora = models.DateTimeField(db_column="FechaHora")
    operacion = models.CharField(max_length=20, choices=Operacion.choices, db_column="Operacion")
    tabla = models.CharField(max_length=40, null=True, blank=True, db_column="Tabla")
    valor_ant = models.TextField(null=True, blank=True, db_column="ValorAnt")
    valor_nuevo = models.TextField(null=True, blank=True, db_column="ValorNuevo")
    motivo = models.CharField(max_length=200, null=True, blank=True, db_column="Motivo")
    ip = models.CharField("IP", max_length=45, db_column="IP")

    objects = BitacoraQuerySet.as_manager()

    class Meta:
        db_table = "bitacora"
        ordering = ["-fecha_hora", "-id"]

    def __str__(self):
        return f"{self.fecha_hora:%d/%m/%Y %H:%M} {self.operacion} {self.tabla or ''}".strip()

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise PermissionError("La bitácora es de solo lectura (RF-31).")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("La bitácora es de solo lectura (RF-31).")
