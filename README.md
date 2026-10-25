# Sistema de Gestión de RRHH – YPFB-Andina

Tesis con metodología PUD. Python 3.12 · Django 5.2 · MySQL 8 · Bootstrap 5 + HTMX · Celery.

- `docs/` — requisitos, casos de uso, reglas, modelo de datos, arquitectura, casos de prueba y plan, tomados del informe final. **Única fuente de requisitos.**
- `AGENTS.md` — reglas para los agentes de IA y para el equipo.
- `orca/` — prompts para cada worktree de Orca, en el orden del plan:

| Orden | Prompt | Rama | Responsable |
|---|---|---|---|
| 1 | `orca/00_base.md` | `base` | Equipo (un solo agente) |
| 2 | `orca/c1_kardex.md` · `orca/c1_cps.md` · `orca/c1_planillas.md` (en paralelo) | `c1-*` | Quina · Rivera · Trujillo |
| 3 | `orca/99_integracion.md` | `main` | Equipo |
| 4 | `orca/c2_administracion.md` · `orca/c2_vacaciones.md` · `orca/c2_finiquitos.md` (en paralelo) | `c2-*` | Quina · Rivera · Trujillo |
| 5 | `orca/99_integracion.md` | `main` | Equipo |

## Cómo levantar la demo

Requisitos: Docker Desktop y Git. Comandos en PowerShell, desde la carpeta del repositorio. La demo solo corre con `DEBUG=True` (desarrollo).

```powershell
# 1. Variables de entorno (genere valores propios para SECRET_KEY y las contraseñas)
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"   # pegar en SECRET_KEY, DB_PASSWORD, DB_ROOT_PASSWORD y REDIS_PASSWORD (uno distinto cada vez)

# 2. Levantar MySQL, Redis, web, Celery y nginx (migra la base automáticamente)
docker compose -p rrhh-demo up -d --build

# 3. Cargar los datos de demostración: las contraseñas se muestran UNA sola vez en esta consola
docker compose -p rrhh-demo exec web python manage.py cargar_datos_demo

# 4. Abrir https://localhost:8443 (certificado autofirmado: aceptar la advertencia del navegador)

# 5. Al terminar, apagar y borrar la base de la demo
docker compose -p rrhh-demo down -v
```

`cargar_datos_demo` es idempotente (se puede repetir sin duplicar) y crea: los 9 departamentos, cargos con funciones, tipos de documento, el haber básico 2026 de las categorías A, B y C (valores de ejemplo), los feriados nacionales 2026, 20 empleados ficticios (CI 9000001 a 9000020) con contrato vigente, anticipos y formularios F110 de octubre de 2026 para algunos de ellos, y un usuario por rol:

| Usuario | Rol | Qué mostrar |
|---|---|---|
| `afiliador` | Afiliador | Kardex y contratos, bandeja del Seguro CPS |
| `pagos` | Encargado de Pagos | Planillas: importar el CSV, procesar, aprobar y exportar |
| `vacaciones` | Responsable de Vacaciones y Lactancias | Kardex solo lectura (su módulo llega en C2) |
| `admin` | Administrador del Sistema | Administración (llega en C2) |
| `consulta` | Consulta | Kardex solo lectura |

Planilla de la demo: en `pagos`, abra Planillas → Procesar **octubre de 2026** y cargue `docs/demo/marcaciones_ejemplo.csv` (cubre a los 20 empleados). Luego revise la preplanilla, apruebe y cierre, y exporte la planilla y las boletas en PDF.
