# Guía de uso

## 1. Clonar el repositorio

```bash
git clone https://github.com/tec-2022/-academic-automation-kit.git
cd -academic-automation-kit
```

> Como el nombre actual empieza con `-`, algunos shells pueden requerir escribir la ruta con `./` o entre comillas. El repositorio funciona igual.

## 2. Ver el catálogo

```bash
python toolkit.py list
```

Filtrar para estudiantes:

```bash
python toolkit.py list --audience students
```

Filtrar por categoría:

```bash
python toolkit.py list --category grading
```

## 3. Ejecutar desde el launcher

Los argumentos que aparecen después del ID se pasan al script seleccionado.

```bash
python toolkit.py run gradebook-calculator -- examples/gradebook.csv --weights tareas=30,examen=40,proyecto=30 --output resultado.csv
```

También puedes ejecutar cada script directamente.

## Ejemplos

### Crear calendario de entregas

```bash
python scripts/students/deadline-planner.py examples/deadlines.csv --output semestre.ics
```

Importa `semestre.ics` en el calendario que prefieras.

### Calcular calificaciones

```bash
python scripts/teachers/gradebook-calculator.py examples/gradebook.csv --weights tareas=30,examen=40,proyecto=30
```

### Resumir asistencia

```bash
python scripts/teachers/attendance-summary.py examples/attendance.csv --min-percent 80
```

### Formar equipos

Crea `estudiantes.txt` con un nombre por línea y ejecuta:

```bash
python scripts/teachers/random-team-maker.py estudiantes.txt --teams 5 --seed 2026
```

Usar `--seed` permite reproducir exactamente el mismo sorteo.

### Generar rúbrica

```bash
python scripts/teachers/rubric-generator.py examples/rubric.csv --output rubrica.md
```

### Limpiar CSV

```bash
python scripts/data/csv-cleaner.py archivo.csv --output archivo_limpio.csv
```

El script nunca sobrescribe el archivo original.

### Seudonimizar datos estudiantiles

```bash
python scripts/data/student-data-anonymizer.py alumnos.csv --columns nombre,matricula,email --salt "un-secreto-local" --output anon.csv
```

No publiques ni reutilices el valor de `--salt` como contraseña. El propósito es mantener una correspondencia seudónima estable durante un análisis local.

### MySQL Smart Setup

En Windows, abre PowerShell como administrador:

```powershell
.\scripts\labs\mysql-smart-setup\mysql-smart-setup.ps1
```

Lee primero el README dentro de esa carpeta. La automatización puede instalar y configurar software del sistema.
