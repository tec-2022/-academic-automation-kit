#!/usr/bin/env python3
"""Calcula calificaciones ponderadas desde un CSV y reporta datos faltantes."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_weights(text: str) -> dict[str, float]:
    weights: dict[str, float] = {}
    for part in text.split(","):
        if "=" not in part:
            raise ValueError(f"Peso inválido: {part}")
        name, value = part.split("=", 1)
        weights[name.strip()] = float(value)
    total = sum(weights.values())
    if abs(total - 100.0) > 0.001:
        raise ValueError(f"Los pesos deben sumar 100; actualmente suman {total}.")
    return weights


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="CSV con columna nombre y columnas de evaluación")
    parser.add_argument("--weights", required=True, help="Ej. tareas=30,examen=40,proyecto=30")
    parser.add_argument("--output", default="calificaciones_finales.csv")
    parser.add_argument("--missing", choices=["zero", "ignore", "error"], default="zero")
    args = parser.parse_args()

    try:
        weights = parse_weights(args.weights)
    except ValueError as exc:
        parser.error(str(exc))

    with open(args.input, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = set(reader.fieldnames or [])

    required = {"nombre", *weights.keys()}
    missing_columns = sorted(required - fields)
    if missing_columns:
        parser.error("Faltan columnas: " + ", ".join(missing_columns))

    output_rows: list[dict[str, object]] = []
    for row in rows:
        missing_values: list[str] = []
        earned = 0.0
        active_weight = 0.0

        for column, weight in weights.items():
            raw = (row.get(column) or "").strip()
            if not raw:
                missing_values.append(column)
                if args.missing == "error":
                    parser.error(f"Falta {column} para {row.get('nombre', '')}")
                if args.missing == "zero":
                    active_weight += weight
                continue

            score = float(raw)
            if not 0 <= score <= 100:
                parser.error(f"{column} fuera de 0-100 para {row.get('nombre', '')}: {score}")
            earned += score * weight
            active_weight += weight

        final = (earned / active_weight) if active_weight else 0.0
        output_rows.append(
            {
                "nombre": row["nombre"],
                "calificacion_final": round(final, 2),
                "datos_faltantes": ";".join(missing_values),
            }
        )

    with open(args.output, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["nombre", "calificacion_final", "datos_faltantes"])
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Generado: {args.output} ({len(output_rows)} estudiantes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
