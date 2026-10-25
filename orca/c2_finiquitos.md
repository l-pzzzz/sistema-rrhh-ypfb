# Prompt — C2 Finiquitos y Evaluaciones (A17) · rama `c2/finiquitos` · responsable: Trujillo

Lee `AGENTS.md` y `docs/`. Trabaja **solo** en `apps/finiquitos/`. No cambies modelos.

## Alcance
- **CU-10 Calcular finiquito** (RF-20) con el patrón Strategy (`estrategias.py`): voluntario (indemnización si más de ANTIG_MIN_INDEM días continuos), despido justificado (sin indemnización ni desahucio), despido injustificado (indemnización + desahucio de 3 sueldos básicos); vacaciones y sueldos devengados; descuento de licencias si la antigüedad es menor a un año. Guarda FINIQUITO y DETALLE FINIQUITO con FechaLimPago (PLAZO_FINIQ). `receivers.py` habilita el finiquito al recibir `contrato_retirado`.
- **CU-11 Registrar evaluación de desempeño** (RF-21): valor de 1 a 5 por trimestre y contrato; acción propuesta (4–5 vale de Bs 1.000; 3 llamada de atención; 1–2 retiro en la primera evaluación); decisión final de la gerencia registrada por el Afiliador.

## Pruebas obligatorias
Criterios de aceptación de RF-20 y RF-21, una prueba por cada estrategia.
