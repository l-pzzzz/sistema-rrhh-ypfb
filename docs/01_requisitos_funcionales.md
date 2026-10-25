# Requisitos funcionales

Fuente: Informe final, punto 3.1 (31 requisitos). Cada requisito indica sus datos, reglas, criterio de aceptación, prioridad y caso de uso.

## Módulo de Kardex

### RF-01 — El sistema debe permitir registrar, actualizar, corregir y consultar el Kardex del empleado con sus datos personales, académicos, laborales y de contacto de emergencia.

- **Prioridad:** Alta · **Caso de uso:** CU-01
- **Datos:** CI (con complemento opcional), código, nombres, apellidos, fecha de nacimiento, sexo, datos académicos, contacto de emergencia (nombre, parentesco y teléfono), estado (ACTIVO o RETIRADO).
- **Reglas:**
  - 1. El CI y el código del empleado son únicos.
  - 2. El CI acepta el complemento (por ejemplo, 1234567-1A).
  - 3. Un empleado no se elimina: su retiro cambia el estado a RETIRADO (RF-28).
  - 4. Actualizar es registrar un cambio real (nueva dirección o teléfono); corregir es enmendar un error de registro. Ambos exigen indicar el motivo y quedan en la bitácora con el valor anterior y el nuevo (RF-31).
- **Criterio de aceptación:** Al registrar un CI repetido, el sistema muestra "El CI ya está registrado". Al editar un apellido, la bitácora muestra el valor anterior y el nuevo.

### RF-02 — El sistema debe permitir registrar, actualizar, corregir y consultar los contratos fechados del empleado asociados a uno o varios cargos, con sus funciones y ubicación (departamento).

- **Prioridad:** Alta · **Caso de uso:** CU-02
- **Datos:** Fecha de inicio, fecha de fin (vacía si es indefinido), categoría, cargo o cargos, estado (VIGENTE o CONCLUIDO), motivo de modificación.
- **Reglas:**
  - 1. Un empleado no puede tener dos contratos vigentes al mismo tiempo.
  - 2. Si el contrato tiene fecha de fin, debe ser posterior a la de inicio; un contrato indefinido no tiene fecha de fin.
  - 3. Todo contrato tiene al menos un cargo.
  - 4. Toda actualización (cambio de cargo o renovación) o corrección (error de registro) de un contrato exige registrar el motivo y queda en la bitácora con el valor anterior y el nuevo.
- **Criterio de aceptación:** Al crear un contrato con dos cargos, se guardan dos registros en CONTRATO CARGO. Al intentar un segundo contrato vigente para el mismo empleado, el sistema lo rechaza.

### RF-03 — El sistema debe asignar automáticamente la categoría según la antigüedad y alertar el cambio de categoría.

- **Prioridad:** Alta · **Caso de uso:** CU-02
- **Datos:** Fecha de ingreso, fecha actual, categoría actual.
- **Reglas:**
  - 1. La antigüedad se mide en años cumplidos: A de 0 a 5; B de 6 a 15; C de 16 en adelante (caso).
  - 2. Una tarea programada del sistema recalcula la antigüedad cada día; el cambio se muestra como alerta al Afiliador.
  - 3. Al cambiar la categoría, se actualiza la categoría del contrato vigente (queda en la bitácora), se alerta al Afiliador y la planilla siguiente usa el haber básico de la nueva categoría.
- **Criterio de aceptación:** Un empleado que cumple 6 años de antigüedad aparece al día siguiente con la alerta "Cambio de categoría: A → B".

### RF-04 — El sistema debe permitir adjuntar, reemplazar y consultar los documentos del empleado y de sus dependientes, clasificados por tipo de documento.

- **Prioridad:** Alta · **Caso de uso:** CU-01, CU-03
- **Datos:** Archivo, tipo de documento, persona (empleado o dependiente), fecha de carga.
- **Reglas:**
  - 1. El tamaño máximo es de 5 MB.
  - 2. Solo se aceptan archivos PDF, JPG o PNG.
  - 3. Un documento no se elimina: se reemplaza y la versión anterior queda en el historial.
- **Criterio de aceptación:** Al subir un PDF de 6 MB, el sistema muestra "El archivo supera el tamaño máximo de 5 MB".

### RF-05 — El sistema debe permitir registrar, actualizar, corregir y consultar los dependientes del empleado con su nombre, parentesco y fotocopia del CI.

- **Prioridad:** Alta · **Caso de uso:** CU-03
- **Datos:** CI, nombres, apellidos, fecha de nacimiento, parentesco, fotocopia del CI.
- **Reglas:**
  - 1. Parentesco permitido: cónyuge o conviviente, hijo o hija, padre, madre.
  - 2. La fotocopia del CI es obligatoria (caso).
  - 3. Un dependiente se registra con un solo trabajador; si ya está registrado, el sistema indica con quién.
  - 4. Si un hijo o hija supera la edad máxima de beneficiario (parámetro, RF-22), el sistema muestra una advertencia.
  - 5. Los dependientes se listan en la ficha del empleado.
- **Criterio de aceptación:** Al registrar como dependiente a un hijo que ya figura con su madre (también empleada), el sistema muestra "Ya está registrado como dependiente de [nombre]".

### RF-28 — El sistema debe registrar el retiro del empleado con su fecha, tipo y motivo.

- **Prioridad:** Alta · **Caso de uso:** CU-02
- **Datos:** Fecha de retiro, tipo de retiro (VOLUNTARIO, DESPIDO JUSTIFICADO o DESPIDO INJUSTIFICADO), motivo.
- **Reglas:**
  - 1. El empleado pasa al estado RETIRADO y su contrato a CONCLUIDO; su información sigue disponible para consulta.
  - 2. La fecha de retiro no puede ser anterior al inicio del contrato.
  - 3. Se genera la alerta de desafiliación pendiente en el módulo CPS (RF-08).
  - 4. Si el empleado tiene una cuenta de usuario, se desactiva (RF-23).
  - 5. Se habilita el cálculo del finiquito según el tipo de retiro (RF-20).
- **Criterio de aceptación:** Al retirar a un empleado por despido injustificado, queda RETIRADO, aparece en la bandeja de la CPS con el contador de baja y su finiquito incluye el desahucio.

### RF-29 — El sistema debe permitir buscar empleados por CI, código o nombre.

- **Prioridad:** Alta · **Caso de uso:** CU-01
- **Datos:** CI, código o nombre (parcial o completo). Filtros: departamento, categoría, estado.
- **Reglas:**
  - 1. La búsqueda por nombre es parcial y no distingue mayúsculas ni tildes.
  - 2. El resultado es una lista resumida (CI, nombre, cargo y estado) antes de abrir la ficha completa.
  - 3. El tiempo de respuesta cumple el RNF-03.
- **Criterio de aceptación:** Al escribir "perez", el sistema lista también a los empleados de apellido "Pérez".

## Módulo de Seguro de Salud (CPS)

### RF-06 — El sistema debe registrar la afiliación del trabajador a la CPS y generar el Aviso de Afiliación del Trabajador (parte de ingreso).

- **Prioridad:** Alta · **Caso de uso:** CU-04
- **Datos:** Contrato del empleado (buscado por su CI), número de matrícula CPS, fecha de afiliación, tipo de afiliación (NUEVO o REINGRESO).
- **Reglas:**
  - 1. El empleado debe tener un contrato vigente.
  - 2. La matrícula CPS es única por contrato vigente.
  - 3. El PDF del aviso replica los campos del formulario oficial de la CPS.
  - 4. El tipo REINGRESO exige una desafiliación anterior registrada del mismo empleado.
- **Criterio de aceptación:** Al afiliar a un empleado sin contrato vigente, el sistema rechaza el registro con el mensaje "El empleado no tiene un contrato vigente". Con contrato vigente, genera el aviso en PDF.

### RF-07 — El sistema debe controlar el plazo de afiliación desde el inicio laboral y mostrar en una bandeja de control las afiliaciones en plazo, próximas a vencer y vencidas.

- **Prioridad:** Alta · **Caso de uso:** CU-04
- **Datos:** Fecha de inicio del contrato, fecha actual, feriados (RF-30), plazo de afiliación en días hábiles (RF-22). Filtros: estado, rango de fechas, departamento.
- **Reglas:**
  - 1. El plazo se cuenta en días hábiles (sin días no laborables ni feriados); el día de inicio cuenta como primer día de trabajo, incluido el período de prueba.
  - 2. El plazo es un parámetro: el caso indica seis días de trabajo y el DL 13214, Art. 6, cinco días hábiles.
  - 3. Semáforo: verde con más de 2 días hábiles restantes, amarillo con 2 o menos y rojo si el plazo venció.
  - 4. El registro tardío no se bloquea: queda con el estado FUERA DE PLAZO.
- **Criterio de aceptación:** Con un plazo de 6 días hábiles, un empleado que ingresa el viernes 6/11/2026 vence el viernes 13/11/2026; la bandeja lo muestra en amarillo desde el miércoles 11/11 y en rojo desde el lunes 16/11.

### RF-08 — El sistema debe alertar la desafiliación pendiente al registrarse el retiro del trabajador y registrar el Aviso de Baja.

- **Prioridad:** Alta · **Caso de uso:** CU-04
- **Datos:** Contrato del empleado (buscado por su CI), fecha de retiro (RF-28), fecha de presentación del aviso de baja, plazo de baja en días hábiles (RF-22).
- **Reglas:**
  - 1. Al registrarse el retiro, el sistema genera una alerta para el Afiliador.
  - 2. El plazo para presentar el aviso de baja es de cinco días hábiles desde el fin de la relación laboral (DL 13214, Art. 8) y se maneja como parámetro.
  - 3. Un contador muestra los días hábiles restantes; al llegar a cero, el estado pasa a rojo.
  - 4. Mientras no se registre el aviso, el sistema advierte que la empresa sigue obligada a pagar las cotizaciones (DL 13214, Art. 8).
- **Criterio de aceptación:** Al marcar a un empleado como retirado, el sistema notifica al Afiliador: "Desafiliación pendiente. Quedan 5 días hábiles para presentar el aviso de baja".

### RF-09 — El sistema debe mantener el historial de afiliaciones y desafiliaciones de cada trabajador.

- **Prioridad:** Media · **Caso de uso:** CU-04
- **Datos:** Contrato del empleado (buscado por su CI).
- **Reglas:**
  - 1. Se muestra en orden cronológico cada alta, baja y corrección, con su fecha y responsable.
  - 2. No se eliminan registros; toda corrección queda en la bitácora con el valor anterior y el nuevo (RF-31).
  - 3. Estados: PENDIENTE, EN PLAZO, FUERA DE PLAZO y DESAFILIADO, los mismos de la tabla AFILIACION CPS.
- **Criterio de aceptación:** Al consultar a un empleado con un reingreso, se ven su primera alta, su baja y su segunda alta, con fechas y responsables.

## Módulo de Planillas de Sueldos

### RF-10 — El sistema debe importar los días trabajados de cada empleado desde el archivo de marcaciones de asistencia.

- **Prioridad:** Alta · **Caso de uso:** CU-05
- **Datos:** Archivo de marcaciones, gestión y mes.
- **Reglas:**
  - 1. Se valida la estructura del archivo antes de procesarlo.
  - 2. Los empleados no registrados o sin contrato vigente se listan como inconsistencias (CU-05.3).
  - 3. Los días trabajados deben estar entre 0 y 30.
  - 4. Hay un solo registro por contrato y mes; reimportar reemplaza los datos solo si la planilla no está cerrada.
  - 5. No hay conexión directa con equipos biométricos (fuera del alcance).
- **Criterio de aceptación:** Al importar un archivo con un CI que no existe en el sistema, ese CI aparece en la lista de inconsistencias y el resto de los registros se importa.

### RF-11 — El sistema debe calcular la planilla mensual (preplanilla), permitir su revisión y cerrarla una vez aprobada.

- **Prioridad:** Alta · **Caso de uso:** CU-05
- **Datos:** Días trabajados, haber básico de la categoría, otros ingresos, anticipos, formularios F110, parámetros de la gestión.
- **Reglas:**
  - 1. Sueldo ganado = haber básico ÷ 30 × días trabajados (RN-01).
  - 2. Total ingresos = sueldo ganado + otros ingresos; total descuentos = anticipos + AFP + RC-IVA; líquido pagable = total ingresos − total descuentos (caso).
  - 3. Primero se genera una preplanilla; al aprobarla, la planilla se cierra, no admite cambios y registra quién la aprobó. Como el caso define un solo operador de pagos, la aprueba el Encargado de Pagos; el control compensatorio es la bitácora (RF-31).
  - 4. Si los parámetros de la gestión no están configurados, no se procesa la planilla.
- **Criterio de aceptación:** Con un haber básico de Bs 3.000 y 25 días trabajados, el sueldo ganado es de Bs 2.500. Una planilla cerrada no permite editar ningún importe.

### RF-12 — El sistema debe aplicar el descuento de AFP según el porcentaje y el umbral parametrizados para la gestión.

- **Prioridad:** Alta · **Caso de uso:** CU-05
- **Datos:** Total ganado, porcentaje de AFP, umbral (en salarios mínimos), salario mínimo de la gestión (RF-22).
- **Reglas:**
  - 1. Si el total ganado supera el umbral, AFP = total ganado × porcentaje de AFP.
  - 2. Valores iniciales del caso: 12,21 % y un umbral de 2 salarios mínimos (2 × Bs 1.656).
  - 3. Normativa vigente: 12,71 % sobre el total ganado, sin umbral (umbral 0); salario mínimo de 2026: Bs 3.300 (DS 5516).
  - 4. La boleta muestra solo el aporte del trabajador, no el aporte patronal.
- **Criterio de aceptación:** Con los valores del caso, un total ganado de Bs 3.000 no tiene descuento de AFP y uno de Bs 4.000 descuenta Bs 488,40. Con los valores vigentes, Bs 4.000 descuenta Bs 508,40.

### RF-13 — El sistema debe calcular el RC-IVA separando la base imponible, el impuesto y el crédito fiscal del formulario F110.

- **Prioridad:** Alta · **Caso de uso:** CU-05, CU-07
- **Datos:** Haber básico, total ganado, AFP, salario mínimo, porcentaje de IVA (13 %), monto de facturas del F110, saldo a favor del mes anterior.
- **Reglas:**
  - 1. Regla del caso: no aplica cuando el haber básico no supera 2 salarios mínimos.
  - 2. Base imponible = sueldo neto (total ganado − AFP) − 2 salarios mínimos.
  - 3. Impuesto = 13 % de la base imponible; crédito = 13 % del monto de las facturas del F110.
  - 4. RC-IVA a retener = impuesto − crédito, nunca negativo; el exceso de crédito queda como saldo a favor para el mes siguiente.
  - 5. La base, el impuesto, el crédito y el saldo se guardan por separado en la boleta.
- **Criterio de aceptación:** Con un haber básico de Bs 3.000, el RC-IVA es 0 (no supera 2 × Bs 1.656). Si el crédito del F110 supera el impuesto, la retención es 0 y la diferencia aparece como saldo a favor en el mes siguiente.

### RF-14 — El sistema debe permitir registrar el formulario F110 presentado por el trabajador.

- **Prioridad:** Alta · **Caso de uso:** CU-07
- **Datos:** Contrato del empleado (buscado por su CI), mes declarado, monto total de las facturas, fecha de presentación.
- **Reglas:**
  - 1. El F110 presentado hasta el día 15 se aplica a la planilla del mes; el presentado después, a la del mes siguiente (caso).
  - 2. Hay una sola presentación por contrato y mes.
  - 3. El crédito (13 %) lo calcula el sistema (RF-13); no se ingresa a mano.
- **Criterio de aceptación:** Un F110 presentado el día 16 aparece aplicado en la planilla del mes siguiente.

### RF-15 — El sistema debe permitir registrar anticipos de sueldo.

- **Prioridad:** Alta · **Caso de uso:** CU-06
- **Datos:** Contrato del empleado (buscado por su CI), monto, fecha.
- **Reglas:**
  - 1. El anticipo solo se registra después del día 15 del mes (caso).
  - 2. La suma de los anticipos del mes no puede superar el 50 % del haber básico de la categoría (caso).
  - 3. El empleado debe tener un contrato vigente.
  - 4. El anticipo se descuenta una sola vez, en la planilla del mes, y queda registrado el usuario que lo cargó.
- **Criterio de aceptación:** Con un haber básico de Bs 3.000, un anticipo de Bs 1.600 se rechaza (el tope es Bs 1.500). Un anticipo registrado el día 10 también se rechaza.

### RF-16 — El sistema debe generar la boleta de pago de cada trabajador y la planilla consolidada de cada uno de los 12 meses de la gestión.

- **Prioridad:** Alta · **Caso de uso:** CU-05
- **Datos:** Planilla cerrada del mes.
- **Reglas:**
  - 1. Las boletas solo se generan de una planilla cerrada.
  - 2. Cada boleta guarda los importes y los parámetros usados en su cálculo (fotografía histórica).
  - 3. Las boletas y la planilla se exportan a PDF y Excel (RNF-17).
  - 4. Hay una planilla por mes y doce por gestión.
- **Criterio de aceptación:** Si en 2027 se cambia el porcentaje de AFP, las boletas de 2026 ya emitidas siguen mostrando los valores originales.

## Módulo de Vacaciones y Lactancias

### RF-17 — El sistema debe registrar las solicitudes de vacaciones y licencias firmadas por el jefe inmediato superior; las licencias se solicitan con un día de anticipación.

- **Prioridad:** Media · **Caso de uso:** CU-08
- **Datos:** Fecha de solicitud, fecha de firma del jefe, tipo (VACACION o LICENCIA), fecha desde, fecha hasta.
- **Reglas:**
  - 1. Sin la fecha de firma del jefe, la solicitud no se guarda (caso).
  - 2. Una licencia debe iniciar al menos un día después de la fecha de solicitud (caso).
  - 3. Los días hábiles de vacación pedidos no pueden superar el saldo (RF-18).
  - 4. Las vacaciones se pueden pedir desde que el empleado cumple un año; antes, solo licencias.
  - 5. Las solicitudes de un mismo empleado no pueden superponerse.
- **Criterio de aceptación:** Una licencia para el mismo día de la solicitud se rechaza. Pedir 10 días de vacación con un saldo de 2 muestra "Saldo insuficiente".

### RF-18 — El sistema debe calcular el saldo de vacaciones en días hábiles según la antigüedad y descontar de él las licencias canjeadas a cuenta de vacaciones.

- **Prioridad:** Media · **Caso de uso:** CU-08
- **Datos:** Fecha de ingreso, solicitudes registradas, feriados (RF-30), días laborables de la semana (RF-22).
- **Reglas:**
  - 1. Escala: desde 1 año hasta menos de 5 años, 15 días hábiles; desde 5 hasta menos de 10, 20; desde 10 años, 30 (parametrizable).
  - 2. Solo se descuentan días hábiles: los feriados y los días no laborables no se descuentan.
  - 3. Las licencias se descuentan del saldo de vacaciones (caso).
  - 4. Las licencias tomadas antes del primer año dejan un saldo negativo; si el empleado se retira antes de cumplir un año, se descuentan en el finiquito (RF-20).
- **Criterio de aceptación:** Un empleado con 7 años de antigüedad tiene 20 días; con una licencia de 3 días, su saldo es 17. Una vacación del lunes 2 al viernes 6 de noviembre de 2026 descuenta 4 días, porque el 2 de noviembre es feriado.

### RF-19 — El sistema debe registrar las entregas mensuales del subsidio de lactancia a la beneficiaria y listar las entregas pendientes del mes.

- **Prioridad:** Media · **Caso de uso:** CU-09
- **Datos:** Beneficiaria (dependiente), hijo o hija (dependiente), fecha de entrega, mes, número de entrega.
- **Reglas:**
  - 1. La beneficiaria es la esposa o conviviente del trabajador registrada como dependiente (caso).
  - 2. La entrega es en especie (productos), por un valor de referencia de 1 salario mínimo (parámetro).
  - 3. Se registra como máximo una entrega por mes y 12 entregas por cada hijo o hija.
  - 4. El sistema lista las entregas pendientes del mes (CU-09.1) y alerta cuando quedan 3 días para terminar el mes (tarea programada del sistema).
- **Criterio de aceptación:** Registrar una segunda entrega en el mismo mes para el mismo hijo se rechaza; la entrega número 13 también se rechaza.

## Módulo de Finiquitos y Evaluaciones

### RF-20 — El sistema debe calcular el finiquito según el tipo de retiro, detallando cada concepto.

- **Prioridad:** Media · **Caso de uso:** CU-10
- **Datos:** Tipo y fecha de retiro (RF-28), fecha de ingreso, total ganado de los últimos 3 meses, haber básico, saldo de vacaciones (RF-18), sueldos devengados, aguinaldo proporcional.
- **Reglas:**
  - 1. Indemnización: un sueldo promedio (de los últimos 3 meses) por año de servicio, proporcional por fracción, si el trabajador cumplió más de 90 días de trabajo continuo (parámetro ANTIG_MIN_INDEM; DS 110, Art. 2).
  - 2. Desahucio: 3 sueldos básicos (caso), solo si el tipo es DESPIDO INJUSTIFICADO.
  - 3. DESPIDO JUSTIFICADO: no hay indemnización ni desahucio; solo se pagan los conceptos pendientes.
  - 4. Se pagan las vacaciones pendientes; si el empleado no cumplió un año, se descuentan las licencias tomadas, en cualquier tipo de retiro (caso).
  - 5. El sistema alerta el plazo de pago del finiquito (parámetro, RF-22).
  - 6. El finiquito aprobado no se modifica.
- **Criterio de aceptación:** Retiro por despido injustificado con 4 años de antigüedad, promedio de Bs 5.000 y haber básico de Bs 4.500: indemnización de Bs 20.000 y desahucio de Bs 13.500. Con retiro voluntario, el desahucio es 0.

### RF-21 — El sistema debe registrar la evaluación trimestral de desempeño y proponer la acción que corresponde según el valor obtenido.

- **Prioridad:** Media · **Caso de uso:** CU-11
- **Datos:** Contrato del empleado (buscado por su CI), trimestre, fecha, valor (1 a 5), evaluador, observaciones, decisión final (instrucción escrita de la gerencia).
- **Reglas:**
  - 1. Hay una evaluación por contrato y trimestre; un reingreso inicia un contrato nuevo con su propia primera evaluación.
  - 2. Acción propuesta (caso): 1 o 2 en la primera evaluación, retiro; 3, llamada de atención escrita; 4 o 5, vale de Bs 1.000 para la canasta familiar.
  - 3. La acción es una propuesta: el Afiliador registra la decisión final según la instrucción escrita de la gerencia; el sistema no retira al empleado automáticamente.
  - 4. Las evaluaciones no se borran; toda corrección queda en la bitácora (RF-31).
- **Criterio de aceptación:** Al registrar un 2 en la primera evaluación, el sistema muestra "Acción propuesta: retiro" y el empleado sigue ACTIVO hasta que el responsable confirme la decisión y se registre el retiro (RF-28).

## Módulo de Administración

### RF-22 — El sistema debe permitir parametrizar por gestión las variables salariales, tributarias y de plazos.

- **Prioridad:** Alta · **Caso de uso:** CU-13
- **Datos:** Año de gestión, salario mínimo, porcentaje y umbral de AFP, porcentaje de IVA, haber básico por categoría, plazos de afiliación y baja CPS, edad máxima de hijo beneficiario, días laborables de la semana, valor de la lactancia, plazo de pago del finiquito, antigüedad mínima para la indemnización.
- **Reglas:**
  - 1. Se crea un registro por gestión; no se sobrescriben los valores de gestiones anteriores.
  - 2. Los porcentajes deben ser mayores a 0 y menores a 100; los plazos, enteros mayores a 0.
  - 3. Una gestión CERRADA no admite cambios en sus parámetros.
  - 4. Los valores iniciales son los del caso.
- **Criterio de aceptación:** Al cambiar el salario mínimo de la gestión 2026, las planillas de la gestión 2025 siguen mostrando el valor anterior.

### RF-23 — El sistema debe permitir gestionar usuarios, roles y permisos.

- **Prioridad:** Alta · **Caso de uso:** CU-12
- **Datos:** Login, contraseña, rol (Afiliador, Encargado de Pagos, Responsable de Vacaciones y Lactancias, Administrador del Sistema), empleado asociado.
- **Reglas:**
  - 1. La contraseña debe tener al menos 8 caracteres, 1 mayúscula y 1 número.
  - 2. Cada usuario tiene un único rol y accede solo a los casos de uso de ese rol.
  - 3. Un usuario no se elimina: se marca como inactivo para conservar su historial en la bitácora.
  - 4. Al registrarse el retiro del empleado titular (RF-28), su cuenta se desactiva.
- **Criterio de aceptación:** Al crear un usuario con una contraseña débil, el sistema la rechaza. Un usuario desactivado ya no puede iniciar sesión, pero su historial se mantiene.

### RF-24 — El sistema debe permitir migrar los datos del personal activo desde archivos Excel o CSV.

- **Prioridad:** Alta · **Caso de uso:** CU-14
- **Datos:** Archivo Excel o CSV con la plantilla predefinida.
- **Reglas:**
  - 1. Se valida que el archivo tenga exactamente las columnas de la plantilla.
  - 2. Una fila con error (por ejemplo, un CI duplicado en el archivo o en la base de datos) no detiene la carga: se procesan las filas correctas y se genera un reporte de errores en Excel.
  - 3. Antes de migrar, se ejecuta un respaldo automático (RF-25).
- **Criterio de aceptación:** Al subir un Excel con 100 empleados, 2 de ellos con CI duplicado, se cargan los 98 correctos y se descarga un Excel con los 2 rechazados y el motivo.

### RF-25 — El sistema debe permitir programar, verificar y restaurar los respaldos de la base de datos.

- **Prioridad:** Alta · **Caso de uso:** CU-14
- **Datos:** Horario de respaldo, ruta de destino, archivo de respaldo a restaurar.
- **Reglas:**
  - 1. El respaldo se ejecuta automáticamente todos los días en el horario programado (por defecto, 23:00).
  - 2. Se conservan los respaldos de los últimos 30 días.
  - 3. Antes de marcar un respaldo como exitoso, el sistema verifica su integridad con una suma de verificación.
  - 4. El resultado (éxito o falla) se notifica por correo al Administrador del Sistema.
  - 5. La restauración es manual, pide confirmación y respalda primero el estado actual.
- **Criterio de aceptación:** A las 23:00 el sistema genera el archivo .sql, lo verifica y envía un correo al Administrador. Al restaurar, pide confirmación antes de ejecutar.

### RF-26 — El sistema debe generar reportes parametrizados exportables a PDF y Excel.

- **Prioridad:** Alta · **Caso de uso:** CU-15
- **Datos:** Filtros (fecha, gestión, mes, departamento, categoría, estado, empleado), tipo de reporte.
- **Reglas:**
  - 1. Cada reporte muestra la fecha y hora de generación y el usuario que lo solicitó.
  - 2. Los PDF llevan el logo de YPFB-Andina y numeración de páginas.
  - 3. Tipos de reporte: Kardex (por departamento, categoría, estado y antigüedad), control de afiliaciones CPS (con totales en plazo y fuera de plazo), planillas, saldos de vacaciones y entregas de lactancia, finiquitos y evaluaciones.
  - 4. Cada usuario solo ve los reportes que su rol permite.
- **Criterio de aceptación:** El reporte de empleados de la categoría B exportado a Excel muestra la fecha de generación y el usuario que lo descargó.

### RF-27 — El sistema debe autenticar a los usuarios mediante usuario y contraseña.

- **Prioridad:** Alta · **Caso de uso:** CU-16
- **Datos:** Usuario (login), contraseña.
- **Reglas:**
  - 1. Solo pueden ingresar las cuentas activas.
  - 2. Tras 3 intentos fallidos consecutivos, la cuenta se bloquea durante 15 minutos.
  - 3. Un inicio de sesión exitoso reinicia el contador de intentos.
  - 4. Al ingresar, se cargan los permisos del rol del usuario.
- **Criterio de aceptación:** Tras el tercer intento fallido, el sistema muestra "Cuenta bloqueada por 15 minutos" y rechaza incluso la contraseña correcta hasta que se cumpla ese tiempo.

### RF-30 — El sistema debe permitir registrar los feriados de cada gestión para el cálculo de días hábiles.

- **Prioridad:** Alta · **Caso de uso:** CU-13
- **Datos:** Fecha, descripción, alcance (NACIONAL o DEPARTAMENTAL), departamento.
- **Reglas:**
  - 1. No se puede repetir la misma fecha para el mismo alcance y departamento.
  - 2. Un feriado departamental solo se aplica a los empleados cuyo cargo está en ese departamento.
  - 3. Los feriados se usan en los cálculos de los RF-07, RF-08, RF-17 y RF-18.
- **Criterio de aceptación:** Con el 24 de septiembre registrado como feriado departamental de Santa Cruz, una vacación que incluye ese día no lo descuenta para los empleados de Santa Cruz, pero sí para los de otros departamentos.

### RF-31 — El sistema debe permitir consultar la bitácora de auditoría.

- **Prioridad:** Alta · **Caso de uso:** CU-12
- **Datos:** Filtros: usuario, rango de fechas, tipo de operación, tabla afectada.
- **Reglas:**
  - 1. La bitácora es de solo lectura: nadie, ni el Administrador del Sistema, puede modificarla ni borrarla.
  - 2. En las tablas críticas (PLANILLA, CONTRATO, PARAMETRO, AFILIACION CPS) se muestran el valor anterior y el nuevo.
  - 3. Cada registro incluye la IP de origen.
  - 4. Se registran también los inicios de sesión fallidos y los bloqueos de cuenta.
- **Criterio de aceptación:** Si alguien modifica un haber básico, la bitácora muestra quién lo hizo, a qué hora, desde qué IP y cuál era el valor anterior.
