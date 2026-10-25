# Trazabilidad informe → código

Cada PR actualiza las filas de los requisitos que implementa. El integrador no une un PR si sus filas quedan en "Pendiente". Así cada requisito del informe tiene su código y su prueba.

| RF | Requisito (resumen) | CU | App | Archivos (vista / servicio) | Pruebas | Estado |
|---|---|---|---|---|---|---|
| RF-01 | El sistema debe permitir registrar, actualizar, corregir y consultar el Kardex del emplead… | CU-01 | `kardex` | `apps/kardex/views.py` (`empleado_nuevo`, `empleado_editar`, `ficha`) / `apps/kardex/services.py` (`ServicioEmpleado`), `forms.py` (`EmpleadoForm`, `EmpleadoEdicionForm`), `templates/kardex/ficha.html`, `formulario.html` | `apps/kardex/tests/test_empleado.py` (CI repetido, CI con complemento, apellido con valor anterior y nuevo, motivo obligatorio), `test_vistas.py` | Implementado |
| RF-02 | El sistema debe permitir registrar, actualizar, corregir y consultar los contratos fechado… | CU-02 | `kardex` | `apps/kardex/views.py` (`contrato_nuevo`, `contrato_editar`) / `apps/kardex/services.py` (`ServicioContrato.registrar`, `modificar`; emite `contrato_registrado`), `forms.py` (`ContratoForm`, `ContratoEdicionForm`) | `apps/kardex/tests/test_contrato.py` (CO-01, dos cargos → dos CONTRATO CARGO, fechas, motivo), `test_senales.py`, `test_vistas.py` | Implementado |
| RF-03 | El sistema debe asignar automáticamente la categoría según la antigüedad y alertar el camb… | CU-02 | `kardex` | `apps/kardex/services.py` (`ServicioContrato.categoria_por_antiguedad`, `recalcular_categorias`, `alertas_categoria`), `apps/kardex/tasks.py` (`recalcular_categorias`, `PROGRAMACION` diario 01:00), `apps/kardex/views.py` (`inicio`: alertas) | `apps/kardex/tests/test_categoria.py` (CA-01, rangos A/B/C, tarea programada), `test_vistas.py` | Implementado |
| RF-04 | El sistema debe permitir adjuntar, reemplazar y consultar los documentos del empleado y de… | CU-01, CU-03 | `kardex` | `apps/kardex/views.py` (`documento_adjuntar`, `documento_reemplazar`, `documento_ver`) / `apps/kardex/services.py` (`ServicioDocumento`), `forms.py` (`DocumentoForm`, `ReemplazoForm`), `migrations/0003_tipo_documento_ci.py` (CI, TITULO, CERTIFICADO) | `apps/kardex/tests/test_documentos.py` (PDF de 6 MB, solo PDF/JPG/PNG, historial con `Vigente = False`), `test_vistas.py` | Implementado |
| RF-05 | El sistema debe permitir registrar, actualizar, corregir y consultar los dependientes del … | CU-03 | `kardex` | `apps/kardex/views.py` (`dependiente_nuevo`, `dependiente_editar`, `ficha`) / `apps/kardex/services.py` (`ServicioDependiente`, `aviso_afiliacion`), `forms.py` (`DependienteForm`, `DependienteEdicionForm`) | `apps/kardex/tests/test_dependientes.py` ("Ya está registrado como dependiente de …", fotocopia obligatoria, EDAD_MAX_HIJO, aviso de afiliación CPS), `test_vistas.py` | Implementado |
| RF-28 | El sistema debe registrar el retiro del empleado con su fecha, tipo y motivo. | CU-02 | `kardex` | `apps/kardex/views.py` (`contrato_retiro`) / `apps/kardex/services.py` (`ServicioContrato.registrar_retiro`; emite `contrato_retirado`), `forms.py` (`RetiroForm`) | `apps/kardex/tests/test_retiro.py` (CONCLUIDO y RETIRADO, fecha anterior al inicio), `test_senales.py`, `test_vistas.py` | Implementado |
| RF-29 | El sistema debe permitir buscar empleados por CI, código o nombre. | CU-01 | `kardex` | `apps/kardex/views.py` (`inicio`, HTMX) / `apps/kardex/services.py` (`buscar_empleados`), `forms.py` (`BusquedaForm`), `templates/kardex/inicio.html`, `_resultados.html` | `apps/kardex/tests/test_busqueda.py` ("perez" encuentra "Pérez", CI, código, filtros), `test_vistas.py` | Implementado |
| RF-06 | El sistema debe registrar la afiliación del trabajador a la CPS y generar el Aviso de Afil… | CU-04 | `cps` | | | Pendiente |
| RF-07 | El sistema debe controlar el plazo de afiliación desde el inicio laboral y mostrar en una … | CU-04 | `cps` | | | Pendiente |
| RF-08 | El sistema debe alertar la desafiliación pendiente al registrarse el retiro del trabajador… | CU-04 | `cps` | | | Pendiente |
| RF-09 | El sistema debe mantener el historial de afiliaciones y desafiliaciones de cada trabajador… | CU-04 | `cps` | | | Pendiente |
| RF-10 | El sistema debe importar los días trabajados de cada empleado desde el archivo de marcacio… | CU-05 | `planillas` | | | Pendiente |
| RF-11 | El sistema debe calcular la planilla mensual (preplanilla), permitir su revisión y cerrarl… | CU-05 | `planillas` | | | Pendiente |
| RF-12 | El sistema debe aplicar el descuento de AFP según el porcentaje y el umbral parametrizados… | CU-05 | `planillas` | | | Pendiente |
| RF-13 | El sistema debe calcular el RC-IVA separando la base imponible, el impuesto y el crédito f… | CU-05, CU-07 | `planillas` | | | Pendiente |
| RF-14 | El sistema debe permitir registrar el formulario F110 presentado por el trabajador. | CU-07 | `planillas` | | | Pendiente |
| RF-15 | El sistema debe permitir registrar anticipos de sueldo. | CU-06 | `planillas` | | | Pendiente |
| RF-16 | El sistema debe generar la boleta de pago de cada trabajador y la planilla consolidada de … | CU-05 | `planillas` | | | Pendiente |
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
