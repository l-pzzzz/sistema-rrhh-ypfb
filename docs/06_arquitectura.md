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

## Nombres de clases obligatorios (deben coincidir con los diagramas de patrones del informe, 3.6.2)
| Clase del informe | Dónde va | Nota |
|---|---|---|
| `ParametrosSistema` | `apps/core/parametros.py` | Singleton; la instancia del módulo se llama `parametros`. |
| `CalendarioLaboral` | `apps/core/calendario.py` | Agrupa `sumar_dias_habiles`, `dias_habiles_entre` y `es_dia_habil`. |
| `ServicioContrato` | `apps/kardex/services.py` | Sujeto del Observer: registra contratos y retiros y emite las señales. |
| `ObservadorContrato`, `EventoContrato` | `apps/core/senales.py` | Interfaz de los receptores y datos del evento (contrato y tipo). |
| `ControlPlazosCPS` | `apps/cps/receivers.py` | Observador: fechas límite de afiliación y baja. |
| `DesactivadorCuenta` | `apps/administracion/receivers.py` | Observador: desactiva la cuenta del titular. |
| `HabilitadorFiniquito` | `apps/finiquitos/receivers.py` | Observador: habilita el finiquito. |
| `FachadaPlanilla`, `ControladorPlanilla`, `CalculadoraDescuentos`, `GeneradorBoletas`, `ServicioAnticipos`, `ServicioF110` | `apps/planillas/` | Facade de la planilla. |
| `IFuenteAsistencia`, `AdaptadorArchivoAsistencia`, `ArchivoMarcacionesCSV` | `apps/planillas/asistencia.py` | Adapter. |
| `ServicioFiniquito`, `EstrategiaFiniquito`, `RetiroVoluntario`, `DespidoJustificado`, `DespidoInjustificado` | `apps/finiquitos/` | Strategy. |

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
| contrato_retirado | cps | Calcula FechaLimBaja = FechaRetiro + PLAZO_BAJA días hábiles, con el mismo criterio que la afiliación: el día del retiro cuenta como día 1 (`incluye_inicio=True`). |
| contrato_retirado | administracion | Desactiva la cuenta de usuario del titular, si existe. |
| contrato_retirado | finiquitos | Habilita el cálculo del finiquito del contrato. |

## Tareas programadas (Celery Beat)
| Tarea | Horario | RF |
|---|---|---|
| Recalcular categoría por antigüedad y alertar | diario 01:00 | RF-03 |
| Actualizar semáforo de plazos CPS | diario 06:00 | RF-07, RF-08 |
| Alertar entregas de lactancia pendientes | diario; alerta cuando faltan 3 días para fin de mes | RF-19 |
| Respaldo mysqldump + SHA-256 + SFTP + correo | según horario del Administrador (por defecto 23:00) | RF-25 |

## Programación de las tareas (Celery Beat)
Cada app declara sus tareas en `apps/<app>/tasks.py` y un diccionario `PROGRAMACION` con su horario. Los agentes de módulo **no** tocan `config/`: el integrador une esos diccionarios en `CELERY_BEAT_SCHEDULE` durante la integración (A15 y A19).

## Alertas a los operadores
Según el diagrama de despliegue (3.10.1, Servidor de Correo), las alertas de plazos de la CPS y de lactancia se muestran en la bandeja de cada módulo **y** se envían por correo (SMTP, `django.core.mail`) a los usuarios activos del rol que corresponde. El resumen del respaldo va al Administrador. No hay tabla de notificaciones: el historial de cada alerta queda en BITACORA cuando cambia un dato.

## Decisiones de la iteración C1
- Kardex: la antigüedad se cuenta desde EMPLEADO.FechaIngreso; un contrato nuevo de un empleado RETIRADO lo vuelve ACTIVO (reingreso); el tipo de documento "CI" se carga con una migración de datos de kardex.
- CPS: la ubicación para feriados departamentales es la del primer cargo del contrato; si un contrato se retira con la afiliación PENDIENTE (nunca se afilió), la afiliación queda PENDIENTE y sale de la bandeja de altas, con una nota en el historial.
- Correo de las alertas: USUARIO no tiene columna de correo, así que los destinatarios se configuran en `.env`: `CORREO_AFILIADORES` (alertas de CPS y de cambio de categoría), `CORREO_RESP_VACACIONES` (lactancia) y `CORREO_ADMINISTRADOR` (respaldos y parámetros faltantes), cada una con direcciones separadas por comas. Si la variable está vacía, la alerta se muestra solo en pantalla.
- Kardex: los datos académicos del RF-01 se registran como documentos (TIPO DOCUMENTO "TITULO" y "CERTIFICADO", RF-04). La alerta de cambio de categoría se muestra en `kardex:inicio` durante 30 días (cubre la planilla del mes siguiente, que ya usa el haber de la nueva categoría, RF-03 regla 3) y se envía por correo a `CORREO_AFILIADORES`.
- Planillas: los valores del caso que faltaban como parámetros ya son claves de PARAMETRO: UMBRAL_RCIVA, MNI_RCIVA, PORC_ANTICIPO, DIA_ANTICIPO y DIA_F110 (docs/04). Se cargan con una migración de datos de planillas. Si faltan parámetros, el proceso se bloquea en pantalla y se avisa por correo a `CORREO_ADMINISTRADOR` (extensión 2b del CU-05).
- Planillas: la preplanilla se calcula al vuelo y no crea boletas (RF-16: las boletas solo se generan al cerrar). Los "otros ingresos" que el Encargado ingresa por trabajador se guardan como borrador en la caché (Redis), por planilla, hasta el cierre; al cerrar quedan en DETALLE BOLETA (concepto OTROS INGRESOS). El archivo de marcaciones tiene las columnas CI y DiasTrab; un contrato vigente sin marcación es una inconsistencia.

## Despliegue
Docker Compose: `nginx` (HTTPS), `web` (Gunicorn + Django), `worker` y `beat` (Celery), `redis`, y MySQL 8 en su propio servidor (en desarrollo, un contenedor `db`).

Secretos en producción (`SECRET_KEY`, `DB_PASSWORD`, `DB_ROOT_PASSWORD` y `REDIS_PASSWORD`): van en el archivo `.env` del servidor, fuera del repositorio y con permisos solo para el usuario que ejecuta Docker (`chmod 600 .env`). El sistema es académico y no usa un gestor de secretos. En producción se usa solo `docker-compose.yml` (`docker compose -f docker-compose.yml up -d`): MySQL y Redis no se publican fuera de la red de Docker; `docker-compose.override.yml` es solo para desarrollo.
