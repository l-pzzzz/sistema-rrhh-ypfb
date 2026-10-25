# Prompt — C1 Kardex y Contratos (A12) · rama `c1/kardex` · responsable: Quina

Lee `AGENTS.md` y `docs/`. Trabaja **solo** en `apps/kardex/`. Los modelos ya existen: no cambies campos ni crees migraciones de esquema.

## Alcance
- **CU-01 Gestionar Kardex** (RF-01, RF-04, RF-29): buscar empleado (CI, código o nombre, sin distinguir mayúsculas ni tildes); registrar; actualizar o corregir con motivo; adjuntar o reemplazar documentos (PDF/JPG/PNG hasta 5 MB, la versión anterior queda con `Vigente = False`).
- **CU-02 Gestionar contrato** (RF-02, RF-03, RF-28): registrar contrato con uno o más cargos y categoría por antigüedad; un solo contrato VIGENTE por empleado; actualizar o corregir con motivo; registrar retiro (fecha, tipo, motivo) → contrato CONCLUIDO y empleado RETIRADO.
  Emite `contrato_registrado` al registrar y `contrato_retirado` al registrar el retiro (`apps.core.senales`).
- **CU-03 Gestionar dependientes** (RF-04, RF-05): registrar con fotocopia del CI obligatoria; actualizar o corregir; un dependiente con un solo trabajador (mensaje "Ya está registrado como dependiente de …"); advertencia si un hijo supera EDAD_MAX_HIJO.
- Tarea programada de RF-03: recálculo diario de categoría y alerta al Afiliador.
- Nivel OPERADOR con rol Afiliador; los demás operadores solo consultan.

## Pruebas obligatorias
CA-01 y CO-01 de `docs/07`, más los criterios de aceptación de RF-01 a RF-05, RF-28 y RF-29 de `docs/01`. Verifica que las señales se emiten (con un receptor de prueba).

## Entrega
PR hacia `main` con: CU y RF implementados, pantallas creadas, pruebas y dudas para el equipo.

## Reglas comunes de esta iteración
- Antes de empezar: `git pull --rebase origin main`. Lee `AGENTS.md`, `docs/` completo y este archivo.
- Usa los servicios de la base: `from apps.core.parametros import parametros`, `CalendarioLaboral` / funciones de `apps.core.calendario`, `apps.core.auditoria.registrar(...)` (con motivo en ACTUALIZACION y CORRECCION), `@requiere_nivel(...)` de `apps.core.permisos` y las fábricas de `apps/core/tests/fabricas.py`.
- Las clases de los patrones usan los nombres de `docs/06` (iguales a los diagramas del informe).
- Expón la URL `<app>:inicio`, que el menú de la plantilla base ya enlaza.
- Pruebas aisladas de los otros agentes (no uses los puertos publicados):
  `docker compose -p rrhh-<app> -f docker-compose.yml run --rm web pytest`
- Primero muéstrame tu plan (pantallas, servicios, pruebas y filas de `docs/09` que vas a completar) y espera mi aprobación.
- Al terminar: actualiza tus filas de `docs/09_trazabilidad_codigo.md`, verifica la definición de terminado de `AGENTS.md` §8 y abre el PR hacia `main`.
