"""Datos de prueba del módulo Planillas: haber básico, parámetros vigentes y contratos con marcación."""

import datetime
from decimal import Decimal

from apps.administracion.models import Parametro
from apps.core.parametros import parametros
from apps.core.tests.fabricas import ContratoFactory, UsuarioFactory, rol
from apps.kardex.models import AjusteSalarial
from apps.planillas.models import Marcacion

ANIO = 2026
MES = 3

# Valores vigentes de docs/04 (DS 5516 y Gestora Pública) para PL-03 y RF-12.
VIGENTES = {"SMN": "3300.00", "PORC_AFP": "12.71", "UMBRAL_AFP": "0.00"}


def haber(monto, categoria="A", anio=ANIO):
    AjusteSalarial.objects.update_or_create(
        categoria_id=categoria, gestion_id=anio, defaults={"haber_basico": Decimal(monto)}
    )


def usar_valores_vigentes(anio=ANIO):
    for clave, valor in VIGENTES.items():
        Parametro.objects.filter(gestion_id=anio, clave=clave).update(valor=Decimal(valor))
    parametros.invalidar(anio)


def contrato_con_marcacion(dias, anio=ANIO, mes=MES, **campos):
    contrato = ContratoFactory(**campos)
    Marcacion.objects.create(contrato=contrato, anio=anio, mes=mes, dias_trab=dias)
    return contrato


def encargado():
    return UsuarioFactory(rol=rol("Encargado de Pagos"))


def fecha(dia, mes=MES, anio=ANIO):
    return datetime.date(anio, mes, dia)
