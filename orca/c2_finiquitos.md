# Prompt — C2 Finiquitos y Evaluaciones (A17) · rama `c2-finiquitos` · responsable: Trujillo

Lee `AGENTS.md` y `docs/`. Trabaja **solo** en `apps/finiquitos/`. No cambies modelos.

## Alcance
- **CU-10 Calcular finiquito** (RF-20) con el patrón Strategy (`estrategias.py`): voluntario (indemnización si más de ANTIG_MIN_INDEM días continuos), despido justificado (sin indemnización ni desahucio), despido injustificado (indemnización + desahucio de 3 sueldos básicos); vacaciones y sueldos devengados; descuento de licencias si la antigüedad es menor a un año. Guarda FINIQUITO y DETALLE FINIQUITO con FechaLimPago (PLAZO_FINIQ). `receivers.py` habilita el finiquito al recibir `contrato_retirado`.
- **CU-11 Registrar evaluación de desempeño** (RF-21): valor de 1 a 5 por trimestre y contrato; acción propuesta (4–5 vale de Bs 1.000; 3 llamada de atención; 1–2 retiro en la primera evaluación); decisión final de la gerencia registrada por el Afiliador.

## Pruebas obligatorias
Criterios de aceptación de RF-20 y RF-21, una prueba por cada estrategia.

## Reglas comunes de esta iteración
- Antes de empezar: `git pull --rebase origin main`. Lee `AGENTS.md`, `docs/` completo y este archivo.
- Usa los servicios de la base: `from apps.core.parametros import parametros`, `CalendarioLaboral` / funciones de `apps.core.calendario`, `apps.core.auditoria.registrar(...)` (con motivo en ACTUALIZACION y CORRECCION), `@requiere_nivel(...)` de `apps.core.permisos` y las fábricas de `apps/core/tests/fabricas.py`.
- Las clases de los patrones usan los nombres de `docs/06` (iguales a los diagramas del informe).
- Expón la URL `<app>:inicio`, que el menú de la plantilla base ya enlaza.
- Pruebas aisladas de los otros agentes (no uses los puertos publicados):
  `docker compose -p rrhh-<app> -f docker-compose.yml run --rm web pytest`
- Primero muéstrame tu plan (pantallas, servicios, pruebas y filas de `docs/09` que vas a completar) y espera mi aprobación.
- Al terminar: actualiza tus filas de `docs/09_trazabilidad_codigo.md`, verifica la definición de terminado de `AGENTS.md` §8 y abre el PR hacia `main`.
