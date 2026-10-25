# Casos de uso

Fuente: Informe final, puntos 3.3 y 3.4. Actores: Usuario RRHH (abstracto), Afiliador, Encargado de Pagos, Responsable de Vacaciones y Lactancias, Administrador del Sistema.

Reglas: «include» = siempre se ejecuta; «extend» = opcional, en un punto de extensión y con una condición. CU-01.1 *Buscar empleado* se reutiliza en varios casos de uso. Los procesos automáticos (alertas, recálculo de categorías, respaldo nocturno) son tareas programadas internas (Celery Beat), no casos de uso.

## CU-01 Gestionar Kardex del empleado

- **Actor:** Afiliador
- **Requisitos:** RF-01, RF-04, RF-29
- **Precondición:** el Afiliador inició sesión.
- **Postcondición:** el expediente queda registrado, actualizado o corregido, con el motivo en la bitácora.
- **Puntos de extensión:** nuevo empleado, cambio o error, documentos
- «include» CU-01.1 Buscar empleado (CI, código o nombre)
- «extend» CU-01.2 Registrar datos del empleado — punto: *nuevo empleado* — condición: [la búsqueda no encuentra al empleado]
- «extend» CU-01.3 Actualizar o corregir datos del empleado — punto: *cambio o error* — condición: [cambio en los datos o error de registro]
- «extend» CU-01.4 Adjuntar o reemplazar documentos — punto: *documentos* — condición: [el empleado presenta documentos]

## CU-02 Gestionar contrato del empleado

- **Actor:** Afiliador
- **Requisitos:** RF-02, RF-03, RF-28
- **Precondición:** el empleado está registrado en el Kardex (CU-01).
- **Postcondición:** el contrato queda vigente, actualizado o concluido y disponible para CPS, Planillas y Finiquitos.
- **Puntos de extensión:** nuevo contrato, cambio o error, retiro
- «include» CU-01.1 Buscar empleado (CI, código o nombre)
- «extend» CU-02.1 Registrar contrato — punto: *nuevo contrato* — condición: [nuevo ingreso o renovación de contrato]
- «extend» CU-02.3 Actualizar o corregir contrato — punto: *cambio o error* — condición: [cambio de cargo o error de registro]
- «extend» CU-02.4 Registrar retiro del empleado — punto: *retiro* — condición: [el empleado deja la empresa]
- CU-02.1 «include» CU-02.2 Asignar cargo(s) y categoría por antigüedad (A, B, C)

## CU-03 Gestionar dependientes

- **Actor:** Afiliador
- **Requisitos:** RF-04, RF-05
- **Precondición:** el empleado ya fue afiliado a la CPS.
- **Postcondición:** los dependientes quedan registrados, actualizados o corregidos, cada uno con un solo trabajador.
- **Puntos de extensión:** nuevo familiar, cambio o error, validación de edad
- «include» CU-01.1 Buscar empleado (CI, código o nombre)
- «extend» CU-03.1 Registrar dependiente — punto: *nuevo familiar* — condición: [el trabajador declara un nuevo familiar]
- «extend» CU-03.3 Actualizar o corregir dependiente — punto: *cambio o error* — condición: [cambio en los datos o error de registro]
- «extend» CU-03.4 Advertir edad máxima de hijo beneficiario — punto: *validación de edad* — condición: [el hijo o hija supera la edad parametrizada]
- CU-03.1 «include» CU-03.2 Adjuntar fotocopia de CI

## CU-04 Gestionar afiliación / desafiliación CPS

- **Actor:** Afiliador
- **Requisitos:** RF-06, RF-07, RF-08, RF-09
- **Precondición:** el contrato del empleado está registrado.
- **Postcondición:** la afiliación queda en el historial con estado EN PLAZO o FUERA DE PLAZO.
- **Puntos de extensión:** alta, baja
- «include» CU-01.1 Buscar empleado (CI, código o nombre)
- «include» CU-04.1 Consultar bandeja de control (semáforo)
- «extend» CU-04.2 Registrar afiliación y matrícula — punto: *alta* — condición: [nuevo ingreso o reingreso]
- «extend» CU-04.4 Registrar aviso de baja — punto: *baja* — condición: [empleado retirado pendiente de baja]
- CU-04.2 «include» CU-04.3 Generar aviso de afiliación (parte de ingreso)

## CU-05 Procesar planilla de sueldos

- **Actor:** Encargado de Pagos
- **Requisitos:** RF-10, RF-11, RF-12, RF-13, RF-16
- **Precondición:** los parámetros de la gestión están configurados.
- **Postcondición:** la planilla del mes queda cerrada, aprobada y con sus boletas.
- **Puntos de extensión:** validación de datos, revisión de preplanilla
- «include» CU-05.1 Importar días trabajados
- «include» CU-05.2 Calcular ingresos, descuentos y generar preplanilla
- «extend» CU-05.3 Reportar inconsistencias — punto: *validación de datos* — condición: [datos incompletos o inconsistentes]
- «extend» CU-05.4 Aprobar y cerrar planilla — punto: *revisión de preplanilla* — condición: [la preplanilla es aprobada]
- CU-05.4 «include» CU-05.5 Generar boletas de pago

## CU-06 Registrar anticipo

- **Actor:** Encargado de Pagos
- **Requisitos:** RF-15
- **Precondición:** el empleado tiene un contrato vigente.
- **Postcondición:** el anticipo queda registrado y se descuenta una vez en la planilla del mes.
- «include» CU-01.1 Buscar empleado (CI, código o nombre)
- «include» CU-06.1 Verificar fecha (día > 15) y tope mensual del 50 %
- **Flujo alternativo:** si no cumple la fecha o el tope, el sistema rechaza el registro (flujo alternativo).

## CU-07 Registrar formulario F110 (RC-IVA)

- **Actor:** Encargado de Pagos
- **Requisitos:** RF-13, RF-14
- **Precondición:** el empleado entregó su formulario F110.
- **Postcondición:** el crédito queda disponible para el cálculo del RC-IVA.
- **Puntos de extensión:** período de aplicación
- «include» CU-01.1 Buscar empleado (CI, código o nombre)
- «include» CU-07.1 Calcular crédito fiscal (13 % de las facturas)
- «extend» CU-07.2 Aplicar al mes siguiente — punto: *período de aplicación* — condición: [presentado después del día 15]

## CU-08 Gestionar vacaciones y licencias

- **Actor:** Responsable de Vacaciones y Lactancias
- **Requisitos:** RF-17, RF-18
- **Precondición:** el formulario está firmado por el jefe inmediato superior.
- **Postcondición:** la solicitud queda registrada y el saldo de vacaciones se actualiza.
- **Puntos de extensión:** tipo de solicitud
- «include» CU-01.1 Buscar empleado (CI, código o nombre)
- «include» CU-08.1 Consultar saldo de vacaciones
- «include» CU-08.2 Verificar firma del jefe inmediato
- «include» CU-08.3 Calcular días hábiles (feriados)
- «extend» CU-08.4 Canjear licencia a cuenta de vacaciones — punto: *tipo de solicitud* — condición: [la solicitud es una licencia]

## CU-09 Controlar entregas de lactancia

- **Actor:** Responsable de Vacaciones y Lactancias
- **Requisitos:** RF-19
- **Precondición:** la beneficiaria y el hijo están registrados como dependientes.
- **Postcondición:** la entrega queda registrada con su número y fecha.
- «include» CU-01.1 Buscar empleado (CI, código o nombre)
- «include» CU-09.1 Consultar entregas pendientes del mes
- «include» CU-09.2 Verificar beneficiaria y límite de 12 entregas

## CU-10 Calcular finiquito

- **Actor:** Encargado de Pagos
- **Requisitos:** RF-20
- **Precondición:** el retiro del empleado está registrado.
- **Postcondición:** el finiquito queda calculado con su detalle y su fecha límite de pago.
- **Puntos de extensión:** desahucio, descuentos
- «include» CU-01.1 Buscar empleado (CI, código o nombre)
- «include» CU-10.1 Calcular indemnización y beneficios de ley
- «include» CU-08.1 Consultar saldo de vacaciones
- «extend» CU-10.2 Calcular desahucio (3 sueldos básicos) — punto: *desahucio* — condición: [despido injustificado]
- «extend» CU-10.3 Descontar licencias — punto: *descuentos* — condición: [antigüedad menor a 1 año]

## CU-11 Registrar evaluación de desempeño

- **Actor:** Afiliador
- **Requisitos:** RF-21
- **Precondición:** el empleado tiene un contrato vigente.
- **Postcondición:** la evaluación, la acción propuesta y la decisión final quedan registradas.
- **Puntos de extensión:** acción, decisión
- «include» CU-01.1 Buscar empleado (CI, código o nombre)
- «include» CU-11.1 Determinar acción propuesta (1 a 5)
- «extend» CU-11.2 Proponer vale de Bs 1.000 — punto: *acción* — condición: [valor 4 o 5]
- «extend» CU-11.3 Proponer llamada de atención — punto: *acción* — condición: [valor 3]
- «extend» CU-11.4 Proponer retiro — punto: *acción* — condición: [valor 1 o 2 en la primera evaluación]
- «extend» CU-11.5 Registrar decisión final — punto: *decisión* — condición: [la gerencia comunica su decisión por escrito]

## CU-12 Gestionar usuarios, roles y auditoría

- **Actor:** Administrador del Sistema
- **Requisitos:** RF-23, RF-31
- **Precondición:** el Administrador inició sesión.
- **Postcondición:** el usuario accede solo a los casos de uso de su rol.
- **Puntos de extensión:** alta, baja, auditoría
- «extend» CU-12.1 Crear usuario y asignar rol — punto: *alta* — condición: [nuevo usuario]
- «extend» CU-12.2 Desactivar usuario — punto: *baja* — condición: [la cuenta deja de usarse]
- «extend» CU-12.3 Consultar bitácora de auditoría — punto: *auditoría* — condición: [revisión de operaciones]

## CU-13 Parametrizar variables y feriados de la gestión

- **Actor:** Administrador del Sistema
- **Requisitos:** RF-22, RF-30
- **Precondición:** el Administrador inició sesión.
- **Postcondición:** los cálculos usan los valores vigentes de la gestión.
- **Puntos de extensión:** parámetros, haber básico, feriados
- «include» CU-13.1 Verificar que la gestión esté abierta
- «extend» CU-13.2 Registrar salario mínimo, porcentajes y plazos — punto: *parámetros* — condición: [nueva gestión o cambio normativo]
- «extend» CU-13.3 Registrar haber básico por categoría — punto: *haber básico* — condición: [ajuste salarial anual]
- «extend» CU-13.4 Registrar feriados — punto: *feriados* — condición: [nueva gestión o feriado decretado]

## CU-14 Administrar respaldos y migración de datos

- **Actor:** Administrador del Sistema
- **Requisitos:** RF-24, RF-25
- **Precondición:** el Administrador inició sesión.
- **Postcondición:** la base de datos queda respaldada, restaurada o con el personal migrado.
- **Puntos de extensión:** horario, restauración, migración
- «extend» CU-14.1 Configurar horario del respaldo — punto: *horario* — condición: [cambio del horario programado]
- «extend» CU-14.2 Restaurar respaldo — punto: *restauración* — condición: [falla o pérdida de datos]
- «extend» CU-14.3 Importar personal desde Excel / CSV — punto: *migración* — condición: [carga inicial del sistema]
- CU-14.2 «include» CU-14.4 Respaldar el estado actual

## CU-15 Generar reportes parametrizados

- **Actor:** Usuario RRHH
- **Requisitos:** RF-26
- **Precondición:** el usuario tiene permiso sobre el reporte.
- **Postcondición:** el reporte se muestra o se exporta.
- **Puntos de extensión:** exportación
- «include» CU-15.1 Seleccionar parámetros
- «include» CU-15.2 Mostrar vista previa
- «extend» CU-15.3 Exportar a PDF o Excel — punto: *exportación* — condición: [el usuario lo solicita]

## CU-16 Iniciar sesión

- **Actor:** Usuario RRHH
- **Requisitos:** RF-27
- **Precondición:** el usuario tiene una cuenta activa.
- **Postcondición:** el usuario accede al menú de su rol.
- **Puntos de extensión:** credenciales inválidas
- «include» CU-16.1 Validar credenciales
- «include» CU-16.2 Cargar permisos del rol
- «extend» CU-16.3 Bloquear cuenta 15 minutos — punto: *credenciales inválidas* — condición: [3 intentos fallidos consecutivos]

# Especificaciones detalladas (formato extendido de Larman)

## CU-02 Gestionar contrato del empleado — Módulo Kardex y Contratos — Responsable: Oscar Adrian Quina Cordero

**Actor principal:** Afiliador

**Personal involucrado e intereses:**
- **Afiliador:** registrar, actualizar o corregir el contrato sin volver a cargar los datos del Kardex.
- **Trabajador:** que su cargo, fechas y categoría sean correctos, porque definen su sueldo, su seguro y su finiquito.
- **Encargado de Pagos:** que solo los contratos vigentes, con la categoría correcta, entren a la planilla.
- **Gerencia:** evitar multas de la CPS y contingencias laborales por datos incorrectos.

**Precondiciones:**
1. El Afiliador inició sesión con nivel Operador en el módulo Kardex (CU-16).
2. El empleado está registrado en el Kardex (CU-01).
3. Las categorías y el haber básico de la gestión están configurados (CU-13).

**Garantías de éxito:**
1. El contrato queda VIGENTE con al menos un cargo y con la categoría que corresponde a la antigüedad.
2. Se crea la afiliación PENDIENTE a la CPS con su fecha límite (CU-04).
3. Toda actualización, corrección o retiro queda en la bitácora con el motivo, el valor anterior y el nuevo.
4. Si se registró un retiro: contrato CONCLUIDO, empleado RETIRADO, alerta de baja en la CPS, cuenta de usuario desactivada y finiquito habilitado.

**Escenario principal de éxito:**

| Paso | Actor | Sistema |
|---|---|---|
| 1 | Busca al empleado por CI, código o nombre (CU-01.1). | Muestra la ficha del empleado con sus contratos. |
| 2 | Elige "Nuevo contrato". | Verifica que el empleado no tenga un contrato VIGENTE. |
| 3 | Ingresa la fecha de inicio, la fecha de fin (si no es indefinido), el cargo o cargos y la ubicación. | Valida las fechas y que exista al menos un cargo. |
| 4 | Espera la respuesta del sistema. | Calcula la antigüedad, asigna la categoría A, B o C (CU-02.2) y muestra el haber básico de la gestión. |
| 5 | Confirma el registro. | Guarda CONTRATO y CONTRATO CARGO, registra la operación en la bitácora y avisa al módulo CPS (evento "contrato registrado"). |
| 6 | Espera la respuesta del sistema. | Muestra la afiliación pendiente con su fecha límite en días hábiles. |

**Extensiones:**
- **2a.** El empleado ya tiene un contrato vigente: el sistema rechaza el registro y ofrece actualizarlo o registrar el retiro.
- **3a.** La fecha de fin es anterior a la de inicio, o no se eligió ningún cargo: el sistema marca el error y no guarda.
- *a. **Actualizar o corregir (CU-02.3):** en cualquier momento el Afiliador abre el contrato vigente, cambia el cargo, la ubicación o las fechas, indica si es una actualización (cambio real) o una corrección (error de registro) y escribe el motivo; el sistema guarda y registra el valor anterior y el nuevo.
- *b. **Registrar retiro (CU-02.4):** el Afiliador ingresa la fecha, el tipo (voluntario, despido justificado o despido injustificado) y el motivo; el sistema valida que la fecha no sea anterior al inicio, concluye el contrato y avisa a CPS, Administración y Finiquitos (patrón Observer).

**Requisitos especiales:** Búsqueda en menos de 3 segundos (RNF-03).; Nivel Operador en el módulo Kardex (RNF-07).; Bitácora inalterable (RNF-09).
**Variaciones de tecnología y datos:** Fechas en formato dd/mm/aaaa; CI con complemento opcional.; Uso desde el navegador de la oficina o del campo (VPN).
**Frecuencia:** Cada vez que ingresa, se renueva, cambia de cargo o se retira un trabajador.
**Temas abiertos:** Confirmar con la empresa si la antigüedad se cuenta desde el primer contrato o desde el contrato vigente.; Confirmar el número máximo de renovaciones de un contrato a plazo fijo.
**Requisitos asociados:** RF-02, RF-03, RF-28 (y RF-29 por la búsqueda)

## CU-04 Gestionar afiliación / desafiliación CPS — Módulo Seguro de Salud (CPS) — Responsable: Eloy Rivera Cellejas

**Actor principal:** Afiliador

**Personal involucrado e intereses:**
- **Afiliador:** ver en una sola bandeja qué afiliaciones y bajas están por vencer.
- **Trabajador y dependientes:** tener atención médica desde su ingreso.
- **CPS:** recibir avisos completos y dentro del plazo.
- **Gerencia:** evitar multas y no pagar el seguro de personal ya retirado.

**Precondiciones:**
1. El contrato está registrado (CU-02) y su afiliación figura como PENDIENTE.
2. Los parámetros PLAZO_AFIL y PLAZO_BAJA y los feriados de la gestión están configurados (CU-13).
3. El Afiliador inició sesión con nivel Operador en el módulo CPS.

**Garantías de éxito:**
1. La afiliación queda con su matrícula (única por contrato), su fecha y el estado EN PLAZO o FUERA DE PLAZO.
2. El aviso de afiliación queda generado en PDF y el movimiento en el historial y la bitácora.
3. En una baja: la afiliación queda DESAFILIADA con su fecha.

**Escenario principal de éxito:**

| Paso | Actor | Sistema |
|---|---|---|
| 1 | Abre la bandeja de control de afiliaciones (CU-04.1). | Lista las afiliaciones y bajas pendientes en plazo, próximas a vencer o vencidas, con su semáforo. |
| 2 | Selecciona la afiliación de un contrato. | Muestra los datos del trabajador, del contrato y la fecha límite en días hábiles. |
| 3 | Indica el tipo (NUEVO o REINGRESO) y solicita el aviso. | Valida que el contrato esté vigente y, si es reingreso, que exista la desafiliación anterior; genera el aviso de afiliación en PDF (CU-04.3). |
| 4 | Presenta el aviso en la CPS (fuera del sistema) y registra la matrícula y la fecha de afiliación (CU-04.2). | Valida que la matrícula no esté registrada en otro contrato vigente. |
| 5 | Espera la respuesta del sistema. | Compara la fecha de afiliación con la fecha límite y registra EN PLAZO o FUERA DE PLAZO; guarda el historial y la bitácora. |
| 6 | Espera la respuesta del sistema. | Habilita el registro de dependientes del trabajador (CU-03). |

**Extensiones:**
- **3a.** Faltan datos del trabajador o del contrato: el sistema indica los campos y no genera el aviso.
- **4a.** La matrícula ya está registrada: el sistema muestra con qué contrato y pide corregirla.
- **5a.** La afiliación se registró después de la fecha límite: queda FUERA DE PLAZO, en rojo y en el reporte de riesgo de multa.
- *a. **Aviso de baja (CU-04.4):** cuando el contrato concluye por retiro, el sistema calcula la fecha límite de baja con PLAZO_BAJA y la muestra en la bandeja; el Afiliador registra el aviso de baja y su fecha y el sistema deja la afiliación DESAFILIADA.

**Requisitos especiales:** Los días hábiles excluyen los fines de semana y los feriados nacionales y departamentales.; Una tarea programada del sistema actualiza el semáforo cada día; el Afiliador lo ve al abrir la bandeja (CU-04.1).; Aviso exportable en PDF (RNF-17).
**Variaciones de tecnología y datos:** Formato del aviso según el modelo de la CPS.; Matrícula alfanumérica.
**Frecuencia:** Una vez por cada ingreso, reingreso o retiro de un trabajador.
**Temas abiertos:** El caso dice "seis días de trabajo" y el DL 13214 dice cinco días hábiles: el valor queda como parámetro (PLAZO_AFIL) hasta que la empresa lo confirme.; Confirmar con la CPS el formato vigente del aviso de afiliación.
**Requisitos asociados:** RF-06, RF-07, RF-08, RF-09

## CU-05 Procesar planilla de sueldos — Módulo Planillas de Sueldos — Responsable: Ezequiel Trujillo Ezequiel

**Actor principal:** Encargado de Pagos

**Personal involucrado e intereses:**
- **Encargado de Pagos:** calcular las 2.500 boletas sin errores y en pocos minutos.
- **Trabajador:** recibir su líquido pagable correcto y una boleta con el detalle.
- **Gerencia:** que la planilla aprobada no se pueda alterar después.
- **SIN y Gestora:** recibir los descuentos de RC-IVA y AFP calculados según la norma.

**Precondiciones:**
1. El Encargado de Pagos inició sesión con nivel Operador en el módulo Planillas.
2. Los parámetros de la gestión están configurados (CU-13).
3. Los anticipos (CU-06) y formularios F110 (CU-07) del mes están registrados.

**Garantías de éxito:**
1. La planilla del mes queda CERRADA, con el usuario que la aprobó, y no admite cambios.
2. Cada contrato vigente tiene su boleta de pago con el detalle de conceptos, y existe la planilla consolidada.
3. Los anticipos del mes quedan marcados como descontados.
4. La operación queda en la bitácora.

**Escenario principal de éxito:**

| Paso | Actor | Sistema |
|---|---|---|
| 1 | Selecciona Planillas > Procesar planilla. | Muestra las gestiones y los meses disponibles. |
| 2 | Selecciona la gestión y el mes. | Verifica que la planilla no esté cerrada y que existan los parámetros de la gestión. |
| 3 | Importa el archivo de marcaciones. | Adapta el archivo (CU-05.1), valida los datos y muestra los días trabajados por contrato. |
| 4 | Confirma el procesamiento. | Por cada contrato vigente calcula sueldo ganado, otros ingresos, anticipos, AFP y RC-IVA (CU-05.2) con las reglas RN-01 a RN-08 y genera la PREPLANILLA. |
| 5 | Revisa la preplanilla. | Muestra los totales por trabajador y generales. |
| 6 | Aprueba la planilla (CU-05.4). | Cierra la planilla, registra quién la aprobó, genera las boletas (CU-05.5) y registra la bitácora. |
| 7 | Exporta la planilla. | Genera la planilla consolidada en PDF o Excel. |

**Extensiones:**
- **2a.** La planilla ya está cerrada: solo se permite consultarla.
- **2b.** Faltan parámetros de la gestión: el sistema bloquea el proceso y avisa al Administrador.
- **3a.** El archivo trae personas sin contrato vigente o días fuera de 0 a 30: el sistema lista las inconsistencias (CU-05.3) y permite continuar sin esos registros o cancelar.
- **4a.** El trabajador no presentó su F110: el RC-IVA se calcula con crédito cero más el saldo a favor del mes anterior.
- **6a.** La preplanilla tiene errores: el Encargado corrige las novedades y recalcula.

**Requisitos especiales:** Procesar 2.500 contratos en menos de 5 minutos (RNF-04).; Importes en DECIMAL con 2 decimales (RNF-18).; Aprobación por el mismo operador, con la bitácora como control compensatorio (el caso define un solo Encargado de Pagos).
**Variaciones de tecnología y datos:** Archivo de marcaciones en Excel o CSV (patrón Adapter).; Exportación en PDF y Excel.
**Frecuencia:** Doce veces por gestión (una por mes).
**Temas abiertos:** La empresa debe confirmar si se aplican los porcentajes del caso o los vigentes (parámetros PORC_AFP, UMBRAL_AFP y SMN).
**Requisitos asociados:** RF-10, RF-11, RF-12, RF-13, RF-16 (con los parámetros del RF-22)
