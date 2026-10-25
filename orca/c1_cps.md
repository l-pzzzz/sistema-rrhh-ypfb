# Prompt — C1 Seguro de Salud CPS (A13) · rama `c1/cps` · responsable: Rivera

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
