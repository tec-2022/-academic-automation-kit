#!/usr/bin/env python3
"""Forma equipos aleatorios reproducibles a partir de una lista o CSV."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


def load_names(path: Path, column: str) -> list[str]:
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if column not in (reader.fieldnames or []):
                raise ValueError(f"No existe la columna '{column}'.")
            names = [(row.get(column) or "").strip() for row in reader]
    else:
        names = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return [name for name in names if name]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="TXT (un nombre por línea) o CSV")
    parser.add_argument("--column", default="nombre")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--teams", type=int, help="Número de equipos")
    group.add_argument("--size", type=int, help="Tamaño aproximado por equipo")
    parser.add_argument("--seed", type=int, default=None, help="Semilla para repetir el sorteo")
    parser.add_argument("--output", default="equipos.csv")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.is_file():
        parser.error(f"No existe: {path}")

    try:
        names = load_names(path, args.column)
    except ValueError as exc:
        parser.error(str(exc))

    if len(names) < 2:
        parser.error("Se necesitan al menos dos participantes.")

    rng = random.Random(args.seed)
    rng.shuffle(names)

    team_count = args.teams or max(1, (len(names) + args.size - 1) // args.size)
    if team_count < 1 or team_count > len(names):
        parser.error("El número de equipos debe estar entre 1 y el número de participantes.")

    teams = [[] for _ in range(team_count)]
    for index, name in enumerate(names):
        teams[index % team_count].append(name)

    with open(args.output, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["equipo", "nombre"])
        for number, team in enumerate(teams, start=1):
            for name in team:
                writer.writerow([number, name])

    print(f"Generado: {args.output}")
    for number, team in enumerate(teams, start=1):
        print(f"Equipo {number}: {', '.join(team)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
