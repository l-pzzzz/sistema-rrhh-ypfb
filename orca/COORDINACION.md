# Coordinación de agentes

Reglas para el agente coordinador (worktree `main`) y para los workers de cada iteración.

## 1. Modelos
- **Coordinador (main):** Opus.
- **Workers:** Sonnet, siempre. Incluye la integración (A15) y los de C2.
- **Workers de C1 ya en marcha** (`c1-kardex`, `c1-cps`, `c1-planillas`): no se interrumpen en medio de un turno. Cuando cada uno queda en reposo (`orca terminal wait --for tui-idle`), se le envía `/model sonnet`, se confirma en su terminal que el cambio se aplicó y después se le envía:
  > Haz git pull --rebase origin main y aplica desde ahora AGENTS.md §10 (ahorro de tokens). Cuando abras tu PR, ejecuta /compact.
- **Workers nuevos:** no se usa `--agent claude`. Se crea el worktree sin agente y se lanza el agente con el modelo indicado:
  ```
  orca worktree create --name <nombre> --base-branch main --setup run --json
  orca terminal create --worktree <id> --command "claude --model sonnet" --json
  orca terminal send --terminal <id> --text "<prompt>" --enter --json
  ```

## 2. Ahorro de tokens
- Los workers aplican `AGENTS.md` §10.
- El coordinador:
  - Espera con `orca terminal wait` y timeouts largos; no consulta el estado a cada rato.
  - Lee solo el último mensaje de cada agente, no la terminal completa.
  - En sus informes resume y da los enlaces. Solo copia texto completo cuando el responsable pide un plan para revisarlo.

## 3. Excepción: worker trabado
- Si un worker se traba más de dos intentos en el mismo problema, el coordinador avisa al responsable.
- Solo con su autorización se cambia ese worker a `/model opus` para esa corrección, y luego se devuelve a `/model sonnet`.

## 4. Autorizaciones
- El coordinador no aprueba planes ni envía mensajes a los agentes sin autorización del responsable.
- El coordinador no une ningún PR (`AGENTS.md` §9).
