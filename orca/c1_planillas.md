# Prompt — C1 Planillas de Sueldos (A14) · rama `c1-planillas` · responsable: Trujillo

Lee `AGENTS.md` y `docs/`. Trabaja **solo** en `apps/planillas/`. No cambies modelos.

## Alcance
- **CU-05 Procesar planilla** (RF-10, RF-11, RF-12, RF-13, RF-16), según la especificación de Larman en `docs/03` y las reglas RN-01 a RN-08 de `docs/04`:
  - `asistencia.py` (Adapter): importar el archivo de marcaciones (Excel/CSV), días 0 a 30, listar inconsistencias.
  - `fachada.py` (Facade): preplanilla por **contrato vigente**: sueldo ganado, otros ingresos, anticipos, AFP y RC-IVA con F110 y saldo a favor; aprobar y cerrar (registra AprobadoPor), generar BOLETA PAGO y DETALLE BOLETA (base y porcentaje aplicados), marcar anticipos descontados. Una planilla cerrada no se modifica.
  - Exportar planilla consolidada y boletas en PDF y Excel.
- **CU-06 Registrar anticipo** (RF-15): solo después del día 15; tope 50 % del haber básico de la categoría en el mes.
- **CU-07 Registrar F110** (RF-13, RF-14): crédito = 13 % (PORC_IVA) de las facturas; presentado después del día 15 → se aplica al mes siguiente.
- Todos los porcentajes y montos legales desde `apps.core.parametros`; dinero con `Decimal`.

## Pruebas obligatorias
PL-01, PL-02, PL-03, AN-01 y AN-02 de `docs/07` **con los valores exactos** (por ejemplo, PL-01 → líquido Bs 5.605,74). Prueba de rendimiento: 2.500 contratos en menos de 5 minutos (RNF-04).

## Entrega
PR hacia `main` con CU/RF, pruebas y dudas.

## Reglas comunes de esta iteración
- Antes de empezar: `git pull --rebase origin main`. Lee `AGENTS.md` completo, este archivo y solo las secciones de `docs/` de tus CU y RF (AGENTS.md §10).
- Usa los servicios de la base: `from apps.core.parametros import parametros`, `CalendarioLaboral` / funciones de `apps.core.calendario`, `apps.core.auditoria.registrar(...)` (con motivo en ACTUALIZACION y CORRECCION), `@requiere_nivel(...)` de `apps.core.permisos` y las fábricas de `apps/core/tests/fabricas.py`.
- Las clases de los patrones usan los nombres de `docs/06` (iguales a los diagramas del informe).
- Expón la URL `<app>:inicio`, que el menú de la plantilla base ya enlaza.
- Pruebas aisladas de los otros agentes (no uses los puertos publicados):
  `docker compose -p rrhh-<app> -f docker-compose.yml run --rm web pytest`
- Primero muéstrame tu plan (pantallas, servicios, pruebas y filas de `docs/09` que vas a completar) y espera mi aprobación.
- Al terminar: actualiza tus filas de `docs/09_trazabilidad_codigo.md`, verifica la definición de terminado de `AGENTS.md` §8 y abre el PR hacia `main`.
