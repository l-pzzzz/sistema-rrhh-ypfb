# Prompt — Integración (A15 y A19) · rama `main` · coordinador

Lee `AGENTS.md`. Tu tarea es **integrar**, no programar funciones nuevas.

1. Revisa los PR abiertos de la iteración en este orden: Kardex → CPS → Planillas (C1) o Administración → Vacaciones → Finiquitos (C2).
2. Para cada PR: verifica que solo toque su app, que no cambie modelos ni la prueba de fidelidad del esquema, y que sus pruebas usen los valores de `docs/07` sin cambios. Lista los problemas encontrados.
3. Une a `main` uno por uno; después de cada unión ejecuta `ruff check .`, `python manage.py makemigrations --check` y `pytest`. Si algo falla, detente y explica la causa.
4. Agrega pruebas de integración en `tests_integracion/`:
   - registrar contrato → aparece la afiliación PENDIENTE con su fecha límite;
   - registrar retiro → fecha límite de baja, cuenta desactivada y finiquito habilitado;
   - contrato vigente con marcaciones → aparece en la preplanilla; contrato concluido → no aparece.
5. Informe final: qué se unió, resultados de las pruebas y pendientes para el equipo.
