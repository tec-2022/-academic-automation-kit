# Academic Automation Kit

[![Validate scripts](https://github.com/tec-2022/-academic-automation-kit/actions/workflows/validate.yml/badge.svg)](https://github.com/tec-2022/-academic-automation-kit/actions/workflows/validate.yml)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![PowerShell](https://img.shields.io/badge/PowerShell-5.1%2B-blue.svg)

> Herramienta creada y mantenida por **Fredy Luis Vidalón Lozano** para preparar, configurar, diagnosticar y automatizar computadoras en contextos universitarios.

**Academic Automation Kit** incluye una interfaz gráfica funcional para Windows, perfiles por carrera, auditoría del equipo antes de instalar, validación de paquetes mediante Winget, limpieza segura de temporales, comprobaciones posteriores a la instalación, diagnóstico de conflictos y una capa de IA local opcional que nunca sustituye al motor determinista.

## Autor

**Fredy Luis Vidalón Lozano**  
Creador y desarrollador de Academic Automation Kit.

Repositorio: `tec-2022/-academic-automation-kit`

## Interfaz gráfica

La aplicación de escritorio ya está implementada con Python + Tkinter y no requiere dependencias gráficas externas. En Windows puede abrirse con doble clic en:

```text
Abrir-Academic-Toolkit.bat
```

O desde terminal:

```powershell
python start_gui.py
```

La interfaz incluye funciones reales, no tarjetas vacías:

- **Inicio:** accesos directos y diagnóstico básico del equipo.
- **Preparar mi PC:** selección de carrera, niveles de software, auditoría de Winget, compatibilidad, instalación y health checks.
- **Programas:** búsqueda real en Winget, instalación y desinstalación del paquete seleccionado.
- **Limpieza:** vista previa de temporales seguros antes de eliminarlos.
- **Asistente:** predicción local inmediata y uso opcional de IA local mediante Ollama cuando las reglas no bastan.
- **IA local opcional:** valida Ollama en Winget antes de instalar y descarga el modelo ligero solo con confirmación del usuario.

Las operaciones lentas se ejecutan en segundo plano para que la ventana no quede congelada durante búsquedas, auditorías o instalaciones.

## Preparar una PC según la carrera

El flujo principal es: **detectar → auditar → mostrar plan → confirmar → preparar → instalar → verificar**.

También puede usarse por terminal:

```powershell
python scripts/labs/career-pc-prep.py careers
python scripts/labs/career-pc-prep.py plan informatics-engineering
python scripts/labs/career-pc-prep.py prepare informatics-engineering
```

El comando `plan` no instala nada. Antes de ofrecer un paquete, el motor comprueba en tiempo de ejecución que su identificador exista en Winget y detecta si ya está instalado. Los paquetes incompatibles o no resolubles se bloquean en lugar de simular una instalación.

### Perfiles incluidos

| Carrera / perfil | Enfoque principal |
|---|---|
| Ingeniería Informática | Programación, web, bases de datos, APIs y contenedores |
| Ingeniería en Sistemas Computacionales | Java, desarrollo, bases de datos, APIs y contenedores |
| Ingeniería Industrial | Python, R, RStudio, análisis y documentación |
| Ingeniería Civil | FreeCAD, QGIS, modelado, automatización y documentación |
| Ingeniería Mecatrónica | Arduino, KiCad, FreeCAD, Python y control de versiones |
| Ingeniería Electrónica | PCB, microcontroladores, programación y CAD |
| Ciencia de Datos | Python, Miniconda, R, RStudio y entornos reproducibles |

Cada perfil separa herramientas en `essential`, `recommended` y `specialized`. Los paquetes especializados pueden declarar requisitos de RAM o virtualización para evitar instalaciones inadecuadas.

## Preparación segura

Antes de una preparación completa, el motor puede revisar y limpiar exclusivamente ubicaciones temporales seguras. No elimina Documentos, Descargas, Escritorio, perfiles de navegador ni carpetas arbitrarias de aplicaciones. La limpieza muestra primero una estimación y después procesa únicamente ubicaciones permitidas.

Para instalaciones relevantes, el resultado de Winget no se considera suficiente: cuando existe un `health_check`, el toolkit intenta ejecutar la herramienta instalada (`python --version`, `git --version`, `node --version`, etc.) y marca **OK** o **NECESITA ATENCIÓN**.

## MySQL y conflictos reales

El perfil de informática integra MySQL como paquete diagnosticable. El módulo MySQL Smart Setup permanece separado porque antes de configurarlo debe revisar XAMPP/MariaDB/MySQL existentes, servicios, puertos y exposición de red. El objetivo es no sobrescribir una instalación previa ni asumir que el puerto 3306 está libre.

## IA local opcional y rápida

La IA no es obligatoria. Las acciones conocidas se resuelven primero mediante reglas y funciones auditables. La IA local solo entra como fallback para interpretar lenguaje natural ambiguo, devuelve intenciones permitidas y no recibe una ruta para ejecutar comandos arbitrarios como administrador.

El adaptador local está configurado para baja latencia: contexto pequeño, salida corta, temperatura 0, `keep_alive` y modelo ligero configurable. Si el usuario decide no descargar IA, el resto de la plataforma sigue funcionando.

## Inicio rápido del catálogo clásico

```bash
git clone https://github.com/tec-2022/-academic-automation-kit.git
cd ./-academic-automation-kit
python toolkit.py list
```

El launcher de terminal también expone `career-pc-prep` en la categoría `pc-preparation`.

## Automatizaciones adicionales

| Área | Automatización | Uso |
|---|---|---|
| Preparación PC | Career PC Prep | Audita y prepara Windows según carrera |
| Estudiantes | Semester Folder Builder | Crea carpetas ordenadas por materia |
| Estudiantes | Assignment Renamer | Renombra entregas con modo `--dry-run` |
| Estudiantes | Deadline Planner | Genera calendarios `.ics` |
| Docentes | Gradebook Calculator | Calcula calificaciones ponderadas |
| Docentes | Attendance Summary | Resume asistencia y alertas |
| Docentes | Random Team Maker | Forma equipos reproducibles |
| Docentes | Rubric Generator | Genera rúbricas Markdown |
| Investigación | Citation Deduplicator | Detecta referencias repetidas |
| Investigación | Literature Matrix | Genera matrices de literatura |
| Datos | CSV Cleaner | Limpia CSV sin sobrescribir originales |
| Datos | Student Data Anonymizer | Seudonimiza identificadores |
| Laboratorios | MySQL Smart Setup | Prepara MySQL Community de forma aislada |

## Estructura

```text
.
├─ Abrir-Academic-Toolkit.bat    # Lanzador de Windows
├─ start_gui.py                  # Entrada de la app gráfica
├─ toolkit.py
├─ catalog.json
├─ academic_toolkit/
│  ├─ desktop_app.py
│  ├─ careers.json
│  ├─ career_engine.py
│  ├─ health_checks.py
│  ├─ software_manager.py
│  ├─ system_prepare.py
│  ├─ predictor.py
│  └─ ai.py
├─ scripts/
│  ├─ students/
│  ├─ teachers/
│  ├─ research/
│  ├─ data/
│  └─ labs/
├─ tests/
├─ docs/
└─ .github/workflows/validate.yml
```

## Seguridad y calidad

Los cambios de sistema deben validarse antes de ejecutarse, operar con mínimos privilegios y evitar abrir servicios a Internet por defecto. Los ejemplos no contienen información académica real y la IA no puede convertirse en un ejecutor privilegiado de comandos generados.

GitHub Actions compila `academic_toolkit`, scripts y tests, valida el JSON de perfiles, ejecuta smoke tests y analiza la sintaxis de PowerShell en Windows.

## Licencia

MIT © 2026 **Fredy Luis Vidalón Lozano**.
