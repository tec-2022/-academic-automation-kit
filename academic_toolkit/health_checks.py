"""Post-install health checks for career packages.

A successful installer exit code is not treated as proof that a tool works.
Created by Fredy Luis Vidalón Lozano.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, asdict

@dataclass
class HealthResult:
    name: str
    ok: bool
    command: list[str]
    output: str
    error: str


def run_check(name: str, command: list[str], timeout: int = 20) -> HealthResult:
    if not command:
        return HealthResult(name, False, [], "", "health check not defined")
    executable = shutil.which(command[0])
    if not executable:
        return HealthResult(name, False, command, "", f"executable not found: {command[0]}")
    try:
        result = subprocess.run([executable, *command[1:]], capture_output=True, text=True,
                                timeout=timeout, encoding="utf-8", errors="replace")
        return HealthResult(name, result.returncode == 0, command,
                            result.stdout.strip(), result.stderr.strip())
    except (OSError, subprocess.TimeoutExpired) as exc:
        return HealthResult(name, False, command, "", str(exc))


def check_packages(packages: list[dict]) -> list[dict]:
    results = []
    for package in packages:
        command = package.get("health_check")
        if command:
            results.append(asdict(run_check(package["name"], command)))
    return results
