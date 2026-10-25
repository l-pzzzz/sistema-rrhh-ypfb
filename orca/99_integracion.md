# Prompt — Integración (A15 y A19) · rama `main` · coordinador

Lee `AGENTS.md`. Tu tarea es **integrar**, no programar funciones nuevas.

1. Revisa los PR abiertos de la iteración en este orden: Kardex → CPS → Planillas (C1) o Administración → Vacaciones → Finiquitos (C2).
2. Para cada PR: verifica que solo toque su app, que no cambie modelos ni la prueba de fidelidad del esquema, y que sus pruebas usen los valores de `docs/07` sin cambios. Lista los problemas encontrados.
3. Une a `main` uno por uno; después de cada unión ejecuta `ruff check .`, `python manage.py makemigrations --check` y `pytest`. Si algo falla, detente y explica la causa.
4. Agrega pruebas de integración en `tests_integracion/`:
   - registrar contrato → aparece la afiliación PENDIENTE con su fecha límite;
   - registrar retiro → fecha límite de baja, cuenta desactivada y finiquito habilitado;
   - contrato vigente con marcaciones → aparece en la preplanilla; contrato concluido → no aparece.
5. Configuración que solo puede tocar el integrador (`config/`):
   - Une los diccionarios `PROGRAMACION` de cada `apps/<app>/tasks.py` en `CELERY_BEAT_SCHEDULE` y agrega una prueba que verifique que cada tarea de `docs/06` está programada.
   - Configura el correo (`EMAIL_HOST`, `EMAIL_PORT=587`, `EMAIL_USE_TLS`, usuario y contraseña desde `.env`) y, en desarrollo, el backend de consola.
6. Datos de demostración (solo desarrollo): crea el comando `python manage.py cargar_datos_demo` en `apps/core/management/commands/`, que cargue de forma idempotente:
   - ubicaciones (los 9 departamentos), algunos cargos con sus funciones y los tipos de documento;
   - el haber básico 2026 de las categorías A, B y C (valores de ejemplo, marcados como demostración en su descripción);
   - los feriados nacionales 2026;
   - un usuario por rol (Afiliador, Encargado de Pagos, Responsable de Vacaciones y Lactancias, Administrador y Consulta) con contraseñas generadas que se muestran una sola vez en consola;
   - unos 20 empleados ficticios con contrato vigente y un archivo de marcaciones de ejemplo en `docs/demo/marcaciones_ejemplo.csv`.
   Debe negarse a correr si `DEBUG` es False. Sirve para la defensa: permite mostrar Kardex, CPS y Planillas sin cargar todo a mano.
7. Revisa `docs/09_trazabilidad_codigo.md`: cada RF de la iteración debe estar en Implementado con archivos y pruebas que existan. Si una fila no coincide con el código, detente y repórtalo.
8. Informe final: qué se unió, resultados de las pruebas y pendientes para el equipo.
