#!/usr/bin/env python3
"""Seudonimiza columnas identificadoras de un CSV antes de análisis o demostraciones."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


def token(value: str, salt: str, length: int) -> str:
    digest = hashlib.sha256((salt + "\0" + value).encode("utf-8")).hexdigest()
    return digest[:length]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--columns", required=True, help="Columnas separadas por coma, ej. nombre,matricula,email")
    parser.add_argument("--salt", required=True, help="Secreto local; no lo guardes en el repositorio")
    parser.add_argument("--output", default="datos_anonimizados.csv")
    parser.add_argument("--length", type=int, default=12)
    args = parser.parse_args()

    source = Path(args.input)
    if not source.is_file():
        parser.error(f"No existe: {source}")
    if args.length < 8:
        parser.error("Usa --length de al menos 8 caracteres.")

    columns = [column.strip() for column in args.columns.split(",") if column.strip()]
    if not columns:
        parser.error("Debes indicar al menos una columna.")

    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing = [column for column in columns if column not in fields]
        if missing:
            parser.error("No existen las columnas: " + ", ".join(missing))
        rows = list(reader)

    for row in rows:
        for column in columns:
            raw = (row.get(column) or "").strip()
            row[column] = f"anon_{token(raw, args.salt, args.length)}" if raw else ""

    destination = Path(args.output)
    if destination.resolve() == source.resolve():
        parser.error("El archivo de salida no puede sobrescribir el original.")

    with destination.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generado: {destination} ({len(rows)} filas seudonimizadas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
