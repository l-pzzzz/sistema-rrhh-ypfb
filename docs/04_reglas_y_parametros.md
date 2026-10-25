# Reglas de negocio y parámetros

## Reglas de negocio de la planilla (CU-05)

- **RN-01:** Sueldo ganado = haber básico de la categoría ÷ 30 × días trabajados.
- **RN-02:** Total ingresos (total ganado) = sueldo ganado + otros ingresos.
- **RN-03:** Total descuentos = anticipos + AFP + RC-IVA.
- **RN-04:** AFP = total ganado × PORC_AFP, cuando el total ganado supera UMBRAL_AFP × SMN. Valores del caso: 12,21 % y 2 × Bs 1.656 = Bs 3.312. Valores vigentes: 12,71 % sin umbral y SMN de Bs 3.300 (DS 5516).
- **RN-05:** RC-IVA: regla del caso, no aplica si el haber básico no supera UMBRAL_RCIVA × SMN (2 SMN). Impuesto = PORC_IVA × (total ganado − AFP − MNI_RCIVA × SMN); crédito = PORC_IVA de las facturas del F110; retención = impuesto − crédito − saldo a favor anterior, nunca negativa; el excedente pasa como saldo a favor al mes siguiente.
- **RN-06:** Anticipos: solo después del día DIA_ANTICIPO (15); la suma del mes no supera PORC_ANTICIPO (50 %) del haber básico de la categoría; cada anticipo se descuenta una sola vez.
- **RN-07:** Líquido pagable = total ingresos − total descuentos. Una gestión tiene 12 planillas mensuales.
- **RN-08:** Cada boleta guarda en DETALLE BOLETA la base y el porcentaje aplicados a cada concepto; un cambio posterior de parámetros no altera las boletas emitidas.

## Parámetros de la gestión (tabla PARAMETRO, clave-valor por año)

El valor del caso es el valor inicial; el sistema calcula con el valor vigente con solo cambiar el parámetro. **Nunca escribir estos valores en el código.** Son 16 claves; VALOR_LACT, UMBRAL_AFP, UMBRAL_RCIVA y MNI_RCIVA se guardan en múltiplos del SMN (1 = 1 SMN de la gestión). Las 5 últimas (UMBRAL_RCIVA, MNI_RCIVA, PORC_ANTICIPO, DIA_ANTICIPO y DIA_F110) se agregaron en C1 para no escribir valores del caso en el código.

| Clave | Descripción | Valor inicial | Origen y referencia vigente |
|---|---|---|---|
| SMN | Salario mínimo nacional | Bs 1.656 | Caso de estudio. Vigente: Bs 3.300 desde el 01/01/2026 (DS 5516). |
| PORC_AFP | Aporte laboral al sistema de pensiones | 12,21 % | Caso de estudio. Vigente: 12,71 % del total ganado (Gestora Pública). |
| UMBRAL_AFP | Salarios mínimos a partir de los cuales se descuenta la AFP | 2 | Caso de estudio. Vigente: 0 (sin umbral). |
| PORC_IVA | Alícuota del RC-IVA y del crédito fiscal del F110 | 13 % | Caso de estudio y SIN. |
| PLAZO_AFIL | Plazo de afiliación a la CPS en días hábiles | 6 | Caso ("seis días de trabajo"). DL 13214, Art. 6: 5 días hábiles. |
| PLAZO_BAJA | Plazo del aviso de baja en días hábiles | 5 | DL 13214, Art. 8 (el caso solo indica "cuanto antes"). El día del retiro cuenta como día 1, igual que el día de inicio en la afiliación. |
| EDAD_MAX_HIJO | Edad máxima de hijo beneficiario (advertencia) | 25 | Propuesta del equipo; a confirmar con la CPS. |
| DIAS_LAB | Días laborables por semana | 5 | Lunes a viernes; ajustable según el régimen de cada área. |
| VALOR_LACT | Valor de referencia de la entrega mensual de lactancia, en múltiplos del SMN | 1 (= 1 SMN) | Subsidio de lactancia en especie durante 12 meses. |
| PLAZO_FINIQ | Plazo de pago del finiquito en días calendario (no hábiles) | 15 | Normativa laboral. Se cuenta en días calendario desde la fecha de retiro (decisión del equipo, a confirmar con la norma vigente). |
| ANTIG_MIN_INDEM | Días de trabajo continuo para tener derecho a la indemnización | 90 | DS 110, Art. 2: más de 90 días de trabajo continuo. |
| UMBRAL_RCIVA | Haber básico, en múltiplos del SMN, hasta el cual no se retiene RC-IVA | 2 | Caso de estudio ("no aplica si no supera dos salarios mínimos"). |
| MNI_RCIVA | Monto no imponible del RC-IVA, en múltiplos del SMN | 2 | Caso de estudio y SIN: se resta del total ganado neto de AFP. |
| PORC_ANTICIPO | Tope mensual de anticipos sobre el haber básico | 50 % | Caso de estudio. |
| DIA_ANTICIPO | Día del mes a partir del cual se registran anticipos | 15 | Caso de estudio ("después del día 15"). |
| DIA_F110 | Último día para que el F110 se aplique a la planilla del mes | 15 | Caso de estudio. |

## Rango válido de cada parámetro (validación del CU-13, RF-22)

| Clave | Unidad | Rango válido |
|---|---|---|
| SMN | bolivianos | mayor a 0 |
| PORC_AFP | porcentaje | mayor a 0 y menor a 100 |
| UMBRAL_AFP | múltiplos del SMN | 0 o mayor (0 = sin umbral) |
| PORC_IVA | porcentaje | mayor a 0 y menor a 100 |
| PLAZO_AFIL | días hábiles | entero mayor a 0 |
| PLAZO_BAJA | días hábiles | entero mayor a 0 |
| EDAD_MAX_HIJO | años | entero mayor a 0 |
| DIAS_LAB | días por semana | entero de 1 a 7 |
| VALOR_LACT | múltiplos del SMN | mayor a 0 |
| PLAZO_FINIQ | días calendario | entero mayor a 0 |
| ANTIG_MIN_INDEM | días de trabajo continuo | entero mayor a 0 |
| UMBRAL_RCIVA | múltiplos del SMN | 0 o mayor |
| MNI_RCIVA | múltiplos del SMN | 0 o mayor |
| PORC_ANTICIPO | porcentaje | mayor a 0 y hasta 100 |
| DIA_ANTICIPO | día del mes | entero de 1 a 28 |
| DIA_F110 | día del mes | entero de 1 a 28 |
