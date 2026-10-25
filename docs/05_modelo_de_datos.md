# Modelo de datos (30 tablas)

Fuente: Informe final, puntos 3.6.1 y 3.7. El diagrama de clases y el diseño relacional son equivalentes: **misma tabla, mismos atributos, mismas relaciones**. CONTRATO es la tabla central.

## Convenciones de implementación en Django

- Nombre de tabla en MySQL: el del informe en minúsculas y con guion bajo (`CONTRATO CARGO` → `contrato_cargo`), con `Meta.db_table`.
- Nombre de columna: el del informe exacto, con `db_column` (por ejemplo `fecha_ingreso = models.DateField(db_column="FechaIngreso")`). En Python los campos van en snake_case (PEP 8).
- Clave primaria compuesta (DETALLE BOLETA, DETALLE FINIQUITO, CONTRATO CARGO, PARAMETRO): `models.CompositePrimaryKey` (Django 5.2).
- Herencia PERSONA → EMPLEADO / DEPENDIENTE: herencia multitabla con `OneToOneField(Persona, parent_link=True, primary_key=True, db_column="CI")`.
- `USUARIO` es el modelo de usuario del sistema (`AUTH_USER_MODEL = "administracion.Usuario"`), con `Login` como nombre de usuario. `Clave` guarda el hash BCrypt puro (`$2b$…`, 60 caracteres).
- Restricciones UNIQUE y CHECK indicadas en la descripción de cada columna (incluidos los rangos) → `Meta.constraints`. Las que MySQL no admite (UNIQUE condicional: un solo contrato VIGENTE por empleado; feriado nacional único) se validan en el servicio y tienen su prueba.
- BITACORA.Operacion: ALTA, ACTUALIZACION, CORRECCION, BAJA, LOGIN FALLIDO, BLOQUEO, ACCESO DENEGADO; `Motivo` es obligatorio en ACTUALIZACION y CORRECCION.
- Nada se elimina físicamente (`on_delete=PROTECT`), salvo los detalles de una composición (`CASCADE`).
- Las tablas propias de Django (auth, sessions, contenttypes, migrations) no son tablas de negocio y no cuentan entre las 30. No se instala `django.contrib.admin`.

## Tabla → app de Django → clase

| Tabla | App | Clase |
|---|---|---|
| PERSONA | `kardex` | `Persona` |
| EMPLEADO | `kardex` | `Empleado` |
| DEPENDIENTE | `kardex` | `Dependiente` |
| TIPO DOCUMENTO | `kardex` | `TipoDocumento` |
| DOCUMENTO | `kardex` | `Documento` |
| CATEGORIA | `kardex` | `Categoria` |
| AJUSTE SALARIAL | `kardex` | `AjusteSalarial` |
| CONTRATO | `kardex` | `Contrato` |
| CONTRATO CARGO | `kardex` | `ContratoCargo` |
| CARGO | `kardex` | `Cargo` |
| FUNCION | `kardex` | `Funcion` |
| UBICACION | `kardex` | `Ubicacion` |
| AFILIACION CPS | `cps` | `AfiliacionCPS` |
| GESTION SALARIAL | `administracion` | `GestionSalarial` |
| PARAMETRO | `administracion` | `Parametro` |
| FERIADO | `administracion` | `Feriado` |
| PLANILLA | `planillas` | `Planilla` |
| BOLETA PAGO | `planillas` | `BoletaPago` |
| DETALLE BOLETA | `planillas` | `DetalleBoleta` |
| ANTICIPO | `planillas` | `Anticipo` |
| FORMULARIO F110 | `planillas` | `FormularioF110` |
| MARCACION | `planillas` | `Marcacion` |
| SOLICITUD VACACION | `vacaciones` | `SolicitudVacacion` |
| ENTREGA LACTANCIA | `vacaciones` | `EntregaLactancia` |
| FINIQUITO | `finiquitos` | `Finiquito` |
| DETALLE FINIQUITO | `finiquitos` | `DetalleFiniquito` |
| EVALUACION | `finiquitos` | `Evaluacion` |
| ROL | `administracion` | `Rol` |
| USUARIO | `administracion` | `Usuario` |
| BITACORA | `administracion` | `Bitacora` |

## PERSONA  (`kardex.Persona`)

Datos comunes de empleados y dependientes (superclase Persona).

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| CI | VARCHAR(15) | PK | No | Cédula de identidad con complemento opcional (1234567-1A) |
| Nombres | VARCHAR(60) | — | No | Nombres |
| Apellidos | VARCHAR(60) | — | No | Apellidos |
| FechaNac | DATE | — | No | Fecha de nacimiento |
| Sexo | CHAR(1) | — | No | M / F (CHECK) |
| Telefono | VARCHAR(15) | — | Sí | Teléfono de contacto |

## EMPLEADO  (`kardex.Empleado`)

Expediente laboral del trabajador (Kardex).

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| CI | VARCHAR(15) | PK, FK | No | Cédula; referencia a PERSONA → PERSONA.CI |
| Codigo | VARCHAR(10) | — | No | Código interno único (UNIQUE, EMP-0001) |
| FechaIngreso | DATE | — | No | Inicio de la relación laboral; base de la antigüedad |
| Direccion | VARCHAR(120) | — | Sí | Domicilio |
| NomEmerg | VARCHAR(80) | — | Sí | Nombre del contacto de emergencia |
| ParEmerg | VARCHAR(20) | — | Sí | Parentesco del contacto de emergencia |
| TelEmerg | VARCHAR(15) | — | Sí | Teléfono del contacto de emergencia |
| Estado | VARCHAR(10) | — | No | ACTIVO / RETIRADO |

## DEPENDIENTE  (`kardex.Dependiente`)

Familiar del trabajador; se registra con un solo trabajador.

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| CI | VARCHAR(15) | PK, FK | No | Cédula; referencia a PERSONA → PERSONA.CI |
| CIEmp | VARCHAR(15) | FK | No | Trabajador del que depende → EMPLEADO.CI |
| Parentesco | VARCHAR(20) | — | No | CONYUGE / CONVIVIENTE / HIJO / PADRE / MADRE (CHECK) |

## TIPO DOCUMENTO  (`kardex.TipoDocumento`)

Catálogo de tipos de documento.

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Id | INT | PK | No | Identificador |
| Descripcion | VARCHAR(40) | — | No | CI, título, certificado, etc. |

## DOCUMENTO  (`kardex.Documento`)

Documentos digitalizados de empleados y dependientes (PDF, JPG o PNG; máximo 5 MB).

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Nro | INT | PK | No | Identificador |
| CIPer | VARCHAR(15) | FK | No | Persona dueña del documento → PERSONA.CI |
| IdTipo | INT | FK | No | Tipo de documento → TIPO DOCUMENTO.Id |
| FechaEmision | DATE | — | Sí | Fecha de emisión |
| Archivo | VARCHAR(200) | — | No | Ruta del archivo digitalizado |
| FechaCarga | DATETIME | — | No | Fecha y hora de carga |
| Vigente | BOOLEAN | — | No | FALSE cuando fue reemplazado (historial) |

## CATEGORIA  (`kardex.Categoria`)

Categorías salariales por antigüedad en años cumplidos.

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Cod | CHAR(1) | PK | No | A, B o C (CHECK Cod IN ('A','B','C')) |
| AñosMin | TINYINT | — | No | Antigüedad mínima (0, 6, 16) |
| AñosMax | TINYINT | — | Sí | Antigüedad máxima (5, 15; nulo en C) |

## AJUSTE SALARIAL  (`kardex.AjusteSalarial`)

Haber básico de cada categoría por gestión.

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Id | INT | PK | No | Identificador |
| CodCat | CHAR(1) | FK | No | Categoría ajustada → CATEGORIA.Cod |
| Año | SMALLINT | FK | No | Gestión del ajuste (UNIQUE con CodCat) → GESTION SALARIAL.Año |
| HaberBasico | DECIMAL(10,2) | — | No | Haber básico vigente |

## CONTRATO  (`kardex.Contrato`)

Contrato del trabajador: eje del sistema; de él dependen afiliación, planillas, anticipos, F110, vacaciones, lactancia, evaluaciones y finiquito.

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Nro | INT | PK | No | Número de contrato |
| CIEmp | VARCHAR(15) | FK | No | Trabajador contratado → EMPLEADO.CI |
| CodCat | CHAR(1) | FK | No | Categoría vigente; se actualiza por antigüedad (RF-03) y queda en la bitácora → CATEGORIA.Cod |
| FechaInicio | DATE | — | No | Inicio del contrato |
| FechaFin | DATE | — | Sí | Fin previsto (nulo si es indefinido; CHECK > FechaInicio) |
| FechaRetiro | DATE | — | Sí | Fecha efectiva del retiro (nulo si vigente; CHECK >= FechaInicio) |
| TipoRetiro | VARCHAR(25) | — | Sí | VOLUNTARIO / DESPIDO JUSTIFICADO / DESPIDO INJUSTIFICADO (nulo si vigente) |
| MotivoRetiro | VARCHAR(200) | — | Sí | Motivo del retiro |
| Estado | VARCHAR(10) | — | No | VIGENTE / CONCLUIDO (un solo VIGENTE por empleado) |

## CONTRATO CARGO  (`kardex.ContratoCargo`)

Tabla intermedia: un contrato tiene uno o varios cargos.

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| NroCon | INT | PK, FK | No | Contrato → CONTRATO.Nro |
| IdCargo | INT | PK, FK | No | Cargo → CARGO.Id |

## CARGO  (`kardex.Cargo`)

Cargos de la empresa.

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Id | INT | PK | No | Identificador |
| Nombre | VARCHAR(60) | — | No | Nombre del cargo |
| IdUbi | INT | FK | No | Departamento donde se ejerce → UBICACION.Id |

## FUNCION  (`kardex.Funcion`)

Funciones de cada cargo.

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Id | INT | PK | No | Identificador |
| Descripcion | VARCHAR(150) | — | No | Función |
| IdCargo | INT | FK | No | Cargo al que pertenece → CARGO.Id |

## UBICACION  (`kardex.Ubicacion`)

Departamentos o secciones.

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Id | INT | PK | No | Identificador |
| Departamento | VARCHAR(60) | — | No | Nombre del departamento |

## AFILIACION CPS  (`cps.AfiliacionCPS`)

Afiliación y desafiliación a la CPS de cada contrato (no se eliminan registros).

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Nro | INT | PK | No | Identificador |
| NroCon | INT | FK | No | Contrato que origina la afiliación (UNIQUE: una afiliación por contrato) → CONTRATO.Nro |
| Tipo | VARCHAR(10) | — | No | NUEVO / REINGRESO |
| FechaLimite | DATE | — | No | Inicio laboral + plazo de afiliación en días hábiles |
| FechaAfil | DATE | — | Sí | Fecha de alta en la CPS |
| Matricula | VARCHAR(20) | — | Sí | N° de matrícula CPS del asegurado |
| FechaLimBaja | DATE | — | Sí | CONTRATO.FechaRetiro + plazo de baja en días hábiles |
| FechaDesafil | DATE | — | Sí | Fecha de presentación del aviso de baja |
| Estado | VARCHAR(20) | — | No | PENDIENTE / EN PLAZO / FUERA DE PLAZO / DESAFILIADO |

## GESTION SALARIAL  (`administracion.GestionSalarial`)

Gestión anual de planillas.

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Año | SMALLINT | PK | No | Año de la gestión |
| Estado | VARCHAR(10) | — | No | ABIERTA / CERRADA (cerrada: parámetros no editables) |

## PARAMETRO  (`administracion.Parametro`)

Parámetros legales y de negocio por gestión, en formato clave-valor (patrón Singleton).

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Año | SMALLINT | PK, FK | No | Gestión a la que aplica → GESTION SALARIAL.Año |
| Clave | VARCHAR(20) | PK | No | SMN, PORC_AFP, UMBRAL_AFP, PORC_IVA, PLAZO_AFIL, PLAZO_BAJA, EDAD_MAX_HIJO, DIAS_LAB, VALOR_LACT, PLAZO_FINIQ, ANTIG_MIN_INDEM |
| Valor | DECIMAL(12,2) | — | No | Valor del parámetro (porcentajes entre 0 y 100; plazos > 0; VALOR_LACT en múltiplos del SMN) |
| Fuente | VARCHAR(80) | — | Sí | Origen del valor (caso de estudio o norma) |

## FERIADO  (`administracion.Feriado`)

Feriados de cada gestión para el cálculo de días hábiles.

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Id | INT | PK | No | Identificador |
| Fecha | DATE | — | No | Fecha del feriado (UNIQUE con Alcance e IdUbi) |
| Descripcion | VARCHAR(60) | — | No | Motivo del feriado |
| Alcance | VARCHAR(15) | — | No | NACIONAL / DEPARTAMENTAL |
| IdUbi | INT | FK | Sí | Departamento (nulo si es nacional) → UBICACION.Id |

## PLANILLA  (`planillas.Planilla`)

Planilla mensual de sueldos (12 por gestión).

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Nro | INT | PK | No | Identificador |
| Año | SMALLINT | FK | No | Gestión → GESTION SALARIAL.Año |
| Mes | TINYINT | — | No | 1 a 12 (UNIQUE con Año) |
| Estado | VARCHAR(12) | — | No | PREPLANILLA / CERRADA |
| FechaCierre | DATE | — | Sí | Fecha de cierre |
| AprobadoPor | VARCHAR(30) | FK | Sí | Usuario que aprobó el cierre → USUARIO.Login |

## BOLETA PAGO  (`planillas.BoletaPago`)

Boleta de pago de cada trabajador en una planilla.

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| NroB | INT | PK | No | Identificador |
| NroPla | INT | FK | No | Planilla mensual → PLANILLA.Nro |
| NroCon | INT | FK | No | Contrato del trabajador (UNIQUE con NroPla) → CONTRATO.Nro |
| DiasTrab | TINYINT | — | No | Días trabajados (0 a 30) |
| TotIngresos | DECIMAL(10,2) | — | No | Total ingresos (histórico) |
| TotDescuentos | DECIMAL(10,2) | — | No | Total descuentos (histórico) |
| Liquido | DECIMAL(10,2) | — | No | Líquido pagable (histórico) |

## DETALLE BOLETA  (`planillas.DetalleBoleta`)

Conceptos calculados de cada boleta con la base y el porcentaje aplicados (fotografía histórica).

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| NroB | INT | PK, FK | No | Boleta → BOLETA PAGO.NroB |
| Concepto | VARCHAR(20) | PK | No | SUELDO GANADO / OTROS INGRESOS / ANTICIPO / AFP / RC-IVA / SALDO RC-IVA |
| Base | DECIMAL(10,2) | — | Sí | Base de cálculo usada |
| Porcentaje | DECIMAL(5,2) | — | Sí | Porcentaje aplicado en ese mes |
| Monto | DECIMAL(10,2) | — | No | Importe del concepto |

## ANTICIPO  (`planillas.Anticipo`)

Anticipos de sueldo (después del día 15; suma mensual hasta 50 % del haber básico).

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Nro | INT | PK | No | Identificador |
| NroCon | INT | FK | No | Contrato al que se descuenta → CONTRATO.Nro |
| Fecha | DATE | — | No | Fecha del anticipo (día > 15) |
| Monto | DECIMAL(10,2) | — | No | Monto del anticipo (> 0) |
| NroPla | INT | FK | Sí | Planilla en la que se descontó (una sola vez) → PLANILLA.Nro |

## FORMULARIO F110  (`planillas.FormularioF110`)

Descargo de facturas para el crédito fiscal del RC-IVA.

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Nro | INT | PK | No | Identificador |
| NroCon | INT | FK | No | Contrato del trabajador que declara → CONTRATO.Nro |
| Año | SMALLINT | — | No | Gestión declarada |
| Mes | TINYINT | — | No | Mes declarado (UNIQUE con NroCon y Año) |
| MontoFact | DECIMAL(10,2) | — | No | Total de facturas presentadas |
| FechaPres | DATE | — | No | Fecha de presentación (después del 15 se aplica al mes siguiente) |

## MARCACION  (`planillas.Marcacion`)

Días trabajados importados del control de asistencia (patrón Adapter).

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Id | INT | PK | No | Identificador |
| NroCon | INT | FK | No | Contrato del trabajador → CONTRATO.Nro |
| Año | SMALLINT | — | No | Gestión |
| Mes | TINYINT | — | No | Mes (UNIQUE con NroCon y Año) |
| DiasTrab | TINYINT | — | No | Días trabajados en el mes (0 a 30) |

## SOLICITUD VACACION  (`vacaciones.SolicitudVacacion`)

Vacaciones y licencias firmadas por el jefe inmediato.

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Nro | INT | PK | No | Identificador |
| NroCon | INT | FK | No | Contrato del trabajador que solicita → CONTRATO.Nro |
| Tipo | VARCHAR(10) | — | No | VACACION / LICENCIA |
| FechaSol | DATE | — | No | Fecha de solicitud |
| FechaFirma | DATE | — | No | Fecha de firma del jefe inmediato |
| FechaDesde | DATE | — | No | Inicio (licencia: al menos un día después de FechaSol) |
| FechaHasta | DATE | — | No | Fin (>= FechaDesde) |
| Dias | DECIMAL(4,1) | — | No | Días hábiles descontados del saldo |

## ENTREGA LACTANCIA  (`vacaciones.EntregaLactancia`)

Entregas mensuales del subsidio de lactancia (en especie, 12 por hijo).

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Nro | INT | PK | No | Identificador |
| NroCon | INT | FK | No | Contrato del trabajador que da derecho al subsidio → CONTRATO.Nro |
| CIBenef | VARCHAR(15) | FK | No | Beneficiaria (esposa o conviviente dependiente) → DEPENDIENTE.CI |
| CIHijo | VARCHAR(15) | FK | No | Hijo o hija que origina el subsidio → DEPENDIENTE.CI |
| Fecha | DATE | — | No | Fecha de entrega (una por mes y por hijo) |
| NroEntrega | TINYINT | — | No | 1 a 12 (UNIQUE con CIHijo) |

## FINIQUITO  (`finiquitos.Finiquito`)

Liquidación de un contrato concluido (patrón Strategy según el tipo de retiro del contrato).

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Nro | INT | PK | No | Identificador |
| NroCon | INT | FK | No | Contrato liquidado (UNIQUE) → CONTRATO.Nro |
| FechaCalc | DATE | — | No | Fecha de cálculo |
| Total | DECIMAL(10,2) | — | No | Monto total del finiquito |
| FechaLimPago | DATE | — | No | CONTRATO.FechaRetiro + plazo de pago (parámetro PLAZO_FINIQ) |
| Estado | VARCHAR(10) | — | No | CALCULADO / APROBADO / PAGADO (aprobado: no editable) |

## DETALLE FINIQUITO  (`finiquitos.DetalleFiniquito`)

Conceptos del finiquito con su importe.

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| NroFin | INT | PK, FK | No | Finiquito → FINIQUITO.Nro |
| Concepto | VARCHAR(25) | PK | No | INDEMNIZACION / DESAHUCIO / VACACIONES / AGUINALDO / DEVENGADOS / DESC. LICENCIAS |
| Monto | DECIMAL(10,2) | — | No | Importe (negativo si es descuento) |

## EVALUACION  (`finiquitos.Evaluacion`)

Evaluación trimestral de desempeño (una por contrato y trimestre).

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Nro | INT | PK | No | Identificador |
| NroCon | INT | FK | No | Contrato del trabajador evaluado → CONTRATO.Nro |
| Trimestre | CHAR(7) | — | No | AAAA-T# (UNIQUE con NroCon) |
| Fecha | DATE | — | No | Fecha de la evaluación |
| Valor | TINYINT | — | No | 1 a 5 (CHECK) |
| Evaluador | VARCHAR(30) | FK | No | Usuario que registró la evaluación → USUARIO.Login |
| AccionProp | VARCHAR(30) | — | Sí | RETIRO / LLAMADA DE ATENCION / VALE (propuesta) |
| Decision | VARCHAR(30) | — | Sí | Decisión final del responsable |

## ROL  (`administracion.Rol`)

Roles de acceso con su nivel (uno por actor).

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Id | INT | PK | No | Identificador |
| Nombre | VARCHAR(40) | — | No | Afiliador, Encargado de Pagos, etc. |
| Nivel | VARCHAR(15) | — | No | ADMINISTRADOR, OPERADOR o CONSULTA (RNF-07) |

## USUARIO  (`administracion.Usuario`)

Cuentas de acceso al sistema (un único rol por usuario).

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Login | VARCHAR(30) | PK | No | Nombre de usuario |
| Clave | VARCHAR(60) | — | No | Contraseña cifrada con BCrypt (hash $2b$ de 60 caracteres) |
| IdRol | INT | FK | No | Rol asignado → ROL.Id |
| CIEmp | VARCHAR(15) | FK | Sí | Empleado titular de la cuenta → EMPLEADO.CI |
| Activo | BOOLEAN | — | No | Cuenta habilitada (baja lógica) |
| Intentos | TINYINT | — | No | Intentos fallidos consecutivos (0 a 3) |
| BloqHasta | DATETIME | — | Sí | Fin del bloqueo de 15 minutos |

## BITACORA  (`administracion.Bitacora`)

Auditoría de operaciones, de solo lectura (RNF-09, RF-31).

| Columna | Tipo | Clave | Nulo | Descripción |
|---|---|---|---|---|
| Id | BIGINT | PK | No | Identificador |
| Login | VARCHAR(30) | FK | Sí | Usuario que operó (nulo si el login ingresado no existe) → USUARIO.Login |
| LoginIntento | VARCHAR(30) | — | Sí | Nombre de usuario ingresado en un intento fallido |
| FechaHora | DATETIME | — | No | Momento de la operación |
| Operacion | VARCHAR(20) | — | No | ALTA / ACTUALIZACION / CORRECCION / BAJA / LOGIN FALLIDO / BLOQUEO / ACCESO DENEGADO |
| Tabla | VARCHAR(40) | — | Sí | Tabla afectada |
| ValorAnt | TEXT | — | Sí | Valor anterior (tablas críticas) |
| ValorNuevo | TEXT | — | Sí | Valor nuevo (tablas críticas) |
| Motivo | VARCHAR(200) | — | Sí | Motivo de la actualización o corrección (obligatorio en esas operaciones) |
| IP | VARCHAR(45) | — | No | Dirección IP de origen |
