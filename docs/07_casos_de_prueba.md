# Casos de prueba de aceptación

Fuente: Informe final, punto 2.3. **Cada caso debe existir como prueba automática en pytest** dentro de la app correspondiente. Los valores esperados se calcularon a mano y no se cambian para que la prueba pase: si no coincide, el error está en el código.

| ID | Regla | Datos de entrada | Resultado esperado |
|---|---|---|---|
| PL-01 | RN-01 a RN-07 | Haber básico Bs 8.000; 30 días; anticipo Bs 1.000; facturas F110 Bs 500. | AFP 976,80; RC-IVA 482,46 − crédito 65,00 = 417,46; descuentos 2.394,26; líquido **Bs 5.605,74**. |
| PL-02 | RN-01, RN-04, RN-05 | Haber básico Bs 3.000 (no supera 2 SMN); 20 días. | Sueldo ganado 2.000,00; sin AFP ni RC-IVA; líquido **Bs 2.000,00**. |
| PL-03 | RN-04, RN-05 (vigente) | Haber básico Bs 8.000; 30 días; facturas F110 Bs 500. | AFP 1.016,80; RC-IVA 49,82 cubierto por el crédito de 65,00; saldo a favor 15,18; líquido **Bs 6.983,20**. |
| AN-01 | RN-06 | Anticipo de Bs 3.500 con haber básico de Bs 6.000, registrado el día 20. | Rechazado: supera el 50 % (Bs 3.000). |
| AN-02 | RN-06 | Anticipo de Bs 1.000 registrado el día 10. | Rechazado: solo después del día 15. |
| CP-01 | RF-07 | Contrato que inicia el viernes 23/10/2026; PLAZO_AFIL = 6 días hábiles; sin feriados. | Fecha límite de afiliación: viernes **30/10/2026**. |
| CA-01 | RF-03 | Empleado con 5 años y 11 meses de antigüedad; luego con 6 años cumplidos. | Categoría A; al cumplir 6 años, categoría **B** y alerta al Afiliador. |
| CO-01 | RF-02 | Segundo contrato vigente para el mismo empleado. | Rechazado: un empleado no puede tener dos contratos vigentes. |

## Criterios de calidad

- Cobertura de pruebas de al menos 80 % en la capa de negocio (`pytest-cov`).
- Código sin errores de estilo (`ruff check .`).
- Cero defectos críticos abiertos para pasar a producción.
- Búsquedas en menos de 3 s y planilla de 2.500 contratos en menos de 5 min (Locust).
