"""RF-06 y RF-09: aviso de afiliación, matrícula, baja, correcciones e historial."""

import pytest

from apps.administracion.models import Bitacora
from apps.core.tests.fabricas import ContratoFactory
from apps.cps import services
from apps.cps.models import AfiliacionCPS

from .conftest import fecha, nuevo_contrato, registrar, retirar

pytestmark = pytest.mark.django_db
Estado = AfiliacionCPS.Estado


@pytest.fixture
def afil():
    contrato = nuevo_contrato("23/10/2026")
    contrato.empleado.direccion = "Av. Siempre Viva 123"
    contrato.empleado.save()
    return registrar(contrato)


def test_registro_en_plazo_y_fuera_de_plazo():
    en_plazo = services.registrar_afiliacion(registrar(nuevo_contrato("23/10/2026")), "A-1", fecha("30/10/2026"))
    tarde = services.registrar_afiliacion(registrar(nuevo_contrato("23/10/2026")), "A-2", fecha("02/11/2026"))
    assert en_plazo.estado == Estado.EN_PLAZO
    assert tarde.estado == Estado.FUERA_DE_PLAZO  # el registro tardío no se bloquea
    assert Bitacora.objects.filter(tabla="afiliacion_cps", operacion="ACTUALIZACION").count() == 2


def test_rf06_sin_contrato_vigente():
    contrato = nuevo_contrato("05/10/2026")
    registrar(contrato)
    afil = retirar(contrato, "09/10/2026")
    with pytest.raises(services.AfiliacionRechazada, match="El empleado no tiene un contrato vigente"):
        services.registrar_afiliacion(afil, "A-3", fecha("08/10/2026"))
    with pytest.raises(services.AfiliacionRechazada, match="El empleado no tiene un contrato vigente"):
        services.generar_aviso(afil, AfiliacionCPS.Tipo.NUEVO)


def test_matricula_unica_por_contrato_vigente(afil):
    services.registrar_afiliacion(afil, "A-4", fecha("26/10/2026"))
    otra = registrar(nuevo_contrato("23/10/2026"))
    with pytest.raises(services.AfiliacionRechazada, match=f"contrato {afil.contrato_id}"):
        services.registrar_afiliacion(otra, "A-4", fecha("26/10/2026"))


def test_matricula_de_un_contrato_concluido_se_puede_reutilizar():
    viejo = nuevo_contrato("05/01/2026")
    services.registrar_afiliacion(registrar(viejo), "A-5", fecha("06/01/2026"))
    retirar(viejo, "30/04/2026")
    nuevo = registrar(nuevo_contrato("01/09/2026", empleado=viejo.empleado))
    assert services.registrar_afiliacion(nuevo, "A-5", fecha("02/09/2026")).matricula == "A-5"


def test_reingreso_exige_desafiliacion_anterior(afil):
    with pytest.raises(services.AfiliacionRechazada, match="desafiliación anterior"):
        services.generar_aviso(afil, AfiliacionCPS.Tipo.REINGRESO)


def test_aviso_en_pdf(afil):
    assert services.generar_aviso(afil, AfiliacionCPS.Tipo.NUEVO).startswith(b"%PDF")


def test_aviso_con_datos_faltantes_lista_los_campos():
    afil = registrar(nuevo_contrato("23/10/2026"))  # el empleado de la fábrica no tiene domicilio
    with pytest.raises(services.AvisoIncompleto) as error:
        services.generar_aviso(afil, AfiliacionCPS.Tipo.NUEVO)
    assert "Domicilio" in error.value.faltantes


def test_rf08_baja_deja_desafiliado(afil):
    services.registrar_afiliacion(afil, "A-6", fecha("26/10/2026"))
    baja = services.registrar_baja(retirar(afil.contrato, "30/10/2026"), fecha("04/11/2026"))
    assert (baja.estado, baja.fecha_desafil) == (Estado.DESAFILIADO, fecha("04/11/2026"))
    assert Bitacora.objects.filter(tabla="afiliacion_cps", operacion="BAJA").count() == 1


def test_baja_exige_contrato_retirado(afil):
    services.registrar_afiliacion(afil, "A-7", fecha("26/10/2026"))
    with pytest.raises(services.AfiliacionRechazada):
        services.registrar_baja(afil, fecha("04/11/2026"))


def test_rf09_correccion_exige_motivo_y_queda_en_bitacora(afil):
    services.registrar_afiliacion(afil, "A-8", fecha("26/10/2026"))
    with pytest.raises(services.AfiliacionRechazada, match="motivo"):
        services.corregir(afil, "CORRECCION", " ", matricula="A-9")
    afil = services.corregir(afil, "CORRECCION", "Error de digitación", matricula="A-9", fecha_afil=fecha("03/11/2026"))
    assert (afil.matricula, afil.estado) == ("A-9", Estado.FUERA_DE_PLAZO)  # el estado se recalcula
    registro = Bitacora.objects.get(operacion="CORRECCION", tabla="afiliacion_cps")
    assert registro.motivo == "Error de digitación"
    assert "A-8" in registro.valor_ant
    assert "A-9" in registro.valor_nuevo


def test_rf09_historial_con_reingreso():
    primero = nuevo_contrato("05/01/2026")
    services.registrar_afiliacion(registrar(primero), "H-1", fecha("06/01/2026"))
    services.registrar_baja(retirar(primero, "30/04/2026"), fecha("05/05/2026"))
    segundo = nuevo_contrato("01/09/2026", empleado=primero.empleado)
    services.registrar_afiliacion(registrar(segundo), "H-2", fecha("02/09/2026"))

    movimientos = services.historial(primero.empleado)
    altas_y_bajas = [m for m in movimientos if m["etiqueta"] in ("Alta", "Baja")]
    assert [m["etiqueta"] for m in altas_y_bajas] == ["Alta", "Baja", "Alta"]
    assert [m["fecha"] for m in altas_y_bajas] == [fecha("06/01/2026"), fecha("05/05/2026"), fecha("02/09/2026")]
    assert all(m["responsable"] for m in movimientos)


def test_historial_nota_de_contrato_concluido_antes_de_la_afiliacion():
    contrato = nuevo_contrato("05/10/2026")
    registrar(contrato)
    retirar(contrato, "09/10/2026")
    notas = [m for m in services.historial(contrato.empleado) if m["etiqueta"] == "Nota"]
    assert notas[0]["detalle"] == "Contrato concluido antes de la afiliación"


def test_historial_vacio_sin_afiliaciones():
    assert services.historial(ContratoFactory().empleado) == []
