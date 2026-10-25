# Prompt — C1 Seguro de Salud CPS (A13) · rama `c1-cps` · responsable: Rivera

Lee `AGENTS.md` y `docs/`. Trabaja **solo** en `apps/cps/`. No cambies modelos.

## Alcance
- **CU-04 Gestionar afiliación / desafiliación CPS** (RF-06 a RF-09), según la especificación de Larman en `docs/03`:
  - `receivers.py`: al recibir `contrato_registrado`, crear AFILIACION CPS PENDIENTE con FechaLimite = inicio + PLAZO_AFIL días hábiles (el día de inicio cuenta como día 1); al recibir `contrato_retirado`, calcular FechaLimBaja con PLAZO_BAJA.
  - Bandeja de control con semáforo (en plazo, próxima a vencer, vencida), filtros y actualización con HTMX.
  - Aviso de afiliación (parte de ingreso) en PDF con WeasyPrint; tipo NUEVO o REINGRESO (reingreso exige desafiliación anterior).
  - Registro de matrícula (única por contrato vigente) y fecha → estado EN PLAZO o FUERA DE PLAZO.
  - Aviso de baja → DESAFILIADO. Historial de movimientos por trabajador.
- Tarea programada diaria que actualiza el semáforo (RF-07, RF-08).
- Mientras Kardex no esté unido a `main`, prueba con contratos creados por `factory_boy` y emitiendo la señal en la prueba.

## Pruebas obligatorias
CP-01 de `docs/07` y los criterios de aceptación de RF-06 a RF-09.

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
