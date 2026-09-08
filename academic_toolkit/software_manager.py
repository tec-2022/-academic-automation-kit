"""Winget-backed software management with explicit verification."""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path

ACCEPT = ["--accept-source-agreements"]

def winget_available() -> bool:
    return shutil.which("winget") is not None

def _run(args: list[str], timeout: int = 1800) -> subprocess.CompletedProcess:
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout,
                          encoding="utf-8", errors="replace")

def verify_package(package_id: str) -> bool:
    if not winget_available():
        return False
    result = _run(["winget", "show", "--id", package_id, "--exact", *ACCEPT], 60)
    return result.returncode == 0

def is_installed(package_id: str) -> bool:
    if not winget_available():
        return False
    result = _run(["winget", "list", "--id", package_id, "--exact", *ACCEPT], 60)
    return result.returncode == 0 and package_id.casefold() in result.stdout.casefold()

def install(package_id: str) -> subprocess.CompletedProcess:
    if not verify_package(package_id):
        raise ValueError(f"Winget package is not currently resolvable: {package_id}")
    if is_installed(package_id):
        return _run(["winget", "list", "--id", package_id, "--exact", *ACCEPT], 60)
    return _run(["winget", "install", "--id", package_id, "--exact", "--silent",
                 "--accept-package-agreements", "--accept-source-agreements"])

def uninstall(package_id: str) -> subprocess.CompletedProcess:
    if not is_installed(package_id):
        raise ValueError(f"Package is not installed: {package_id}")
    return _run(["winget", "uninstall", "--id", package_id, "--exact", "--silent",
                 "--accept-source-agreements"])

def load_profile(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)

def audit_profile(profile: dict) -> list[dict]:
    """Resolve every package before the UI offers an installation button."""
    return [{**pkg, "available": verify_package(pkg["id"]),
             "installed": is_installed(pkg["id"])} for pkg in profile["packages"]]
