"""CU-05 Exportar planilla consolidada y boletas a PDF y Excel (RF-16, RNF-17)."""

import io
from decimal import Decimal

import openpyxl
from django.template.loader import render_to_string
from django.utils import timezone

from .models import DetalleBoleta

C = DetalleBoleta.Concepto
CERO = Decimal("0.00")
ENCABEZADOS = ["CI", "Trabajador", "Días", "Sueldo ganado", "Otros ingresos", "Total ingresos", "Anticipos",
               "AFP", "RC-IVA", "Total descuentos", "Líquido"]
CONTENIDO = {"xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
             "pdf": "application/pdf"}


def filas_planilla(planilla):
    """Una fila por boleta de la planilla cerrada, con los importes guardados (fotografía histórica)."""
    boletas = planilla.boletas.select_related("contrato__empleado").prefetch_related("detalles").order_by("nro")
    filas = []
    for b in boletas:
        m = {d.concepto: d.monto for d in b.detalles.all()}
        e = b.contrato.empleado
        filas.append([e.ci, f"{e.apellidos} {e.nombres}", b.dias_trab, m.get(C.SUELDO_GANADO, CERO),
                      m.get(C.OTROS_INGRESOS, CERO), b.tot_ingresos, m.get(C.ANTICIPO, CERO), m.get(C.AFP, CERO),
                      m.get(C.RC_IVA, CERO), b.tot_descuentos, b.liquido])
    return filas


def _excel(titulo, encabezados, filas):
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = titulo[:31]
    hoja.append([titulo])
    hoja.append([f"Generado el {timezone.localtime():%d/%m/%Y %H:%M}"])
    hoja.append(encabezados)
    for fila in filas:
        hoja.append([float(v) if isinstance(v, Decimal) else v for v in fila])
    for celdas in hoja.iter_rows(min_row=4):
        for celda in celdas:
            if isinstance(celda.value, float):
                celda.number_format = "#,##0.00"
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


def _pdf(plantilla, contexto):
    from weasyprint import HTML

    return HTML(string=render_to_string(plantilla, contexto)).write_pdf()


def planilla_excel(planilla):
    return _excel(f"Planilla {planilla.mes:02d}-{planilla.gestion_id}", ENCABEZADOS, filas_planilla(planilla))


def planilla_pdf(planilla):
    filas = filas_planilla(planilla)
    totales = [sum((f[i] for f in filas), CERO) for i in range(3, 11)]
    return _pdf("planillas/pdf_planilla.html", {"planilla": planilla, "encabezados": ENCABEZADOS, "filas": filas,
                                                "totales": totales, "ahora": timezone.localtime()})


def conceptos_boleta(boleta):
    return list(boleta.detalles.order_by("concepto"))


def boleta_excel(boleta):
    filas = [[d.concepto, d.base, d.porcentaje, d.monto] for d in conceptos_boleta(boleta)]
    filas += [["TOTAL INGRESOS", None, None, boleta.tot_ingresos],
              ["TOTAL DESCUENTOS", None, None, boleta.tot_descuentos], ["LÍQUIDO PAGABLE", None, None, boleta.liquido]]
    return _excel(f"Boleta {boleta.nro}", ["Concepto", "Base", "Porcentaje", "Monto"], filas)


def boleta_pdf(boleta):
    return _pdf("planillas/pdf_boleta.html", {"boleta": boleta, "detalles": conceptos_boleta(boleta),
                                              "ahora": timezone.localtime()})
