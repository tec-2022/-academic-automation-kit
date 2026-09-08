#!/usr/bin/env python3
"""Genera una rúbrica Markdown a partir de un CSV de criterios y niveles."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="CSV con columnas criterio,peso y una o más columnas de nivel")
    parser.add_argument("--output", default="rubrica.md")
    parser.add_argument("--title", default="Rúbrica de evaluación")
    args = parser.parse_args()

    with open(args.input, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if "criterio" not in fields or "peso" not in fields:
            parser.error("El CSV debe incluir criterio,peso y al menos una columna de nivel.")
        level_columns = [field for field in fields if field not in {"criterio", "peso"}]
        if not level_columns:
            parser.error("Agrega al menos una columna de nivel, por ejemplo excelente,bien,suficiente.")
        rows = list(reader)

    try:
        total_weight = sum(float((row.get("peso") or "0").strip()) for row in rows)
    except ValueError:
        parser.error("Los pesos deben ser numéricos.")

    headers = ["Criterio", "Peso", *level_columns]
    lines = [f"# {args.title}", "", f"**Peso total:** {total_weight:g}", "", "| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]

    for row in rows:
        cells = [
            (row.get("criterio") or "").strip(),
            (row.get("peso") or "").strip(),
            *[(row.get(col) or "").strip().replace("|", "\\|") for col in level_columns],
        ]
        lines.append("| " + " | ".join(cells) + " |")

    Path(args.output).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generado: {args.output}")
    if abs(total_weight - 100.0) > 0.001:
        print(f"AVISO: los pesos suman {total_weight:g}, no 100.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
