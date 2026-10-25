"""CU-05.1 Importar días trabajados (RF-10), patrón Adapter (docs/06).

``IFuenteAsistencia`` es la interfaz que usa la planilla; ``AdaptadorArchivoAsistencia`` la implementa
sobre ``ArchivoMarcacionesCSV`` (el archivo Excel o CSV leído con pandas). No hay conexión directa con
equipos biométricos (RF-10, regla 5).
"""

import io
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import pandas as pd

COLUMNAS = ["CI", "DiasTrab"]
DIAS_MIN, DIAS_MAX = 0, 30
EXTENSIONES = (".csv", ".xlsx", ".xls")

MOTIVO_DIAS = "Días trabajados fuera de 0 a 30"
MOTIVO_REPETIDO = "CI repetido en el archivo"


class ArchivoInvalido(ValueError):
    """La estructura del archivo no es la esperada (RF-10, regla 1)."""


@dataclass(frozen=True)
class RegistroAsistencia:
    """Una fila del archivo. ``dias`` es None si la fila tiene un error (``motivo``)."""

    ci: str
    dias: int | None
    motivo: str | None = None


class IFuenteAsistencia(ABC):
    @abstractmethod
    def obtener_dias_trabajados(self, contrato, anio, mes):
        """Días trabajados del contrato en el mes, o None si la fuente no lo registra."""

    @abstractmethod
    def registros(self):
        """Todas las filas de la fuente, ya validadas (``RegistroAsistencia``)."""


class ArchivoMarcacionesCSV:
    """Archivo de marcaciones (CSV o Excel) con las columnas CI y DiasTrab."""

    def __init__(self, archivo):
        self.nombre = getattr(archivo, "name", "") or ""
        if not self.nombre.lower().endswith(EXTENSIONES):
            raise ArchivoInvalido("El archivo debe ser Excel (.xlsx) o CSV (.csv).")
        contenido = archivo.read()
        if not contenido.strip():
            raise ArchivoInvalido("El archivo está vacío.")
        try:
            self.tabla = self._leer(contenido)
        except ArchivoInvalido:
            raise
        except Exception as error:
            raise ArchivoInvalido("No se pudo leer el archivo de marcaciones.") from error
        self.tabla.columns = [str(c).strip() for c in self.tabla.columns]
        if list(self.tabla.columns) != COLUMNAS:
            raise ArchivoInvalido("El archivo debe tener exactamente las columnas CI y DiasTrab.")

    def _leer(self, contenido):
        if self.nombre.lower().endswith(".csv"):
            texto = contenido.decode("utf-8-sig")
            primera = texto.splitlines()[0]
            separador = ";" if ";" in primera and "," not in primera else ","
            return pd.read_csv(io.StringIO(texto), sep=separador, dtype=str, keep_default_na=False)
        return pd.read_excel(io.BytesIO(contenido), dtype=str, keep_default_na=False)

    def filas(self):
        return list(zip(self.tabla["CI"], self.tabla["DiasTrab"], strict=True))


def _dias(texto):
    try:
        valor = Decimal(str(texto).strip())
    except InvalidOperation:
        return None
    if valor != valor.to_integral_value() or not DIAS_MIN <= valor <= DIAS_MAX:
        return None
    return int(valor)


class AdaptadorArchivoAsistencia(IFuenteAsistencia):
    def __init__(self, archivo: ArchivoMarcacionesCSV):
        self.archivo = archivo
        self._registros = None

    def registros(self):
        if self._registros is None:
            filas = [(str(ci).strip(), dias) for ci, dias in self.archivo.filas()]
            repetidos = {ci for ci, n in Counter(ci for ci, _ in filas).items() if n > 1}
            vistos = set()
            self._registros = []
            for ci, dias in filas:
                if ci in repetidos:
                    if ci not in vistos:
                        self._registros.append(RegistroAsistencia(ci, None, MOTIVO_REPETIDO))
                    vistos.add(ci)
                    continue
                valor = _dias(dias)
                motivo = None if valor is not None else MOTIVO_DIAS
                self._registros.append(RegistroAsistencia(ci, valor, motivo))
        return self._registros

    def obtener_dias_trabajados(self, contrato, anio, mes):
        for registro in self.registros():
            if registro.ci == contrato.empleado_id and registro.motivo is None:
                return registro.dias
        return None
