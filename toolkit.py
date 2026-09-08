#!/usr/bin/env python3
"""CLI central para descubrir y ejecutar automatizaciones del repositorio."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "catalog.json"


def load_catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def find_automation(catalog: dict, automation_id: str) -> dict:
    for item in catalog.get("automations", []):
        if item.get("id") == automation_id:
            return item
    raise KeyError(automation_id)


def command_for(path: Path) -> list[str]:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return [sys.executable, str(path)]
    if suffix == ".ps1":
        shell = shutil.which("pwsh") or shutil.which("powershell")
        if not shell:
            raise RuntimeError("No se encontró PowerShell.")
        return [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(path)]
    if suffix in {".bat", ".cmd"} and sys.platform.startswith("win"):
        return ["cmd.exe", "/c", str(path)]
    raise RuntimeError(f"Tipo de automatización no ejecutable directamente: {path}")


def cmd_list(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    items = catalog.get("automations", [])
    if args.audience:
        items = [item for item in items if item.get("audience") in {args.audience, "both"}]
    if args.category:
        items = [item for item in items if item.get("category") == args.category]

    if not items:
        print("No hay automatizaciones que coincidan con el filtro.")
        return 0

    width = max(len(item["id"]) for item in items)
    for item in items:
        print(f"{item['id']:<{width}}  {item.get('audience','-'):<10}  {item.get('category','-'):<12}  {item.get('path','')}")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    try:
        item = find_automation(catalog, args.id)
    except KeyError:
        print(f"No existe la automatización: {args.id}", file=sys.stderr)
        return 2
    print(json.dumps(item, ensure_ascii=False, indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    try:
        item = find_automation(catalog, args.id)
    except KeyError:
        print(f"No existe la automatización: {args.id}", file=sys.stderr)
        return 2

    path = (ROOT / item["path"]).resolve()
    if not path.exists():
        print(f"La ruta del catálogo no existe todavía: {path}", file=sys.stderr)
        return 3
    if path.is_dir():
        print(f"'{args.id}' es una herramienta con carpeta propia. Revisa: {path}")
        return 4

    try:
        command = command_for(path) + list(args.extra)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 5

    print("Ejecutando:", " ".join(command))
    completed = subprocess.run(command, cwd=path.parent)
    return completed.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="Lista automatizaciones")
    list_parser.add_argument("--audience", choices=["students", "teachers", "researchers"])
    list_parser.add_argument("--category")
    list_parser.set_defaults(func=cmd_list)

    info_parser = sub.add_parser("info", help="Muestra una entrada del catálogo")
    info_parser.add_argument("id")
    info_parser.set_defaults(func=cmd_info)

    run_parser = sub.add_parser("run", help="Ejecuta una automatización")
    run_parser.add_argument("id")
    run_parser.add_argument("extra", nargs=argparse.REMAINDER, help="Argumentos que se pasan al script")
    run_parser.set_defaults(func=cmd_run)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
