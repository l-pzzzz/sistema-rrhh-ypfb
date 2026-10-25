# Sistema de Gestión de RRHH – YPFB-Andina

Tesis con metodología PUD. Python 3.12 · Django 5.2 · MySQL 8 · Bootstrap 5 + HTMX · Celery.

- `docs/` — requisitos, casos de uso, reglas, modelo de datos, arquitectura, casos de prueba y plan, tomados del informe final. **Única fuente de requisitos.**
- `AGENTS.md` — reglas para los agentes de IA y para el equipo.
- `orca/` — prompts para cada worktree de Orca, en el orden del plan:

| Orden | Prompt | Rama | Responsable |
|---|---|---|---|
| 1 | `orca/00_base.md` | `base` | Equipo (un solo agente) |
| 2 | `orca/c1_kardex.md` · `orca/c1_cps.md` · `orca/c1_planillas.md` (en paralelo) | `c1/*` | Quina · Rivera · Trujillo |
| 3 | `orca/99_integracion.md` | `main` | Equipo |
| 4 | `orca/c2_administracion.md` · `orca/c2_vacaciones.md` · `orca/c2_finiquitos.md` (en paralelo) | `c2/*` | Quina · Rivera · Trujillo |
| 5 | `orca/99_integracion.md` | `main` | Equipo |
