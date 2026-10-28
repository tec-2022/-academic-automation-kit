"""Conservative cleanup of temporary files owned by Academic Automation Kit.

Never enumerate or delete arbitrary files from the user's or Windows' Temp
directories. General Windows cleanup belongs to Storage Sense, not this app.
"""
from __future__ import annotations

import tempfile
import time
import stat
from dataclasses import dataclass
from pathlib import Path


APP_TEMP_DIR = "AcademicAutomationKit"
MANAGED_SUFFIXES = frozenset({".tmp", ".cache"})
MIN_AGE_DAYS = 7


@dataclass
class CleanupResult:
    scanned: int = 0
    removed: int = 0
    failed: int = 0
    bytes_freed: int = 0


def app_temp_root() -> Path:
    """The only directory this app may clean, never the system Temp root."""
    return Path(tempfile.gettempdir()) / APP_TEMP_DIR


def _is_link_or_junction(path: Path) -> bool:
    # Windows junctions are not always reported by Path.is_symlink().
    if path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)()):
        return True
    try:
        flags = getattr(path.lstat(), "st_file_attributes", 0)
        return bool(flags & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    except OSError:
        # Fail closed when link metadata cannot be inspected.
        return True


def safe_temp_roots() -> list[Path]:
    root = app_temp_root()
    if not root.is_dir() or _is_link_or_junction(root):
        return []
    return [root]


def clean_temporaries(dry_run: bool = True, *, min_age_days: int = MIN_AGE_DAYS) -> CleanupResult:
    """Remove only stale, regular, top-level app-owned .tmp/.cache files.

    `removed` and `bytes_freed` describe eligible files during a dry run and
    successfully removed files during execution. Directories and links are
    deliberately never removed or followed.
    """
    if min_age_days < 1:
        raise ValueError("min_age_days must be at least one")

    result = CleanupResult()
    cutoff = time.time() - min_age_days * 86400
    for root in safe_temp_roots():
        try:
            entries = list(root.iterdir())
        except OSError:
            result.failed += 1
            continue

        for item in entries:
            result.scanned += 1
            try:
                if (_is_link_or_junction(item) or not item.is_file()
                        or item.suffix.lower() not in MANAGED_SUFFIXES):
                    continue
                stats = item.stat()
                if stats.st_mtime > cutoff:
                    continue
                if not dry_run:
                    item.unlink()
                result.removed += 1
                result.bytes_freed += stats.st_size
            except OSError:
                # Files in use or with changed permissions remain untouched.
                result.failed += 1
    return result
