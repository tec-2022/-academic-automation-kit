"""Career-profile planning engine.

Created by Fredy Luis Vidalón Lozano.
Builds a deterministic preparation plan before anything is installed.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

from .software_manager import verify_package, is_installed

ROOT = Path(__file__).resolve().parent
CAREERS_FILE = ROOT / "careers.json"
TIERS = ("essential", "recommended", "specialized")

@dataclass
class DeviceProfile:
    os_name: str
    architecture: str
    ram_gb: float | None
    free_disk_gb: float
    winget: bool
    virtualization_hint: bool

@dataclass
class PlanItem:
    package_id: str
    name: str
    tier: str
    group: str
    available: bool
    installed: bool
    compatible: bool
    reason: str = ""


def load_careers(path: Path = CAREERS_FILE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_catalog(data)
    return data


def validate_catalog(data: dict) -> None:
    ids: set[str] = set()
    for career in data.get("careers", []):
        cid = career.get("id")
        if not cid or cid in ids:
            raise ValueError(f"Career id invalid or duplicated: {cid!r}")
        ids.add(cid)
        if not career.get("packages"):
            raise ValueError(f"Career without packages: {cid}")
        for package in career["packages"]:
            if not package.get("id") or not package.get("name"):
                raise ValueError(f"Invalid package in {cid}")
            if package.get("tier") not in TIERS:
                raise ValueError(f"Invalid tier for {package.get('id')}")


def list_careers() -> list[dict]:
    return [
        {"id": c["id"], "name": c["name"], "description": c["description"]}
        for c in load_careers()["careers"]
    ]


def get_career(career_id: str) -> dict:
    for career in load_careers()["careers"]:
        if career["id"] == career_id:
            return career
    raise KeyError(f"Unknown career: {career_id}")


def detect_device() -> DeviceProfile:
    free = shutil.disk_usage(Path.home()).free / (1024 ** 3)
    ram = _ram_gb()
    # A portable, non-invasive hint. Full Windows virtualization checks belong
    # to a platform-specific diagnostic before Docker/VM installation.
    virtualization_hint = platform.machine().lower() in {"amd64", "x86_64", "arm64"}
    return DeviceProfile(
        os_name=platform.system(),
        architecture=platform.machine(),
        ram_gb=ram,
        free_disk_gb=round(free, 1),
        winget=shutil.which("winget") is not None,
        virtualization_hint=virtualization_hint,
    )


def build_plan(career_id: str, tiers: Iterable[str] = ("essential", "recommended"), *, online_audit: bool = True) -> dict:
    selected = set(tiers)
    invalid = selected.difference(TIERS)
    if invalid:
        raise ValueError(f"Invalid tiers: {sorted(invalid)}")
    career = get_career(career_id)
    device = detect_device()
    items: list[PlanItem] = []
    for pkg in career["packages"]:
        if pkg["tier"] not in selected:
            continue
        compatible, reason = _compatible(pkg, device)
        available = verify_package(pkg["id"]) if online_audit and device.winget else False
        installed = is_installed(pkg["id"]) if device.winget else False
        items.append(PlanItem(pkg["id"], pkg["name"], pkg["tier"], pkg["group"], available, installed, compatible, reason))
    return {
        "career": {"id": career["id"], "name": career["name"]},
        "device": asdict(device),
        "items": [asdict(item) for item in items],
        "ready_to_install": device.os_name == "Windows" and device.winget and all(i.compatible for i in items),
    }


def _compatible(pkg: dict, device: DeviceProfile) -> tuple[bool, str]:
    req = pkg.get("requires", {})
    required_ram = req.get("ram_gb")
    if required_ram and device.ram_gb is not None and device.ram_gb < required_ram:
        return False, f"requires at least {required_ram} GB RAM"
    if req.get("virtualization") and not device.virtualization_hint:
        return False, "virtualization-capable architecture not detected"
    return True, ""


def _ram_gb() -> float | None:
    try:
        if os.name == "nt":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
            status = MEMORYSTATUSEX()
            status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            return round(status.ullTotalPhys / (1024 ** 3), 1)
        pages = os.sysconf("SC_PHYS_PAGES")
        size = os.sysconf("SC_PAGE_SIZE")
        return round((pages * size) / (1024 ** 3), 1)
    except Exception:
        return None
