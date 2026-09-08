# Academic Automation Kit

> Automatizaciones abiertas para ahorrar tiempo en tareas repetitivas de estudiantes, docentes e investigadores universitarios.

Academic Automation Kit reúne scripts pequeños, auditables y reutilizables para organización académica, evaluación, asistencia, investigación, limpieza de datos y preparación de laboratorios.

## Objetivos

- Reducir trabajo manual repetitivo.
- Priorizar scripts fáciles de entender y adaptar.
- Funcionar localmente siempre que sea posible.
- Proteger datos académicos y credenciales.
- Mantener IA como capa opcional de ayuda, no como ejecutor libre de acciones privilegiadas.
- Servir tanto para usuarios no técnicos como para quienes quieran aprender automatización.

## Catálogo inicial

| Área | Automatización | Uso |
|---|---|---|
| Estudiantes | Semester Folder Builder | Crea carpetas ordenadas por materia y tipo de evidencia |
| Estudiantes | Assignment Renamer | Renombra entregas con una convención consistente |
| Estudiantes | Deadline Planner | Convierte un CSV de entregas en un calendario `.ics` |
| Docentes | Gradebook Calculator | Calcula calificaciones ponderadas y detecta faltantes |
| Docentes | Attendance Summary | Resume asistencias, faltas y porcentajes |
| Docentes | Random Team Maker | Forma equipos reproducibles sin hojas de cálculo manuales |
| Docentes | Rubric Generator | Genera rúbricas Markdown desde una especificación CSV |
| Investigación | Citation Deduplicator | Detecta referencias bibliográficas repetidas |
| Investigación | Literature Matrix | Construye una matriz de revisión de literatura |
| Datos | CSV Cleaner | Normaliza encabezados, espacios y columnas vacías |
| Datos | Student Data Anonymizer | Seudonimiza identificadores antes de analizar datos |
| Laboratorios | MySQL Smart Setup | Diagnostica puertos/software, instala MySQL y configura FEDERATED/LAN |

## Estructura

```text
.
├─ scripts/
│  ├─ students/
│  ├─ teachers/
│  ├─ research/
│  ├─ data/
│  └─ labs/
├─ docs/
├─ examples/
├─ .github/workflows/
├─ catalog.json
├─ CONTRIBUTING.md
├─ SECURITY.md
└─ LICENSE
```

## Principios de seguridad

Los scripts que cambian el sistema deben validar el estado previo, usar mínimos privilegios, crear respaldo cuando corresponda y evitar exponer servicios a Internet por defecto. Los scripts de datos no deben subir información estudiantil a servicios externos automáticamente.

## Requisitos

La mayoría de herramientas usan Python 3.10+ o PowerShell 5.1+. Cada script incluye ayuda mediante `--help` o parámetros documentados.

## Contribuir

Se aceptan automatizaciones útiles para educación superior siempre que incluyan validaciones, documentación, ejemplo de uso y no contengan datos personales ni secretos.

## Licencia

MIT. Consulta `LICENSE`.
