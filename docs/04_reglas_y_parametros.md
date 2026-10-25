# Reglas de negocio y parámetros

## Reglas de negocio de la planilla (CU-05)

- **RN-01:** Sueldo ganado = haber básico de la categoría ÷ 30 × días trabajados.
- **RN-02:** Total ingresos (total ganado) = sueldo ganado + otros ingresos.
- **RN-03:** Total descuentos = anticipos + AFP + RC-IVA.
- **RN-04:** AFP = total ganado × PORC_AFP, cuando el total ganado supera UMBRAL_AFP × SMN. Valores del caso: 12,21 % y 2 × Bs 1.656 = Bs 3.312. Valores vigentes: 12,71 % sin umbral y SMN de Bs 3.300 (DS 5516).
- **RN-05:** RC-IVA: regla del caso, no aplica si el haber básico no supera 2 SMN. Impuesto = 13 % × (total ganado − AFP − 2 SMN); crédito = 13 % de las facturas del F110; retención = impuesto − crédito − saldo a favor anterior, nunca negativa; el excedente pasa como saldo a favor al mes siguiente.
- **RN-06:** Anticipos: solo después del día 15; la suma del mes no supera el 50 % del haber básico de la categoría; cada anticipo se descuenta una sola vez.
- **RN-07:** Líquido pagable = total ingresos − total descuentos. Una gestión tiene 12 planillas mensuales.
- **RN-08:** Cada boleta guarda en DETALLE BOLETA la base y el porcentaje aplicados a cada concepto; un cambio posterior de parámetros no altera las boletas emitidas.

## Parámetros de la gestión (tabla PARAMETRO, clave-valor por año)

El valor del caso es el valor inicial; el sistema calcula con el valor vigente con solo cambiar el parámetro. **Nunca escribir estos valores en el código.** Son 11 claves; VALOR_LACT se guarda en múltiplos del SMN (1 = 1 SMN de la gestión).

| Clave | Descripción | Valor inicial | Origen y referencia vigente |
|---|---|---|---|
| SMN | Salario mínimo nacional | Bs 1.656 | Caso de estudio. Vigente: Bs 3.300 desde el 01/01/2026 (DS 5516). |
| PORC_AFP | Aporte laboral al sistema de pensiones | 12,21 % | Caso de estudio. Vigente: 12,71 % del total ganado (Gestora Pública). |
| UMBRAL_AFP | Salarios mínimos a partir de los cuales se descuenta la AFP | 2 | Caso de estudio. Vigente: 0 (sin umbral). |
| PORC_IVA | Alícuota del RC-IVA y del crédito fiscal del F110 | 13 % | Caso de estudio y SIN. |
| PLAZO_AFIL | Plazo de afiliación a la CPS en días hábiles | 6 | Caso ("seis días de trabajo"). DL 13214, Art. 6: 5 días hábiles. |
| PLAZO_BAJA | Plazo del aviso de baja en días hábiles | 5 | DL 13214, Art. 8 (el caso solo indica "cuanto antes"). |
| EDAD_MAX_HIJO | Edad máxima de hijo beneficiario (advertencia) | 25 | Propuesta del equipo; a confirmar con la CPS. |
| DIAS_LAB | Días laborables por semana | 5 | Lunes a viernes; ajustable según el régimen de cada área. |
| VALOR_LACT | Valor de referencia de la entrega mensual de lactancia, en múltiplos del SMN | 1 (= 1 SMN) | Subsidio de lactancia en especie durante 12 meses. |
| PLAZO_FINIQ | Plazo de pago del finiquito en días | 15 | Normativa laboral; a confirmar si son días hábiles o calendario. |
| ANTIG_MIN_INDEM | Días de trabajo continuo para tener derecho a la indemnización | 90 | DS 110, Art. 2: más de 90 días de trabajo continuo. |
