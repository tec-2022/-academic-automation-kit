#!/usr/bin/env python3
"""Detecta referencias bibliográficas duplicadas mediante normalización conservadora."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def normalize(line: str) -> str:
    line = line.strip().lower()
    line = re.sub(r"\s+", " ", line)
    line = re.sub(r"[.,;:]+$", "", line)
    return line


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Archivo TXT con una referencia por línea")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.is_file():
        parser.error(f"No existe: {path}")

    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    seen: dict[str, int] = {}
    duplicates: list[tuple[int, int, str]] = []

    for index, line in enumerate(lines, start=1):
        key = normalize(line)
        if key in seen:
            duplicates.append((seen[key], index, line))
        else:
            seen[key] = index

    if not duplicates:
        print("No se detectaron duplicados exactos después de normalizar.")
        return 0

    print(f"Duplicados encontrados: {len(duplicates)}")
    for first, current, line in duplicates:
        print(f"- líneas {first} y {current}: {line}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
