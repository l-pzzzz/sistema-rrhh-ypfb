# Plan del proyecto (38 semanas, 190 días hábiles)

Duración obtenida con COCOMO básico (modo orgánico) sobre 9.780 LDC: E = 26,31 personas-mes, D = 8,66 meses, P = 3,04 personas (informe, punto 2.2).

Fuente: Informe final, punto 2.1. Ruta crítica: todas las actividades salvo A05, A06 y A13.

| ID | Actividad | Fase | Días | Predecesoras | Responsable |
|---|---|---|---|---|---|
| A01 | Relevamiento del caso de estudio y entrevistas con los operadores | Inicio | 8 | — | Equipo |
| A02 | Definición del alcance, actores y catálogo de casos de uso | Inicio | 6 | A01 | Equipo |
| A03 | Requisitos funcionales y no funcionales | Inicio | 6 | A02 | Equipo |
| A04 | Diagramas de casos de uso y especificaciones (Larman) | Elaboración | 12 | A03 | Equipo |
| A05 | Estimación, plan de calidad, análisis de riesgos y presupuesto | Elaboración | 12 | A03 | Equipo |
| A06 | Diagramas de actividades | Elaboración | 8 | A04 | Equipo |
| A07 | Diagrama de clases y patrones de diseño | Elaboración | 12 | A04 | Equipo |
| A08 | Mapeo relacional y diccionario de datos | Elaboración | 8 | A07 | Equipo |
| A09 | Componentes, despliegue y entorno base (Docker, Django, Git, CI) | Elaboración | 15 | A08 | Equipo |
| A10 | Prototipo ejecutable y revisión de la arquitectura | Elaboración | 8 | A05, A06, A09 | Equipo |
| A11 | Base del sistema: modelos, migraciones, inicio de sesión, roles y parámetros | Construcción C1 | 10 | A10 | Equipo |
| A12 | Módulo Kardex y Contratos (CU-01 a CU-03) | Construcción C1 | 30 | A11 | Quina |
| A13 | Módulo Seguro de Salud CPS (CU-04) | Construcción C1 | 25 | A11 | Rivera |
| A14 | Módulo Planillas de Sueldos (CU-05 a CU-07) | Construcción C1 | 30 | A11 | Trujillo |
| A15 | Integración y pruebas de la iteración C1 | Construcción C1 | 10 | A12, A13, A14 | Equipo |
| A16 | Módulo Vacaciones y Lactancias (CU-08 y CU-09) | Construcción C2 | 28 | A15 | Rivera |
| A17 | Módulo Finiquitos y Evaluaciones (CU-10 y CU-11) | Construcción C2 | 28 | A15 | Trujillo |
| A18 | Administración y reportes (CU-12 a CU-15) | Construcción C2 | 28 | A15 | Quina |
| A19 | Integración, pruebas de carga y de seguridad | Construcción C2 | 10 | A16, A17, A18 | Equipo |
| A20 | Manual de usuario y documentación técnica | Construcción C2 | 7 | A19 | Equipo |
| A21 | Migración de datos del personal activo | Transición | 6 | A20 | Equipo |
| A22 | Pruebas de aceptación con los operadores | Transición | 8 | A21 | Equipo |
| A23 | Capacitación de los operadores | Transición | 4 | A22 | Equipo |
| A24 | Puesta en producción y cierre del proyecto | Transición | 2 | A23 | Equipo |
