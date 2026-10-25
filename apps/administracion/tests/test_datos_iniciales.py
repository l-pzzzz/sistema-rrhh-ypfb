"""Datos iniciales de la fase base: roles, gestión 2026 con sus parámetros y categorías (docs/04, RF-03, RF-22)."""

from decimal import Decimal

import pytest

from apps.administracion.models import GestionSalarial, Parametro, Rol
from apps.kardex.models import AjusteSalarial, Categoria

pytestmark = pytest.mark.django_db


def test_roles_con_su_nivel():
    assert dict(Rol.objects.values_list("nombre", "nivel")) == {
        "Afiliador": "OPERADOR",
        "Encargado de Pagos": "OPERADOR",
        "Responsable de Vacaciones y Lactancias": "OPERADOR",
        "Administrador del Sistema": "ADMINISTRADOR",
        "Consulta": "CONSULTA",
    }


def test_gestion_2026_abierta():
    assert GestionSalarial.objects.get(anio=2026).estado == GestionSalarial.Estado.ABIERTA


def test_parametros_iniciales_del_caso():
    valores = dict(Parametro.objects.filter(gestion_id=2026).values_list("clave", "valor"))
    assert valores == {
        "SMN": Decimal("1656.00"),
        "PORC_AFP": Decimal("12.21"),
        "UMBRAL_AFP": Decimal("2.00"),
        "PORC_IVA": Decimal("13.00"),
        "PLAZO_AFIL": Decimal("6.00"),
        "PLAZO_BAJA": Decimal("5.00"),
        "EDAD_MAX_HIJO": Decimal("25.00"),
        "DIAS_LAB": Decimal("5.00"),
        "VALOR_LACT": Decimal("1.00"),
        "PLAZO_FINIQ": Decimal("15.00"),
        "ANTIG_MIN_INDEM": Decimal("90.00"),
        # Las 5 claves de planillas las carga la migración planillas.0002 (docs/04).
        "UMBRAL_RCIVA": Decimal("2.00"),
        "MNI_RCIVA": Decimal("2.00"),
        "PORC_ANTICIPO": Decimal("50.00"),
        "DIA_ANTICIPO": Decimal("15.00"),
        "DIA_F110": Decimal("15.00"),
    }
    assert not Parametro.objects.filter(gestion_id=2026, fuente__isnull=True).exists()


def test_categorias_por_antiguedad():
    assert list(Categoria.objects.order_by("cod").values_list("cod", "anios_min", "anios_max")) == [
        ("A", 0, 5),
        ("B", 6, 15),
        ("C", 16, None),
    ]


def test_sin_haber_basico_inicial():
    """El haber básico lo registra el Administrador (CU-13.3)."""
    assert not AjusteSalarial.objects.exists()
