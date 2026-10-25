# Prompt — C2 Administración y reportes (A18) · rama `c2/administracion` · responsable: Quina

Lee `AGENTS.md` y `docs/`. Trabaja **solo** en `apps/administracion/` y `apps/reportes/`. No cambies modelos.

## Alcance
- **CU-12** (RF-23, RF-31): crear usuario y asignar rol y nivel; desactivar usuario (nunca borrar); consultar la bitácora con filtros. `receivers.py`: desactivar la cuenta al recibir `contrato_retirado`.
- **CU-13** (RF-22, RF-30): parámetros por gestión, haber básico por categoría y feriados (nacionales y departamentales). Al guardar, invalidar la caché de `apps.core.parametros`.
- **CU-14** (RF-24, RF-25): horario del respaldo; tarea de respaldo (mysqldump comprimido + SHA-256 + SFTP + correo); restaurar creando antes un respaldo del estado actual; importar personal desde Excel/CSV con validaciones.
- **CU-15** (RF-26): los cinco reportes de la Tabla de reportes del informe (Kardex y contratos, planilla, control de afiliaciones, vacaciones y lactancias, finiquitos y evaluaciones), con vista previa y exportación a PDF y Excel, logo, fecha, usuario y numeración; cada actor ve solo los de su proceso.

## Pruebas obligatorias
Criterios de aceptación de RF-22 a RF-27, RF-30 y RF-31; prueba de permisos por nivel (RNF-07).
