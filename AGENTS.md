# AGENTS.md — Reglas para los agentes de código

Proyecto: **Sistema de Información para la Gestión de Recursos Humanos – YPFB-Andina** (tesis, metodología PUD).
Equipo: Oscar Adrian Quina Cordero, Eloy Rivera Cellejas, Ezequiel Trujillo Ezequiel.

## 1. Regla de oro: todo nace del informe
- Programa **solo** lo que está en `docs/`. Cada pantalla, formulario, reporte o proceso debe responder a un RF y a un CU de `docs/01` y `docs/03`.
- Si algo no está en `docs/` o hay una contradicción, **no lo inventes**: detente y escribe la duda en el pull request (sección "Dudas para el equipo").
- Cita en cada vista y servicio el RF/CU que implementa, en el docstring: `"""CU-02.1 Registrar contrato (RF-02, RF-03)."""`.

## 2. Stack (no cambiar sin aprobación del equipo)
- Python 3.12, **Django 5.2**, MySQL 8 (`mysqlclient`), plantillas de Django + Bootstrap 5 + HTMX.
- Celery + Celery Beat + Redis para tareas programadas; WeasyPrint (PDF), openpyxl (Excel), pandas (importaciones).
- Pruebas: pytest, pytest-django, pytest-cov, factory_boy. Estilo: Ruff (PEP 8).
- Docker Compose para desarrollo y producción.

## 3. Estructura del repositorio
```
config/            settings, urls, celery
apps/core/         servicios compartidos: parámetros, calendario laboral, auditoría, señales del contrato
apps/kardex/       CU-01 a CU-03   (Quina)
apps/cps/          CU-04           (Rivera)
apps/planillas/    CU-05 a CU-07   (Trujillo)
apps/vacaciones/   CU-08 y CU-09   (Rivera)
apps/finiquitos/   CU-10 y CU-11   (Trujillo)
apps/administracion/ CU-12 a CU-14 y CU-16 (Quina)
apps/reportes/     CU-15           (Quina)
templates/  static/  docs/  orca/
```
- Cada app tiene su propio `urls.py`, `services.py` (reglas de negocio), `views.py`, `forms.py`, `templates/<app>/` y `tests/`.
- **No modifiques archivos de otra app.** `config/settings.py` y `config/urls.py` solo los cambia el agente de la fase base o el integrador.

## 4. Modelo de datos (crítico)
- Los 30 modelos están definidos en `docs/05_modelo_de_datos.md` y `docs/esquema/schema.json`. Son **idénticos** al diagrama de clases y al diseño relacional del informe.
- Nombres de tabla y columna exactos según las convenciones de `docs/05` (`db_table`, `db_column`). La prueba `apps/core/tests/test_fidelidad_esquema.py` lo verifica: **nunca la modifiques para que pase**.
- **CONTRATO es el eje:** afiliación, boletas, anticipos, F110, marcaciones, vacaciones, evaluaciones, lactancias y finiquitos se relacionan con el contrato, no con el empleado.
- Solo el agente de la fase base crea modelos y migraciones. Un agente de módulo **no cambia campos ni crea migraciones de esquema**; si necesita un cambio, lo pide en el PR.
- No se usan librerías que creen tablas extra del negocio (ni django-simple-history ni django-axes): la bitácora va en `BITACORA` y el bloqueo usa `USUARIO.Intentos` y `USUARIO.BloqHasta`.
- `USUARIO.Clave` guarda el hash BCrypt puro (`$2b$…`, 60 caracteres) mediante `set_password`/`check_password` propios del modelo (RNF-06).
- Las restricciones que MySQL no admite (un solo contrato VIGENTE por empleado; feriado nacional único) se validan en el servicio de su app y tienen prueba.

## 5. Reglas de negocio
- Nada se elimina: se usan estados (RETIRADO, CONCLUIDO, DESAFILIADO, usuario inactivo). `on_delete=PROTECT` salvo detalles de composición.
- Actualizar (cambio real) y corregir (error de registro) exigen **motivo** y quedan en BITACORA con `Operacion` = ACTUALIZACION o CORRECCION, `Motivo`, valor anterior y nuevo. Un acceso denegado se registra como ACCESO DENEGADO.
- Los valores legales (SMN, AFP, RC-IVA, plazos) se leen **siempre** de `PARAMETRO` mediante `apps.core.parametros`. Prohibido escribir 1656, 12.21, 3300, etc. en el código.
- Importes con `Decimal` y redondeo `ROUND_HALF_UP` a 2 decimales. Nunca `float` para dinero.
- Días hábiles siempre con `apps.core.calendario` (fines de semana y FERIADO).

## 6. Comunicación entre módulos (patrón Observer)
- `apps/core/senales.py` define `contrato_registrado(contrato)` y `contrato_retirado(contrato)`.
- Kardex las **emite**; CPS, Administración y Finiquitos las **escuchan** en su `receivers.py`. Ningún módulo importa servicios de otro módulo de negocio.

## 7. Seguridad (RNF-05 a RNF-09)
- Niveles: ADMINISTRADOR, OPERADOR, CONSULTA (`docs/02`). Toda vista exige login y verifica nivel y rol (decorador de `apps.core.permisos`).
- Bloqueo tras 3 intentos fallidos durante 15 minutos; sesión de 15 minutos de inactividad.
- Menú y acceso por rol (casos de uso de cada actor e informe 3.3.1):
  - Afiliador: Kardex y Contratos, Seguro CPS y Evaluaciones (operador).
  - Encargado de Pagos: Planillas y Finiquitos (operador); Kardex solo lectura.
  - Responsable de Vacaciones y Lactancias: Vacaciones y Lactancias (operador); Kardex solo lectura.
  - Administrador del Sistema: Administración.
  - Consulta: Kardex solo lectura.
  - Todos: Reportes, cada uno solo los de su proceso (RF-26).
- MySQL y Redis no se publican fuera de la red de Docker en producción; en desarrollo, solo en 127.0.0.1.

## 8. Pruebas y calidad (definición de terminado)
Una tarea está terminada solo si:
1. Las pruebas de `docs/07_casos_de_prueba.md` que le corresponden existen y pasan, con los valores esperados **sin modificar**.
2. `pytest` pasa completo y la cobertura de `services.py` es de al menos 80 %.
3. `ruff check .` no muestra errores.
4. `python manage.py makemigrations --check` no detecta cambios pendientes.
5. El PR lista: RF y CU implementados, pruebas agregadas y dudas para el equipo.
6. El PR actualiza `docs/09_trazabilidad_codigo.md` (archivos, pruebas y estado de cada RF que implementa).
7. Las clases de los patrones de diseño usan los nombres de `docs/06` (iguales a los diagramas del informe).

Escribe primero las pruebas (con los resultados del informe) y después el código.

## 9. Git
- Una rama por worktree: `base`, `c1-kardex`, `c1-cps`, `c1-planillas`, `c2-vacaciones`, `c2-finiquitos`, `c2-administracion`.
- Commits pequeños en español: `CU-02.1: registrar contrato con cargos`.
- Nada se une a `main` sin revisión del integrante responsable.

## 10. Ahorro de tokens
- **Lee solo lo que necesitas.** No releas `docs/` completo en cada turno: busca tus secciones por identificador (`grep -n "RF-05\|CU-03" docs/*.md`) y lee solo esos rangos. `AGENTS.md` y tu archivo de `orca/` sí se leen completos al empezar.
- **No muestres archivos grandes enteros.** Usa `grep`, `sed -n 'inicio,finp'` o `head`/`tail`; nunca hagas `cat` de migraciones, `schema.json`, logs ni archivos de más de 200 líneas.
- **Pruebas con salida corta.** Durante el desarrollo ejecuta solo tu app: `pytest apps/<app> -q -x --tb=short`. La suite completa, una sola vez antes del PR. Si la salida es larga, guárdala en un archivo y muestra solo el final (`... > pytest.log; tail -30 pytest.log`).
- **Comandos silenciosos.** `docker compose build -q`, `pip install -q`, `ruff check . --quiet` (o `--output-format concise`), `makemigrations --check --dry-run`. No sigas logs con `-f`.
- **Respuestas breves.** Entre pasos no narres lo que haces; al terminar, un resumen corto. La descripción completa va en el PR, no en la terminal.
- **Contexto limpio.** Cuando termines una tarea (PR abierto), ejecuta `/compact`. No arrastres a una tarea nueva el historial de la anterior.
- **No repitas trabajo.** Si una prueba o comando ya pasó y no cambiaste nada relacionado, no lo vuelvas a ejecutar.
