#!/usr/bin/env python3
"""Prepare a Windows PC according to a university career profile.

Created by Fredy Luis Vidalón Lozano.
No package is installed unless it resolves through Winget at runtime.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from academic_toolkit.career_engine import build_plan, get_career, list_careers
from academic_toolkit.health_checks import check_packages
from academic_toolkit.software_manager import install, verify_package, is_installed
from academic_toolkit.system_prepare import clean_temporaries


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepara una PC según la carrera, con diagnóstico antes de instalar.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("careers", help="Lista las carreras disponibles")

    plan = sub.add_parser("plan", help="Audita la PC y crea un plan sin instalar")
    plan.add_argument("career")
    plan.add_argument("--tier", action="append", choices=["essential", "recommended", "specialized"])
    plan.add_argument("--offline", action="store_true", help="No consulta Winget")

    prepare = sub.add_parser("prepare", help="Limpia temporales seguros, audita e instala paquetes válidos")
    prepare.add_argument("career")
    prepare.add_argument("--tier", action="append", choices=["essential", "recommended", "specialized"])
    prepare.add_argument("--yes", action="store_true", help="Confirma el plan sin preguntar")
    prepare.add_argument("--skip-clean", action="store_true")

    args = parser.parse_args()
    if args.command == "careers":
        for item in list_careers():
            print(f"{item['id']}: {item['name']} — {item['description']}")
        return 0

    tiers = args.tier or ["essential", "recommended"]
    if args.command == "plan":
        print(json.dumps(build_plan(args.career, tiers, online_audit=not args.offline), ensure_ascii=False, indent=2))
        return 0

    if not args.skip_clean:
        preview = clean_temporaries(dry_run=True)
        print(f"Temporales seguros detectados: {preview.scanned}; potencialmente liberables: {preview.bytes_freed / (1024**2):.1f} MB")

    plan_data = build_plan(args.career, tiers, online_audit=True)
    print(f"\nCarrera: {plan_data['career']['name']}")
    for item in plan_data["items"]:
        state = "instalado" if item["installed"] else ("disponible" if item["available"] else "NO disponible")
        compat = "" if item["compatible"] else f"; incompatible: {item['reason']}"
        print(f"- {item['name']} [{item['tier']}]: {state}{compat}")

    blocked = [i for i in plan_data["items"] if not i["available"] and not i["installed"]]
    incompatible = [i for i in plan_data["items"] if not i["compatible"]]
    if blocked:
        print("\nSe omitirán paquetes que Winget no puede resolver en este momento.")
    if incompatible:
        print("Se omitirán paquetes que no cumplen los requisitos del equipo.")

    installable = [i for i in plan_data["items"] if i["compatible"] and i["available"] and not i["installed"]]
    if not installable:
        print("\nNo hay paquetes pendientes instalables.")
        return 0

    if not args.yes:
        answer = input(f"\n¿Instalar {len(installable)} paquete(s)? [s/N]: ").strip().casefold()
        if answer not in {"s", "si", "sí", "y", "yes"}:
            print("Cancelado sin cambios.")
            return 0

    if not args.skip_clean:
        cleaned = clean_temporaries(dry_run=False)
        print(f"Limpieza: {cleaned.removed} elementos procesados; {cleaned.bytes_freed / (1024**2):.1f} MB liberables/procesados.")

    failed = 0
    career = get_career(args.career)
    package_meta = {p["id"]: p for p in career["packages"]}
    installed_meta = []
    for item in installable:
        package_id = item["package_id"]
        print(f"\nInstalando {item['name']}...")
        if not verify_package(package_id):
            print("  omitido: el paquete dejó de estar disponible en Winget")
            failed += 1
            continue
        result = install(package_id)
        if result.returncode != 0 and not is_installed(package_id):
            print(f"  error ({result.returncode}): {result.stderr.strip()[:500]}")
            failed += 1
            continue
        print("  instalación verificada por Winget")
        installed_meta.append(package_meta[package_id])

    health = check_packages(installed_meta)
    if health:
        print("\nHealth checks:")
        for check in health:
            print(f"- {check['name']}: {'OK' if check['ok'] else 'NECESITA ATENCIÓN'}")
            if not check["ok"] and check["error"]:
                print(f"  {check['error']}")
                failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
