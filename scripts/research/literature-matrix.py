#!/usr/bin/env python3
"""Crea una matriz de revisión de literatura en CSV a partir de una plantilla o archivo existente."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

DEFAULT_COLUMNS = [
    "id",
    "autor_anio",
    "titulo",
    "objetivo",
    "metodologia",
    "muestra",
    "variables",
    "hallazgos",
    "limitaciones",
    "doi_url",
    "notas",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="matriz_literatura.csv")
    parser.add_argument("--rows", type=int, default=20, help="Filas vacías iniciales")
    args = parser.parse_args()

    if args.rows < 0:
        parser.error("--rows no puede ser negativo.")

    path = Path(args.output)
    if path.exists():
        parser.error(f"El archivo ya existe: {path}")

    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=DEFAULT_COLUMNS)
        writer.writeheader()
        for index in range(1, args.rows + 1):
            row = {column: "" for column in DEFAULT_COLUMNS}
            row["id"] = index
            writer.writerow(row)

    print(f"Generado: {path} ({args.rows} filas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
