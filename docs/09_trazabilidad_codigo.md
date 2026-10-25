# Trazabilidad informe → código

Cada PR actualiza las filas de los requisitos que implementa. El integrador no une un PR si sus filas quedan en "Pendiente". Así cada requisito del informe tiene su código y su prueba.

| RF | Requisito (resumen) | CU | App | Archivos (vista / servicio) | Pruebas | Estado |
|---|---|---|---|---|---|---|
| RF-01 | El sistema debe permitir registrar, actualizar, corregir y consultar el Kardex del emplead… | CU-01 | `kardex` | | | Pendiente |
| RF-02 | El sistema debe permitir registrar, actualizar, corregir y consultar los contratos fechado… | CU-02 | `kardex` | | | Pendiente |
| RF-03 | El sistema debe asignar automáticamente la categoría según la antigüedad y alertar el camb… | CU-02 | `kardex` | | | Pendiente |
| RF-04 | El sistema debe permitir adjuntar, reemplazar y consultar los documentos del empleado y de… | CU-01, CU-03 | `kardex` | | | Pendiente |
| RF-05 | El sistema debe permitir registrar, actualizar, corregir y consultar los dependientes del … | CU-03 | `kardex` | | | Pendiente |
| RF-28 | El sistema debe registrar el retiro del empleado con su fecha, tipo y motivo. | CU-02 | `kardex` | | | Pendiente |
| RF-29 | El sistema debe permitir buscar empleados por CI, código o nombre. | CU-01 | `kardex` | | | Pendiente |
| RF-06 | El sistema debe registrar la afiliación del trabajador a la CPS y generar el Aviso de Afil… | CU-04 | `cps` | | | Pendiente |
| RF-07 | El sistema debe controlar el plazo de afiliación desde el inicio laboral y mostrar en una … | CU-04 | `cps` | | | Pendiente |
| RF-08 | El sistema debe alertar la desafiliación pendiente al registrarse el retiro del trabajador… | CU-04 | `cps` | | | Pendiente |
| RF-09 | El sistema debe mantener el historial de afiliaciones y desafiliaciones de cada trabajador… | CU-04 | `cps` | | | Pendiente |
| RF-10 | El sistema debe importar los días trabajados de cada empleado desde el archivo de marcacio… | CU-05 | `planillas` | `apps/planillas/asistencia.py` (`IFuenteAsistencia`, `ArchivoMarcacionesCSV`, `AdaptadorArchivoAsistencia`) / `fachada.py` (`FachadaPlanilla.importar_asistencia`), `views.py` (`procesar`) | `tests/test_asistencia.py` | Implementado |
| RF-11 | El sistema debe calcular la planilla mensual (preplanilla), permitir su revisión y cerrarl… | CU-05 | `planillas` | `apps/planillas/fachada.py` (`FachadaPlanilla`, `ControladorPlanilla`, `CalculadoraDescuentos`) / `views.py` (`preplanilla`, `detalle`), `templates/planillas/` | `tests/test_calculadora.py`, `test_fachada.py`, `test_vistas.py`, `test_rendimiento.py` (RNF-04) | Implementado |
| RF-12 | El sistema debe aplicar el descuento de AFP según el porcentaje y el umbral parametrizados… | CU-05 | `planillas` | `apps/planillas/fachada.py` (`CalculadoraDescuentos`) | `tests/test_calculadora.py`, `test_casos_aceptacion.py` (PL-01, PL-03) | Implementado |
| RF-13 | El sistema debe calcular el RC-IVA separando la base imponible, el impuesto y el crédito f… | CU-05, CU-07 | `planillas` | `apps/planillas/fachada.py` (`CalculadoraDescuentos`) / `services.py` (`ServicioF110.credito`) | `tests/test_calculadora.py`, `test_casos_aceptacion.py` (PL-01 a PL-03), `test_fachada.py` | Implementado |
| RF-14 | El sistema debe permitir registrar el formulario F110 presentado por el trabajador. | CU-07 | `planillas` | `apps/planillas/services.py` (`ServicioF110`) / `views.py` (`f110`), `forms.py` (`F110Form`) | `tests/test_anticipos_f110.py` | Implementado |
| RF-15 | El sistema debe permitir registrar anticipos de sueldo. | CU-06 | `planillas` | `apps/planillas/services.py` (`ServicioAnticipos`) / `views.py` (`anticipos`), `forms.py` (`AnticipoForm`) | `tests/test_anticipos_f110.py`, `test_casos_aceptacion.py` (AN-01, AN-02) | Implementado |
| RF-16 | El sistema debe generar la boleta de pago de cada trabajador y la planilla consolidada de … | CU-05 | `planillas` | `apps/planillas/fachada.py` (`GeneradorBoletas`, `aprobar_y_cerrar`) / `exportacion.py`, `views.py` (`boleta`, `exportar_planilla`, `exportar_boleta`) | `tests/test_fachada.py`, `test_exportacion.py` | Implementado |
| RF-17 | El sistema debe registrar las solicitudes de vacaciones y licencias firmadas por el jefe i… | CU-08 | `vacaciones` | | | Pendiente |
| RF-18 | El sistema debe calcular el saldo de vacaciones en días hábiles según la antigüedad y desc… | CU-08 | `vacaciones` | | | Pendiente |
| RF-19 | El sistema debe registrar las entregas mensuales del subsidio de lactancia a la beneficiar… | CU-09 | `vacaciones` | | | Pendiente |
| RF-20 | El sistema debe calcular el finiquito según el tipo de retiro, detallando cada concepto. | CU-10 | `finiquitos` | | | Pendiente |
| RF-21 | El sistema debe registrar la evaluación trimestral de desempeño y proponer la acción que c… | CU-11 | `finiquitos` | | | Pendiente |
| RF-22 | El sistema debe permitir parametrizar por gestión las variables salariales, tributarias y … | CU-13 | `administracion` | | | Pendiente |
| RF-23 | El sistema debe permitir gestionar usuarios, roles y permisos. | CU-12 | `administracion` | | | Pendiente |
| RF-24 | El sistema debe permitir migrar los datos del personal activo desde archivos Excel o CSV. | CU-14 | `administracion` | | | Pendiente |
| RF-25 | El sistema debe permitir programar, verificar y restaurar los respaldos de la base de dato… | CU-14 | `administracion` | | | Pendiente |
| RF-26 | El sistema debe generar reportes parametrizados exportables a PDF y Excel. | CU-15 | `reportes` | | | Pendiente |
| RF-27 | El sistema debe autenticar a los usuarios mediante usuario y contraseña. | CU-16 | `administracion` | `apps/administracion/views.py` (`InicioSesionView`, `CierreSesionView`) / `apps/administracion/services.py` (`autenticar`), `forms.py` (`InicioSesionForm`), `backends.py`, `models.py` (`Usuario`: BCrypt, `Intentos`, `BloqHasta`), `templates/administracion/login.html` | `apps/administracion/tests/test_inicio_sesion.py` (bloqueo de 3 intentos por 15 minutos, cuenta inactiva, bitácora de LOGIN FALLIDO y BLOQUEO, sesión de 15 minutos) | Implementado |
| RF-30 | El sistema debe permitir registrar los feriados de cada gestión para el cálculo de días há… | CU-13 | `administracion` | | | Pendiente |
| RF-31 | El sistema debe permitir consultar la bitácora de auditoría. | CU-12 | `administracion` | | | Pendiente |

Estado: Pendiente · En curso · Implementado (con prueba que pasa).

La fila de RF-27 (CU-16 Iniciar sesión) se completa en la fase base.
