"""Reglas de negocio del módulo Kardex y contratos (CU-01 a CU-03).

Los servicios lanzan ``ValidationError`` con el mensaje del informe; las vistas lo muestran en el
formulario. Cada alta, actualización, corrección o retiro queda en BITACORA (RF-31).
"""

import datetime
import json
import os
import re
from dataclasses import dataclass

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Prefetch, Q
from django.utils import timezone

from apps.administracion.models import Bitacora
from apps.core import auditoria
from apps.core.parametros import parametros
from apps.core.senales import contrato_registrado, contrato_retirado

from .models import (
    AjusteSalarial,
    Categoria,
    Contrato,
    ContratoCargo,
    Dependiente,
    Documento,
    Empleado,
    Persona,
    TipoDocumento,
)

ALTA = Bitacora.Operacion.ALTA
BAJA = Bitacora.Operacion.BAJA
ACTUALIZACION = Bitacora.Operacion.ACTUALIZACION
CORRECCION = Bitacora.Operacion.CORRECCION

# CI con complemento opcional: 1234567 o 1234567-1A (RF-01, regla 2).
PATRON_CI = re.compile(r"^\d{4,12}(-[0-9A-Z]{1,2})?$")

CAMPOS_PERSONA = ("nombres", "apellidos", "fecha_nac", "sexo", "telefono")
CAMPOS_EMPLEADO = ("codigo", "fecha_ingreso", "direccion", "nom_emerg", "par_emerg", "tel_emerg")
CAMPOS_DEPENDIENTE = (*CAMPOS_PERSONA, "parentesco")

TIPO_DOCUMENTO_CI = "CI"  # Cargado por la migración 0003_tipo_documento_ci.
TAMANIO_MAXIMO = 5 * 1024 * 1024  # RF-04, regla 1.
# Extensión → firma del archivo (RF-04, regla 2).
FIRMAS = {
    ".pdf": b"%PDF",
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
    ".png": b"\x89PNG\r\n\x1a\n",
}

PREFIJO_ALERTA = "Cambio de categoría:"
DIAS_ALERTA = 30  # Días que el Afiliador ve una alerta de cambio de categoría (docs/06, decisiones de C1).
AVISO_SIN_AFILIACION = "El trabajador aún no está afiliado a la CPS"


# ---------------------------------------------------------------- utilidades


def normalizar_ci(ci):
    ci = (ci or "").strip().upper()
    if not PATRON_CI.match(ci):
        raise ValidationError({"ci": "CI no válido: use solo números y, si corresponde, el complemento (1234567-1A)."})
    return ci


def anios_cumplidos(desde, hasta):
    """Años cumplidos entre dos fechas (antigüedad, RF-03; edad del hijo, RF-05)."""
    return hasta.year - desde.year - ((hasta.month, hasta.day) < (desde.month, desde.day))


def nombre_completo(persona):
    return f"{persona.nombres} {persona.apellidos}"


def _validar_operacion(operacion, motivo):
    """Actualizar (cambio real) o corregir (error de registro), siempre con motivo (RF-01, regla 4)."""
    if operacion not in (ACTUALIZACION, CORRECCION):
        raise ValidationError({"operacion": "Indique si es una actualización o corrección."})
    motivo = (motivo or "").strip()
    if not motivo:
        raise ValidationError({"motivo": "Indique el motivo del cambio."})
    if len(motivo) > 200:
        raise ValidationError({"motivo": "El motivo no puede superar los 200 caracteres."})
    return motivo


def _vacio_a_nulo(valor):
    return None if isinstance(valor, str) and not valor.strip() else valor


def _cambios(objeto, datos, campos):
    """(valores anteriores, valores nuevos) solo de los campos que cambian."""
    anterior, nuevo = {}, {}
    for campo in campos:
        if campo not in datos:
            continue
        valor = _vacio_a_nulo(datos[campo])
        if getattr(objeto, campo) != valor:
            anterior[campo] = getattr(objeto, campo)
            nuevo[campo] = valor
    return anterior, nuevo


def _aplicar(objeto, nuevo):
    for campo, valor in nuevo.items():
        setattr(objeto, campo, valor)
    objeto.save()


def _sin_cambios():
    return ValidationError("No se registró ningún cambio.")


# ---------------------------------------------------------------- CU-01.1


def buscar_empleados(texto="", departamento=None, categoria=None, estado=None):
    """CU-01.1 Buscar empleado por CI, código o nombre (RF-29).

    Cada palabra debe aparecer en el CI, el código, los nombres o los apellidos. La base usa la
    intercalación utf8mb4_0900_ai_ci: no distingue mayúsculas ni tildes ("perez" encuentra "Pérez").
    Devuelve la lista resumida (CI, nombre, cargo y estado) con ``cargos`` y ``categoria`` del
    contrato vigente.
    """
    empleados = Empleado.objects.all()
    for palabra in (texto or "").split():
        empleados = empleados.filter(
            Q(ci__icontains=palabra)
            | Q(codigo__icontains=palabra)
            | Q(nombres__icontains=palabra)
            | Q(apellidos__icontains=palabra)
        )
    vigente = {}
    if departamento:
        vigente["contratos__cargos__ubicacion"] = departamento
    if categoria:
        vigente["contratos__categoria"] = categoria
    if vigente:
        empleados = empleados.filter(contratos__estado=Contrato.Estado.VIGENTE, **vigente).distinct()
    if estado:
        empleados = empleados.filter(estado=estado)
    empleados = empleados.prefetch_related(
        Prefetch(
            "contratos",
            queryset=Contrato.objects.filter(estado=Contrato.Estado.VIGENTE).prefetch_related("cargos"),
            to_attr="contratos_vigentes",
        )
    ).order_by("apellidos", "nombres")

    resultado = list(empleados)
    for empleado in resultado:
        empleado.cargos = [c.nombre for contrato in empleado.contratos_vigentes for c in contrato.cargos.all()]
        empleado.categoria = next((c.categoria_id for c in empleado.contratos_vigentes), None)
    return resultado


# ---------------------------------------------------------------- CU-01.2 y CU-01.3


class ServicioEmpleado:
    """CU-01.2 Registrar y CU-01.3 Actualizar o corregir datos del empleado (RF-01)."""

    def registrar(self, datos):
        """CU-01.2: el CI y el código son únicos; el empleado queda ACTIVO."""
        ci = normalizar_ci(datos.get("ci"))
        codigo = (datos.get("codigo") or "").strip().upper()
        errores = {}
        if Empleado.objects.filter(pk=ci).exists():
            errores["ci"] = "El CI ya está registrado"
        if Empleado.objects.filter(codigo=codigo).exists():
            errores["codigo"] = "El código ya está registrado"
        if errores:
            raise ValidationError(errores)

        valores_persona = {c: _vacio_a_nulo(datos.get(c)) for c in CAMPOS_PERSONA}
        valores_empleado = {c: _vacio_a_nulo(datos.get(c)) for c in CAMPOS_EMPLEADO} | {"codigo": codigo}
        with transaction.atomic():
            if Persona.objects.filter(pk=ci).exists():
                # Un dependiente que ingresa a la empresa: solo se agrega la fila de EMPLEADO.
                Persona.objects.filter(pk=ci).update(**valores_persona)
                Empleado(persona_id=ci, estado=Empleado.Estado.ACTIVO, **valores_empleado).save_base(raw=True)
                empleado = Empleado.objects.get(pk=ci)
            else:
                empleado = Empleado.objects.create(
                    ci=ci, estado=Empleado.Estado.ACTIVO, **valores_persona, **valores_empleado
                )
            auditoria.registrar(
                ALTA, "empleado",
                valor_nuevo={"ci": ci, **valores_persona, **valores_empleado, "estado": empleado.estado},
            )
        return empleado

    def modificar(self, empleado, datos, operacion, motivo):
        """CU-01.3: actualizar o corregir con motivo; la bitácora guarda el valor anterior y el nuevo."""
        motivo = _validar_operacion(operacion, motivo)
        if "ci" in datos and datos["ci"] != empleado.ci:
            raise ValidationError({"ci": "El CI no se puede modificar."})
        if "codigo" in datos:
            datos = datos | {"codigo": (datos["codigo"] or "").strip().upper()}
            if Empleado.objects.filter(codigo=datos["codigo"]).exclude(pk=empleado.pk).exists():
                raise ValidationError({"codigo": "El código ya está registrado"})
        anterior, nuevo = _cambios(empleado, datos, CAMPOS_PERSONA + CAMPOS_EMPLEADO)
        if not nuevo:
            raise _sin_cambios()
        with transaction.atomic():
            _aplicar(empleado, nuevo)
            auditoria.registrar(operacion, "empleado", anterior, nuevo, motivo)
        return empleado


# ---------------------------------------------------------------- CU-01.4 y CU-03.2


class ServicioDocumento:
    """CU-01.4 Adjuntar o reemplazar documentos y CU-03.2 Adjuntar fotocopia de CI (RF-04)."""

    @staticmethod
    def validar_archivo(archivo):
        """PDF, JPG o PNG (extensión y firma del archivo) de hasta 5 MB."""
        if archivo is None:
            raise ValidationError({"archivo": "Seleccione un archivo."})
        if archivo.size > TAMANIO_MAXIMO:
            raise ValidationError({"archivo": "El archivo supera el tamaño máximo de 5 MB"})
        firma = FIRMAS.get(os.path.splitext(archivo.name)[1].lower())
        archivo.seek(0)
        cabecera = archivo.read(8)
        archivo.seek(0)
        if firma is None or not cabecera.startswith(firma):
            raise ValidationError({"archivo": "Solo se aceptan archivos PDF, JPG o PNG."})

    def adjuntar(self, persona, tipo, archivo, fecha_emision=None):
        """Adjunta un documento vigente al empleado o dependiente."""
        self.validar_archivo(archivo)
        with transaction.atomic():
            documento = Documento.objects.create(
                persona_id=persona.pk,
                tipo=tipo,
                fecha_emision=fecha_emision,
                archivo=archivo,
                fecha_carga=timezone.now(),
                vigente=True,
            )
            auditoria.registrar(ALTA, "documento", valor_nuevo=self._valores(documento))
        return documento

    def reemplazar(self, documento, archivo, motivo, fecha_emision=None):
        """Un documento no se elimina: la versión anterior queda con Vigente = False (RF-04, regla 3)."""
        if not documento.vigente:
            raise ValidationError("Solo se puede reemplazar un documento vigente.")
        motivo = _validar_operacion(ACTUALIZACION, motivo)
        self.validar_archivo(archivo)
        with transaction.atomic():
            Documento.objects.filter(pk=documento.pk).update(vigente=False)
            documento.vigente = False
            nuevo = Documento.objects.create(
                persona_id=documento.persona_id,
                tipo=documento.tipo,
                fecha_emision=fecha_emision,
                archivo=archivo,
                fecha_carga=timezone.now(),
                vigente=True,
            )
            auditoria.registrar(
                ACTUALIZACION, "documento", self._valores(documento), self._valores(nuevo), motivo
            )
        return nuevo

    @staticmethod
    def _valores(documento):
        return {
            "nro": documento.nro,
            "ci": documento.persona_id,
            "tipo": documento.tipo.descripcion,
            "archivo": documento.archivo.name,
            "vigente": documento.vigente,
        }


# ---------------------------------------------------------------- CU-02


@dataclass(frozen=True)
class AlertaCategoria:
    """Alerta al Afiliador por el cambio de categoría de un contrato (RF-03)."""

    contrato: int
    ci: str
    nombre: str
    mensaje: str
    fecha: datetime.datetime | None = None


class ServicioContrato:
    """CU-02 Gestionar contrato del empleado (RF-02, RF-03, RF-28).

    Sujeto del patrón Observer (docs/06): emite ``contrato_registrado`` al registrar un contrato y
    ``contrato_retirado`` al registrar el retiro. Las señales se envían dentro de la transacción:
    si un observador falla, no queda un contrato a medias.
    """

    # CU-02.2

    @staticmethod
    def _categoria_para(anios, categorias):
        for categoria in categorias:
            if categoria.anios_min <= anios and (categoria.anios_max is None or anios <= categoria.anios_max):
                return categoria
        raise ValidationError(f"No hay una categoría configurada para {anios} años de antigüedad.")

    def categoria_por_antiguedad(self, fecha_ingreso, hoy=None):
        """CU-02.2: categoría según los años cumplidos desde EMPLEADO.FechaIngreso (tabla CATEGORIA)."""
        hoy = hoy or timezone.localdate()
        return self._categoria_para(anios_cumplidos(fecha_ingreso, hoy), list(Categoria.objects.all()))

    @staticmethod
    def haber_basico(categoria, anio):
        """Haber básico de la categoría en la gestión (AJUSTE SALARIAL), o None si no está configurado."""
        return (
            AjusteSalarial.objects.filter(categoria_id=getattr(categoria, "pk", categoria), gestion_id=anio)
            .values_list("haber_basico", flat=True)
            .first()
        )

    # CU-02.1

    @staticmethod
    def _validar(fecha_inicio, fecha_fin, cargos):
        errores = {}
        if fecha_fin is not None and fecha_fin <= fecha_inicio:
            errores["fecha_fin"] = "La fecha de fin debe ser posterior a la fecha de inicio."
        if not cargos:
            errores["cargos"] = "El contrato debe tener al menos un cargo."
        if errores:
            raise ValidationError(errores)

    def registrar(self, empleado, fecha_inicio, fecha_fin, cargos, hoy=None):
        """CU-02.1 Registrar contrato con sus cargos y la categoría por antigüedad (CU-02.2)."""
        hoy = hoy or timezone.localdate()
        cargos = list(cargos)
        self._validar(fecha_inicio, fecha_fin, cargos)
        with transaction.atomic():
            # Bloquea al empleado para que dos registros simultáneos no creen dos contratos vigentes.
            empleado = Empleado.objects.select_for_update().get(pk=empleado.pk)
            if empleado.contratos.filter(estado=Contrato.Estado.VIGENTE).exists():
                raise ValidationError(
                    "Rechazado: un empleado no puede tener dos contratos vigentes. "
                    "Actualice el contrato vigente o registre el retiro."
                )
            categoria = self.categoria_por_antiguedad(empleado.fecha_ingreso, hoy)
            contrato = Contrato.objects.create(
                empleado=empleado,
                categoria=categoria,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                estado=Contrato.Estado.VIGENTE,
            )
            ContratoCargo.objects.bulk_create(ContratoCargo(contrato=contrato, cargo=c) for c in cargos)
            if empleado.estado == Empleado.Estado.RETIRADO:
                # Reingreso (decisión C1, docs/06): el empleado vuelve a ACTIVO.
                empleado.estado = Empleado.Estado.ACTIVO
                empleado.save(update_fields=["estado"])
                auditoria.registrar(
                    ALTA, "empleado",
                    valor_ant={"ci": empleado.ci, "estado": Empleado.Estado.RETIRADO},
                    valor_nuevo={"ci": empleado.ci, "estado": Empleado.Estado.ACTIVO, "contrato": contrato.nro},
                )
            auditoria.registrar(ALTA, "contrato", valor_nuevo=self._valores(contrato))
            contrato_registrado.send(sender=Contrato, contrato=contrato)
        return contrato

    # CU-02.3

    def modificar(self, contrato, datos, cargos, operacion, motivo):
        """CU-02.3 Actualizar (cambio de cargo o renovación) o corregir (error de registro) el contrato vigente."""
        motivo = _validar_operacion(operacion, motivo)
        if contrato.estado != Contrato.Estado.VIGENTE:
            raise ValidationError("Solo se puede modificar el contrato vigente.")
        cargos = list(cargos)
        fecha_inicio = datos.get("fecha_inicio", contrato.fecha_inicio)
        fecha_fin = datos.get("fecha_fin", contrato.fecha_fin)
        self._validar(fecha_inicio, fecha_fin, cargos)

        anterior, nuevo = _cambios(contrato, datos, ("fecha_inicio", "fecha_fin"))
        cargos_antes = list(contrato.cargos.order_by("nombre", "id"))
        if {c.pk for c in cargos_antes} != {c.pk for c in cargos}:
            anterior["cargos"] = [c.nombre for c in cargos_antes]
            nuevo["cargos"] = sorted(c.nombre for c in cargos)
        if not nuevo:
            raise _sin_cambios()
        with transaction.atomic():
            _aplicar(contrato, {k: v for k, v in nuevo.items() if k != "cargos"})
            if "cargos" in nuevo:
                ContratoCargo.objects.filter(contrato=contrato).delete()
                ContratoCargo.objects.bulk_create(ContratoCargo(contrato=contrato, cargo=c) for c in cargos)
            auditoria.registrar(operacion, "contrato", anterior, nuevo, motivo)
        return contrato

    # CU-02.4

    def registrar_retiro(self, contrato, fecha_retiro, tipo_retiro, motivo):
        """CU-02.4 Registrar retiro (RF-28): contrato CONCLUIDO, empleado RETIRADO y aviso a los observadores."""
        motivo = (motivo or "").strip()
        errores = {}
        if contrato.estado != Contrato.Estado.VIGENTE:
            raise ValidationError("Solo se puede registrar el retiro de un contrato vigente.")
        if fecha_retiro < contrato.fecha_inicio:
            errores["fecha_retiro"] = "La fecha de retiro no puede ser anterior al inicio del contrato."
        if tipo_retiro not in Contrato.TipoRetiro.values:
            errores["tipo_retiro"] = "Seleccione un tipo de retiro válido."
        if not motivo:
            errores["motivo_retiro"] = "Indique el motivo del retiro."
        if errores:
            raise ValidationError(errores)

        with transaction.atomic():
            anterior = self._valores(contrato)
            contrato.fecha_retiro = fecha_retiro
            contrato.tipo_retiro = tipo_retiro
            contrato.motivo_retiro = motivo
            contrato.estado = Contrato.Estado.CONCLUIDO
            contrato.save(update_fields=["fecha_retiro", "tipo_retiro", "motivo_retiro", "estado"])
            empleado = contrato.empleado
            empleado.estado = Empleado.Estado.RETIRADO
            empleado.save(update_fields=["estado"])
            auditoria.registrar(BAJA, "contrato", anterior, self._valores(contrato), motivo)
            auditoria.registrar(
                BAJA, "empleado",
                {"ci": empleado.ci, "estado": Empleado.Estado.ACTIVO},
                {"ci": empleado.ci, "estado": Empleado.Estado.RETIRADO},
                motivo,
            )
            contrato_retirado.send(sender=Contrato, contrato=contrato)
        return contrato

    # RF-03: tarea programada

    def recalcular_categorias(self, hoy=None):
        """Recalcula la categoría de cada contrato vigente (RF-03, regla 2) y devuelve las alertas.

        El cambio queda en BITACORA como ACTUALIZACION con el motivo "Cambio de categoría: A → B",
        que es lo que el Afiliador ve como alerta (``alertas_categoria``).
        """
        hoy = hoy or timezone.localdate()
        categorias = list(Categoria.objects.all())
        alertas = []
        vigentes = Contrato.objects.filter(estado=Contrato.Estado.VIGENTE).select_related("empleado")
        for contrato in vigentes:
            nueva = self._categoria_para(anios_cumplidos(contrato.empleado.fecha_ingreso, hoy), categorias)
            if nueva.pk == contrato.categoria_id:
                continue
            anterior = contrato.categoria_id
            mensaje = f"{PREFIJO_ALERTA} {anterior} → {nueva.pk}"
            with transaction.atomic():
                Contrato.objects.filter(pk=contrato.pk).update(categoria=nueva)
                auditoria.registrar(
                    ACTUALIZACION, "contrato",
                    {"nro": contrato.nro, "ci": contrato.empleado_id, "categoria": anterior},
                    {"nro": contrato.nro, "ci": contrato.empleado_id, "categoria": nueva.pk},
                    mensaje,
                )
            alertas.append(
                AlertaCategoria(contrato.nro, contrato.empleado_id, nombre_completo(contrato.empleado), mensaje)
            )
        enviar_alertas_categoria(alertas)
        return alertas

    @staticmethod
    def _valores(contrato):
        return {
            "nro": contrato.nro,
            "ci": contrato.empleado_id,
            "categoria": contrato.categoria_id,
            "fecha_inicio": contrato.fecha_inicio,
            "fecha_fin": contrato.fecha_fin,
            "cargos": sorted(c.nombre for c in contrato.cargos.all()),
            "estado": contrato.estado,
            "fecha_retiro": contrato.fecha_retiro,
            "tipo_retiro": contrato.tipo_retiro,
        }


def correos_afiliadores():
    """Direcciones de CORREO_AFILIADORES (.env, separadas por comas); vacía = alerta solo en pantalla."""
    return list(settings.CORREO_AFILIADORES)


def enviar_alertas_categoria(alertas):
    """Envía por correo las alertas de cambio de categoría al Afiliador (docs/06, RF-03 regla 2)."""
    destinatarios = correos_afiliadores()
    if not alertas or not destinatarios:
        return
    lineas = [f"- {a.nombre} (CI {a.ci}, contrato {a.contrato}): {a.mensaje}" for a in alertas]
    send_mail(
        f"Cambio de categoría: {len(alertas)} contrato(s)",
        "Se recalculó la categoría por antigüedad de los siguientes contratos:\n\n" + "\n".join(lineas),
        None,
        destinatarios,
    )


def alertas_categoria(hoy=None, dias=DIAS_ALERTA):
    """Alertas de cambio de categoría de los últimos ``dias`` días, leídas de BITACORA (RF-03, regla 2)."""
    hoy = hoy or timezone.localdate()
    desde = timezone.make_aware(datetime.datetime.combine(hoy - datetime.timedelta(days=dias), datetime.time.min))
    hasta = timezone.make_aware(datetime.datetime.combine(hoy + datetime.timedelta(days=1), datetime.time.min))
    registros = Bitacora.objects.filter(
        operacion=ACTUALIZACION,
        tabla="contrato",
        motivo__startswith=PREFIJO_ALERTA,
        fecha_hora__gte=desde,
        fecha_hora__lt=hasta,
    )
    filas = [(json.loads(b.valor_nuevo), b) for b in registros]
    nombres = {
        e.ci: nombre_completo(e) for e in Empleado.objects.filter(pk__in={v["ci"] for v, _ in filas})
    }
    return [
        AlertaCategoria(v["nro"], v["ci"], nombres.get(v["ci"], v["ci"]), b.motivo, b.fecha_hora) for v, b in filas
    ]


# ---------------------------------------------------------------- CU-03


def aviso_afiliacion(empleado):
    """Aviso si el contrato vigente no está afiliado a la CPS (precondición del CU-03, decisión C1).

    Se lee el modelo de CPS sin importar sus servicios (AGENTS.md §6).
    """
    AfiliacionCPS = apps.get_model("cps", "AfiliacionCPS")
    afiliado = AfiliacionCPS.objects.filter(
        contrato__empleado=empleado,
        contrato__estado=Contrato.Estado.VIGENTE,
        estado__in=[AfiliacionCPS.Estado.EN_PLAZO, AfiliacionCPS.Estado.FUERA_DE_PLAZO],
    ).exists()
    return [] if afiliado else [AVISO_SIN_AFILIACION]


class ServicioDependiente:
    """CU-03 Gestionar dependientes (RF-04, RF-05)."""

    def registrar(self, empleado, datos, parentesco, fotocopia_ci, hoy=None):
        """CU-03.1 Registrar dependiente con la fotocopia del CI (CU-03.2).

        Devuelve (dependiente, avisos): la edad del hijo (CU-03.4) y la afiliación a la CPS no bloquean.
        """
        hoy = hoy or timezone.localdate()
        if fotocopia_ci is None:
            raise ValidationError({"fotocopia_ci": "La fotocopia del CI es obligatoria."})
        ci = normalizar_ci(datos.get("ci"))
        if ci == empleado.ci:
            raise ValidationError({"ci": "Un empleado no puede ser dependiente de sí mismo."})
        existente = Dependiente.objects.select_related("empleado").filter(pk=ci).first()
        if existente is not None:
            titular = nombre_completo(existente.empleado)
            raise ValidationError({"ci": f"Ya está registrado como dependiente de {titular}"})
        if parentesco not in Dependiente.Parentesco.values:
            raise ValidationError({"parentesco": "Parentesco no permitido."})
        try:
            ServicioDocumento.validar_archivo(fotocopia_ci)
        except ValidationError as error:
            raise ValidationError({"fotocopia_ci": error.messages}) from error

        valores = {c: _vacio_a_nulo(datos.get(c)) for c in CAMPOS_PERSONA}
        with transaction.atomic():
            persona = Persona.objects.filter(pk=ci).first()
            if persona is not None:
                # Por ejemplo, una empleada que es cónyuge de otro empleado: sus datos no se tocan.
                dependiente = Dependiente.crear_desde_persona(persona, empleado=empleado, parentesco=parentesco)
            else:
                dependiente = Dependiente.objects.create(ci=ci, empleado=empleado, parentesco=parentesco, **valores)
            ServicioDocumento().adjuntar(
                dependiente, TipoDocumento.objects.get(descripcion=TIPO_DOCUMENTO_CI), fotocopia_ci
            )
            auditoria.registrar(
                ALTA, "dependiente",
                valor_nuevo={
                    "ci": ci, "ci_empleado": empleado.ci, "parentesco": parentesco,
                    **{c: getattr(dependiente, c) for c in CAMPOS_PERSONA},
                },
            )
        return dependiente, self.avisos(dependiente, hoy) + aviso_afiliacion(empleado)

    def modificar(self, dependiente, datos, operacion, motivo, hoy=None):
        """CU-03.3 Actualizar o corregir dependiente; devuelve los avisos de edad."""
        motivo = _validar_operacion(operacion, motivo)
        if "parentesco" in datos and datos["parentesco"] not in Dependiente.Parentesco.values:
            raise ValidationError({"parentesco": "Parentesco no permitido."})
        anterior, nuevo = _cambios(dependiente, datos, CAMPOS_DEPENDIENTE)
        if not nuevo:
            raise _sin_cambios()
        with transaction.atomic():
            _aplicar(dependiente, nuevo)
            auditoria.registrar(operacion, "dependiente", anterior, nuevo, motivo)
        return self.avisos(dependiente, hoy or timezone.localdate())

    @staticmethod
    def avisos(dependiente, hoy):
        """CU-03.4: advertencia si un hijo o hija supera EDAD_MAX_HIJO (RF-05, regla 4)."""
        if dependiente.parentesco != Dependiente.Parentesco.HIJO:
            return []
        edad_maxima = int(parametros.valor_vigente("EDAD_MAX_HIJO", hoy.year))
        if anios_cumplidos(dependiente.fecha_nac, hoy) > edad_maxima:
            return [f"El hijo o hija supera la edad máxima de beneficiario ({edad_maxima} años)."]
        return []
