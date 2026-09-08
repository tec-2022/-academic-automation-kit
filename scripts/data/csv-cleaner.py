#!/usr/bin/env python3
"""Limpia un CSV académico sin modificar el archivo original."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def clean_header(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"[^a-z0-9_áéíóúüñ]", "", value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--output", default="datos_limpios.csv")
    parser.add_argument("--keep-empty-columns", action="store_true")
    args = parser.parse_args()

    source = Path(args.input)
    if not source.is_file():
        parser.error(f"No existe: {source}")

    with source.open(newline="", encoding="utf-8-sig") as handle:
        raw = list(csv.reader(handle))

    raw = [row for row in raw if any(cell.strip() for cell in row)]
    if not raw:
        parser.error("El CSV está vacío.")

    headers = [clean_header(header) for header in raw[0]]
    width = len(headers)
    body = [(row + [""] * width)[:width] for row in raw[1:]]

    keep = list(range(width))
    if not args.keep_empty_columns:
        keep = [
            index
            for index in range(width)
            if headers[index] or any(row[index].strip() for row in body)
        ]

    clean_headers = [headers[index] or f"columna_{index + 1}" for index in keep]
    clean_rows = [[row[index].strip() for index in keep] for row in body]

    destination = Path(args.output)
    if destination.resolve() == source.resolve():
        parser.error("El archivo de salida no puede ser el mismo que el original.")

    with destination.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(clean_headers)
        writer.writerows(clean_rows)

    print(f"Generado: {destination} ({len(clean_rows)} filas, {len(clean_headers)} columnas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
