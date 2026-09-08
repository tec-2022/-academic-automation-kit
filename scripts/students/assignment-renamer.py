#!/usr/bin/env python3
"""Renombra entregas académicas con una convención consistente."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


def clean(text: str) -> str:
    text = re.sub(r'[\\/:*?"<>|]+', "_", text.strip())
    text = re.sub(r"\s+", "_", text)
    return text.strip("_")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="Archivo a renombrar")
    parser.add_argument("--subject", required=True, help="Materia")
    parser.add_argument("--activity", required=True, help="Actividad")
    parser.add_argument("--student", required=True, help="Nombre o identificador")
    parser.add_argument("--date", required=True, help="Fecha YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Muestra el cambio sin renombrar")
    args = parser.parse_args()

    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        parser.error(f"No existe el archivo: {source}")

    parts = [clean(args.subject), clean(args.activity), clean(args.student), args.date]
    if any(not part for part in parts):
        parser.error("Los campos no pueden quedar vacíos después de normalizarlos.")

    destination = source.with_name("__".join(parts) + source.suffix.lower())

    if destination.exists() and destination != source:
        parser.error(f"El archivo destino ya existe: {destination}")

    if args.dry_run:
        print(f"{source.name} -> {destination.name}")
        return 0

    source.rename(destination)
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
