# Arquitectura

Fuente: Informe final, puntos 3.6.2, 3.9 y 3.10.

## Capas
- **Presentación:** plantillas de Django + Bootstrap 5 + HTMX. No calcula ni accede a la base de datos.
- **Negocio:** una app de Django por módulo; las reglas viven en `services.py`.
- **Servicios de soporte (`apps/core`):** parámetros, calendario laboral, auditoría, notificaciones, tareas programadas, señales del contrato.
- **Datos:** ORM de Django sobre MySQL 8, una sola base `bd_rrhh`.

## Patrones de diseño (dónde se implementan)
| Patrón | Archivo | Qué hace |
|---|---|---|
| Singleton | `apps/core/parametros.py` | Una sola instancia con caché de PARAMETRO por año: `parametros.valor("SMN", anio)`. Se invalida al guardar un parámetro. |
| Facade | `apps/planillas/fachada.py` | `FachadaPlanilla.generar_preplanilla(anio, mes)` y `aprobar_y_cerrar(planilla, usuario)`. |
| Adapter | `apps/planillas/asistencia.py` | `IFuenteAsistencia.obtener_dias_trabajados(contrato, anio, mes)` y `AdaptadorArchivoAsistencia` (pandas). |
| Strategy | `apps/finiquitos/estrategias.py` | `RetiroVoluntario`, `DespidoJustificado`, `DespidoInjustificado`. |
| Observer | `apps/core/senales.py` + `receivers.py` de cada app | `contrato_registrado` y `contrato_retirado`. |

## Contrato de las señales
```python
# apps/core/senales.py
from django.dispatch import Signal
contrato_registrado = Signal()   # kwargs: contrato
contrato_retirado = Signal()     # kwargs: contrato (con FechaRetiro, TipoRetiro y MotivoRetiro ya guardados)
```
| Señal | Quién escucha | Qué hace |
|---|---|---|
| contrato_registrado | cps | Crea AFILIACION CPS en estado PENDIENTE con FechaLimite = inicio + PLAZO_AFIL días hábiles (el día de inicio cuenta como día 1). |
| contrato_retirado | cps | Calcula FechaLimBaja = FechaRetiro + PLAZO_BAJA días hábiles. |
| contrato_retirado | administracion | Desactiva la cuenta de usuario del titular, si existe. |
| contrato_retirado | finiquitos | Habilita el cálculo del finiquito del contrato. |

## Tareas programadas (Celery Beat)
| Tarea | Horario | RF |
|---|---|---|
| Recalcular categoría por antigüedad y alertar | diario 01:00 | RF-03 |
| Actualizar semáforo de plazos CPS | diario 06:00 | RF-07, RF-08 |
| Alertar entregas de lactancia pendientes | diario; alerta cuando faltan 3 días para fin de mes | RF-19 |
| Respaldo mysqldump + SHA-256 + SFTP + correo | según horario del Administrador (por defecto 23:00) | RF-25 |

## Despliegue
Docker Compose: `nginx` (HTTPS), `web` (Gunicorn + Django), `worker` y `beat` (Celery), `redis`, y MySQL 8 en su propio servidor (en desarrollo, un contenedor `db`).
