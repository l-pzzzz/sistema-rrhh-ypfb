# Prompt — C2 Vacaciones y Lactancias (A16) · rama `c2-vacaciones` · responsable: Rivera

Lee `AGENTS.md` y `docs/`. Trabaja **solo** en `apps/vacaciones/`. No cambies modelos.

## Alcance
- **CU-08 Gestionar vacaciones y licencias** (RF-17, RF-18): solicitud firmada por el jefe inmediato; días hábiles con `apps.core.calendario`; licencias con un día de anticipación y canje a cuenta de vacaciones; saldo según antigüedad (15, 20 o 30 días hábiles); rechazo si el saldo no alcanza.
- **CU-09 Controlar entregas de lactancia** (RF-19): beneficiaria e hijo registrados como dependientes; máximo 12 entregas por hijo; entregas pendientes del mes; tarea programada que alerta cuando faltan 3 días para fin de mes.

## Pruebas obligatorias
Criterios de aceptación de RF-17 a RF-19.

## Reglas comunes de esta iteración
- Antes de empezar: `git pull --rebase origin main`. Lee `AGENTS.md`, `docs/` completo y este archivo.
- Usa los servicios de la base: `from apps.core.parametros import parametros`, `CalendarioLaboral` / funciones de `apps.core.calendario`, `apps.core.auditoria.registrar(...)` (con motivo en ACTUALIZACION y CORRECCION), `@requiere_nivel(...)` de `apps.core.permisos` y las fábricas de `apps/core/tests/fabricas.py`.
- Las clases de los patrones usan los nombres de `docs/06` (iguales a los diagramas del informe).
- Expón la URL `<app>:inicio`, que el menú de la plantilla base ya enlaza.
- Pruebas aisladas de los otros agentes (no uses los puertos publicados):
  `docker compose -p rrhh-<app> -f docker-compose.yml run --rm web pytest`
- Primero muéstrame tu plan (pantallas, servicios, pruebas y filas de `docs/09` que vas a completar) y espera mi aprobación.
- Al terminar: actualiza tus filas de `docs/09_trazabilidad_codigo.md`, verifica la definición de terminado de `AGENTS.md` §8 y abre el PR hacia `main`.
