#!/usr/bin/env python3
"""Resume asistencias, faltas y porcentaje de asistencia desde un CSV."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict

PRESENT_VALUES = {"p", "presente", "1", "si", "sí", "yes", "y"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="CSV con columnas nombre,fecha,estado")
    parser.add_argument("--output", default="resumen_asistencia.csv")
    parser.add_argument("--min-percent", type=float, default=80.0, help="Umbral de alerta")
    args = parser.parse_args()

    stats = defaultdict(lambda: {"total": 0, "presentes": 0})

    with open(args.input, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"nombre", "fecha", "estado"}
        if not required.issubset(set(reader.fieldnames or [])):
            parser.error("El CSV debe contener: nombre,fecha,estado")

        for row in reader:
            name = row["nombre"].strip()
            if not name:
                continue
            stats[name]["total"] += 1
            if row["estado"].strip().lower() in PRESENT_VALUES:
                stats[name]["presentes"] += 1

    output = []
    for name, values in sorted(stats.items()):
        total = values["total"]
        presentes = values["presentes"]
        faltas = total - presentes
        pct = (presentes / total * 100.0) if total else 0.0
        output.append(
            {
                "nombre": name,
                "clases": total,
                "asistencias": presentes,
                "faltas": faltas,
                "porcentaje_asistencia": round(pct, 2),
                "alerta": "SI" if pct < args.min_percent else "NO",
            }
        )

    fields = ["nombre", "clases", "asistencias", "faltas", "porcentaje_asistencia", "alerta"]
    with open(args.output, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)

    print(f"Generado: {args.output} ({len(output)} estudiantes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
