"""Safe Windows preparation helpers for Academic Automation Kit.

Created by Fredy Luis Vidalón Lozano.
Only cleans user/system temporary locations; it never touches Documents,
Downloads, Desktop, browser profiles or arbitrary application data.
"""
from __future__ import annotations
import ctypes
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

@dataclass
class CleanupResult:
    scanned: int = 0
    removed: int = 0
    failed: int = 0
    bytes_freed: int = 0


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def safe_temp_roots() -> list[Path]:
    roots = [Path(tempfile.gettempdir())]
    windir = os.environ.get("WINDIR")
    if windir and is_admin():
        roots.append(Path(windir) / "Temp")
    # Preserve order while removing duplicates.
    return list(dict.fromkeys(p.resolve() for p in roots if p.exists()))


def clean_temporaries(dry_run: bool = True) -> CleanupResult:
    result = CleanupResult()
    for root in safe_temp_roots():
        for item in root.iterdir():
            result.scanned += 1
            try:
                size = _size(item)
                if not dry_run:
                    if item.is_dir() and not item.is_symlink():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                result.removed += 1
                result.bytes_freed += size
            except (PermissionError, OSError):
                # Locked/current temp files are expected and are left untouched.
                result.failed += 1
    return result


def _size(path: Path) -> int:
    if path.is_file() or path.is_symlink():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    for root, _, files in os.walk(path, onerror=lambda _: None):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                pass
    return total
