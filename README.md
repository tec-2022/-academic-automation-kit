# Academic Automation Kit

[![Validate scripts](https://github.com/tec-2022/-academic-automation-kit/actions/workflows/validate.yml/badge.svg)](https://github.com/tec-2022/-academic-automation-kit/actions/workflows/validate.yml)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![PowerShell](https://img.shields.io/badge/PowerShell-5.1%2B-blue.svg)

> Automatizaciones abiertas para ahorrar tiempo en tareas repetitivas de estudiantes, docentes e investigadores universitarios.

**Academic Automation Kit** reúne scripts pequeños, auditables y reutilizables para organización académica, evaluación, asistencia, investigación, limpieza de datos y preparación de laboratorios. La prioridad es que cada herramienta sea fácil de entender, segura por defecto y útil incluso para personas que no se dedican a programación.

## Inicio rápido

```bash
git clone https://github.com/tec-2022/-academic-automation-kit.git
cd ./-academic-automation-kit
python toolkit.py list
```

El launcher central permite descubrir herramientas por audiencia o categoría:

```bash
python toolkit.py list --audience students
python toolkit.py list --audience teachers
python toolkit.py list --category research
```

Ejemplo de ejecución:

```bash
python toolkit.py run gradebook-calculator -- examples/gradebook.csv --weights tareas=30,examen=40,proyecto=30 --output resultado.csv
```

Consulta [`docs/USAGE.md`](docs/USAGE.md) para más ejemplos.

## Automatizaciones incluidas

| Área | Automatización | Uso |
|---|---|---|
| Estudiantes | Semester Folder Builder | Crea carpetas ordenadas por materia y tipo de evidencia |
| Estudiantes | Assignment Renamer | Renombra entregas con una convención consistente y modo `--dry-run` |
| Estudiantes | Deadline Planner | Convierte un CSV de entregas en un calendario `.ics` con recordatorios |
| Docentes | Gradebook Calculator | Calcula calificaciones ponderadas y reporta datos faltantes |
| Docentes | Attendance Summary | Resume asistencias, faltas, porcentajes y alertas |
| Docentes | Random Team Maker | Forma equipos reproducibles mediante una semilla opcional |
| Docentes | Rubric Generator | Genera rúbricas Markdown desde una especificación CSV |
| Investigación | Citation Deduplicator | Detecta referencias bibliográficas repetidas |
| Investigación | Literature Matrix | Genera una matriz estructurada de revisión de literatura |
| Datos | CSV Cleaner | Normaliza encabezados, espacios, filas y columnas vacías sin sobrescribir el original |
| Datos | Student Data Anonymizer | Seudonimiza identificadores antes de análisis o demostraciones |
| Laboratorios | MySQL Smart Setup | Detecta conflictos, instala MySQL Community y configura FEDERATED/LAN de forma aislada |

## Estructura

```text
.
├─ toolkit.py                    # Launcher central
├─ catalog.json                  # Catálogo legible por máquinas
├─ scripts/
│  ├─ students/
│  ├─ teachers/
│  ├─ research/
│  ├─ data/
│  └─ labs/
├─ examples/                     # Datos ficticios para probar scripts
├─ tests/                        # Smoke tests sin datos reales
├─ docs/
│  ├─ USAGE.md
│  └─ ROADMAP.md
├─ .github/workflows/validate.yml
├─ CONTRIBUTING.md
├─ SECURITY.md
└─ LICENSE
```

## Diseño y seguridad

Los scripts que modifican el sistema validan el estado previo, usan mínimos privilegios y evitan exponer servicios a Internet por defecto. Los scripts de datos no suben información estudiantil a servicios externos. Los ejemplos contienen datos ficticios.

La IA, cuando se incorpore a una automatización, será **opcional** y funcionará como capa de diagnóstico o explicación. No tendrá una ruta para ejecutar comandos arbitrarios con privilegios.

## Calidad

Cada push ejecuta GitHub Actions en Linux y Windows para:

- compilar todos los scripts Python;
- ejecutar smoke tests de las automatizaciones principales;
- analizar sintaxis de PowerShell.

## Contribuir

Se aceptan automatizaciones útiles para educación superior siempre que incluyan validaciones, documentación, ejemplo de uso y no contengan datos personales ni secretos. Consulta [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Roadmap

El siguiente nivel contempla un launcher gráfico, más herramientas para evaluación e investigación, preparación de laboratorios y asistencia de IA local mediante un flujo seguro. Consulta [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Licencia

MIT © 2026 Fredy Luis Vidalón Lozano.
