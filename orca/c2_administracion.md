# Prompt — C2 Administración y reportes (A18) · rama `c2/administracion` · responsable: Quina

Lee `AGENTS.md` y `docs/`. Trabaja **solo** en `apps/administracion/` y `apps/reportes/`. No cambies modelos.

## Alcance
- **CU-12** (RF-23, RF-31): crear usuario y asignar rol y nivel; desactivar usuario (nunca borrar); consultar la bitácora con filtros. `receivers.py`: desactivar la cuenta al recibir `contrato_retirado`.
- **CU-13** (RF-22, RF-30): parámetros por gestión, haber básico por categoría y feriados (nacionales y departamentales). Al guardar, invalidar la caché de `apps.core.parametros`.
- **CU-14** (RF-24, RF-25): horario del respaldo; tarea de respaldo (mysqldump comprimido + SHA-256 + SFTP + correo); restaurar creando antes un respaldo del estado actual; importar personal desde Excel/CSV con validaciones.
- **CU-15** (RF-26): los cinco reportes de la Tabla de reportes del informe (Kardex y contratos, planilla, control de afiliaciones, vacaciones y lactancias, finiquitos y evaluaciones), con vista previa y exportación a PDF y Excel, logo, fecha, usuario y numeración; cada actor ve solo los de su proceso.

## Pruebas obligatorias
Criterios de aceptación de RF-22 a RF-27, RF-30 y RF-31; prueba de permisos por nivel (RNF-07).

## Reglas comunes de esta iteración
- Antes de empezar: `git pull --rebase origin main`. Lee `AGENTS.md`, `docs/` completo y este archivo.
- Usa los servicios de la base: `from apps.core.parametros import parametros`, `CalendarioLaboral` / funciones de `apps.core.calendario`, `apps.core.auditoria.registrar(...)` (con motivo en ACTUALIZACION y CORRECCION), `@requiere_nivel(...)` de `apps.core.permisos` y las fábricas de `apps/core/tests/fabricas.py`.
- Las clases de los patrones usan los nombres de `docs/06` (iguales a los diagramas del informe).
- Expón la URL `<app>:inicio`, que el menú de la plantilla base ya enlaza.
- Pruebas aisladas de los otros agentes (no uses los puertos publicados):
  `docker compose -p rrhh-<app> -f docker-compose.yml run --rm web pytest`
- Primero muéstrame tu plan (pantallas, servicios, pruebas y filas de `docs/09` que vas a completar) y espera mi aprobación.
- Al terminar: actualiza tus filas de `docs/09_trazabilidad_codigo.md`, verifica la definición de terminado de `AGENTS.md` §8 y abre el PR hacia `main`.
