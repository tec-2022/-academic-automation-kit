# Contributing

Gracias por mejorar Academic Automation Kit.

## Qué buscamos

Automatizaciones pequeñas y útiles para educación superior: organización académica, docencia, evaluación, investigación, análisis de datos y preparación de laboratorios.

## Requisitos para una nueva automatización

1. Ubícala en la categoría correcta dentro de `scripts/`.
2. Incluye ayuda de línea de comandos o parámetros claros.
3. Valida entradas antes de modificar archivos o configuración.
4. Evita dependencias innecesarias.
5. No incluyas datos personales reales, contraseñas, tokens ni API keys.
6. Documenta qué modifica y cómo revertirlo cuando aplique.
7. Añade una entrada en `catalog.json`.
8. Si requiere privilegios de administrador, indícalo explícitamente.

## Estilo

- Python: 3.10+, biblioteca estándar cuando sea razonable, `argparse` para CLI.
- PowerShell: `Set-StrictMode`, `$ErrorActionPreference = 'Stop'`, validaciones y mensajes comprensibles.
- Nombres de archivo en `kebab-case`.
- Nada de acciones destructivas silenciosas.

## IA

Las funciones de IA deben ser opcionales. No deben enviar datos académicos a terceros sin una acción explícita del usuario. La IA puede explicar, clasificar o recomendar; las operaciones privilegiadas deben permanecer en código determinista y validado.
