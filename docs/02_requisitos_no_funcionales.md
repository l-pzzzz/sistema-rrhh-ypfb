# Requisitos no funcionales

Fuente: Informe final, punto 3.2 (ISO/IEC 25010).

| ID | Característica | Requisito | Criterio de verificación |
|---|---|---|---|
| RNF-01 | Usabilidad | Interfaz web en español con diseño responsivo. | Se visualiza correctamente en pantallas desde 1366×768. |
| RNF-02 | Usabilidad | Validación de datos en los formularios con mensajes claros. | Cada campo obligatorio indica el error antes de guardar. |
| RNF-03 | Eficiencia | Tiempo de respuesta de las consultas y búsquedas. | Menor a 3 segundos con 2.500 empleados registrados. |
| RNF-04 | Eficiencia | Tiempo de procesamiento de la planilla mensual. | Menor a 5 minutos para 2.500 empleados. |
| RNF-05 | Seguridad | Comunicación cifrada entre el navegador y el servidor. | Uso de HTTPS con TLS 1.2 o superior. |
| RNF-06 | Seguridad | Almacenamiento seguro de contraseñas. | Contraseñas cifradas con BCrypt (hasher de Django). |
| RNF-07 | Seguridad | Control de acceso por niveles. | Tres niveles (Tabla "Niveles de acceso"): Administrador, Operador y Consulta. Cada usuario ve en el menú solo lo que su nivel y su rol permiten; un acceso denegado responde con el error 403 y queda en la bitácora. |
| RNF-08 | Seguridad | Cierre automático de sesión. | Tras 15 minutos de inactividad. |
| RNF-09 | Seguridad | Registro inalterable de las operaciones. | Toda alta, baja, modificación, inicio de sesión fallido y bloqueo queda en la bitácora con usuario, fecha, IP y, en tablas críticas, valor anterior y nuevo; ningún rol puede modificarla. |
| RNF-10 | Fiabilidad | Disponibilidad del sistema. | Mínimo 99 % en horario hábil. |
| RNF-11 | Fiabilidad | Recuperación ante fallas. | Pérdida máxima de datos de 24 horas y restauración en menos de 4 horas. |
| RNF-12 | Fiabilidad | Integridad de las transacciones. | Gestor de base de datos con propiedades ACID. |
| RNF-13 | Mantenibilidad | Arquitectura en capas (presentación, negocio y datos). | Separación por capas y por aplicaciones de Django en el código fuente. |
| RNF-14 | Mantenibilidad | Modelo de datos normalizado. | Tercera forma normal (3FN), con redundancia controlada solo en documentos históricos. |
| RNF-15 | Portabilidad | Servidor portable mediante contenedores. | Se ejecuta en Ubuntu Server con Docker y en cualquier sistema operativo que ejecute Docker. |
| RNF-16 | Portabilidad | Cliente multiplataforma. | Solo requiere un navegador (Chrome, Firefox o Edge). |
| RNF-17 | Compatibilidad | Exportación de documentos. | Boletas, planillas y reportes en PDF y Excel. |
| RNF-18 | Adecuación funcional | Exactitud de los cálculos monetarios. | Importes en DECIMAL con 2 decimales y redondeo al centavo; los resultados coinciden con un cálculo de referencia en el 100 % de los casos de prueba. |
| RNF-19 | Mantenibilidad | Reglas legales configurables. | Un cambio de salario mínimo, porcentaje o plazo se aplica desde la gestión correspondiente sin recompilar el sistema. |
| RNF-20 | Fiabilidad | Respaldos automáticos (backups) de la base de datos. | Respaldo completo diario a las 23:00, comprimido, verificado con SHA-256 y copiado a un servidor distinto; se conservan 30 días y se prueba una restauración al mes. |

## Niveles de acceso (RNF-07)

| Nivel | Quién lo tiene | Qué puede hacer | Qué no puede hacer |
|---|---|---|---|
| 1. Administrador | Administrador del Sistema | Crear y desactivar usuarios, asignar nivel y rol, configurar parámetros y feriados, programar y restaurar respaldos, consultar la bitácora. | Registrar, actualizar o corregir uno a uno datos de empleados, planillas o afiliaciones (separación de funciones); su única carga de personal es la migración inicial (CU-14). |
| 2. Operador | Afiliador, Encargado de Pagos, Responsable de Vacaciones y Lactancias | Registrar, actualizar, corregir y consultar los datos de su propio módulo; generar sus reportes. | Entrar a los módulos de otro operador, cambiar parámetros, borrar registros o modificar la bitácora. |
| 3. Consulta | Gerencia u otros usuarios autorizados (actor Usuario RRHH) | Iniciar sesión, consultar fichas y generar reportes de solo lectura. | Registrar, actualizar o corregir cualquier dato. |
