# Prompt — Fase base (A11) · rama `base` · un solo agente

Lee `AGENTS.md` y todos los archivos de `docs/`. Tu tarea es crear la **base del sistema** sobre la que trabajarán después seis agentes en paralelo. No programes pantallas de negocio todavía.

## Entregables
1. Proyecto Django 5.2 en `config/` y las apps de `AGENTS.md` §3 dentro de `apps/`, registradas en `INSTALLED_APPS`.
2. **Los 30 modelos** de `docs/05_modelo_de_datos.md`, cada uno en la app que indica la tabla "Tabla → app → clase", siguiendo las convenciones de esa sección (`db_table`, `db_column`, `CompositePrimaryKey`, herencia de PERSONA, `on_delete`, `Meta.constraints` para UNIQUE y CHECK). `USUARIO` es el `AUTH_USER_MODEL`.
3. Migraciones iniciales y una migración de datos con:
   - los 4 roles con su nivel: Afiliador, Encargado de Pagos y Responsable de Vacaciones y Lactancias (OPERADOR) y Administrador del Sistema (ADMINISTRADOR), más un rol Consulta (CONSULTA);
   - la gestión 2026 con los parámetros de `docs/04` (valores iniciales del caso);
   - las categorías A (0–5 años), B (6–15) y C (16 o más).
4. `apps/core/`: `senales.py` (contrato exacto de `docs/06`), `parametros.py` (Singleton), `calendario.py` (`sumar_dias_habiles`, `dias_habiles_entre`), `auditoria.py` (registra en BITACORA usuario, IP, operación, tabla, valor anterior y nuevo; incluye middleware que guarda el usuario y la IP de la petición), `permisos.py` (decorador `requiere_nivel(nivel, rol=None)`).
5. Inicio y cierre de sesión con bloqueo de 3 intentos por 15 minutos usando `USUARIO.Intentos` y `USUARIO.BloqHasta`, y registro de intentos fallidos en BITACORA (CU-16, RF-27). Sesión de 15 minutos de inactividad.
6. Plantilla base (`templates/base.html`) con Bootstrap 5, HTMX, menú por nivel/rol y un área de alertas.
7. `requirements.txt`, `Dockerfile`, `docker-compose.yml` (web, db MySQL 8, redis, worker, beat), `.env.example`, `pyproject.toml` (Ruff), `pytest.ini`, `config/celery.py` y `.github/workflows/ci.yml` (MySQL 8 como servicio; ejecuta ruff, `makemigrations --check` y pytest).
8. Pruebas:
   - `apps/core/tests/test_fidelidad_esquema.py`: lee `docs/esquema/schema.json` y verifica, para cada una de las 30 tablas, que exista un modelo con ese `db_table` y exactamente esas columnas, claves primarias y foráneas.
   - Pruebas de `calendario.py` (incluido el caso CP-01 de `docs/07`), de `parametros.py` y del bloqueo de sesión.

## Criterio de terminado
`docker compose up` levanta el sistema; `pytest` y `ruff check .` pasan; `makemigrations --check` sin cambios; el PR describe el modelo creado y cualquier duda sobre el esquema.
