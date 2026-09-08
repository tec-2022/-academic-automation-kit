from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    ok: bool
    returncode: int
    stdout: str
    stderr: str


def available() -> bool:
    return shutil.which('winget') is not None or shutil.which('winget.exe') is not None


def _run(args: list[str], timeout: int = 900) -> CommandResult:
    exe = shutil.which('winget') or shutil.which('winget.exe')
    if not exe:
        return CommandResult(False, 127, '', 'winget no está disponible')
    completed = subprocess.run([exe, *args], text=True, capture_output=True, timeout=timeout)
    return CommandResult(completed.returncode == 0, completed.returncode, completed.stdout, completed.stderr)


def package_exists(package_id: str) -> bool:
    result = _run(['show', '--id', package_id, '-e', '--accept-source-agreements'], timeout=90)
    return result.ok


def is_installed(package_id: str) -> bool:
    result = _run(['list', '--id', package_id, '-e', '--accept-source-agreements'], timeout=90)
    if not result.ok:
        return False
    text = (result.stdout + '\n' + result.stderr).lower()
    return package_id.lower() in text


def install(package_id: str, *, silent: bool = True) -> CommandResult:
    args = ['install', '--id', package_id, '-e', '--accept-package-agreements', '--accept-source-agreements']
    if silent:
        args.append('--silent')
    return _run(args)


def uninstall(package_id: str, *, silent: bool = True) -> CommandResult:
    args = ['uninstall', '--id', package_id, '-e', '--accept-source-agreements']
    if silent:
        args.append('--silent')
    return _run(args)


def _parse_table(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    separator = next((i for i, line in enumerate(lines) if re.fullmatch(r'[-\s]+', line)), None)
    if separator is None or separator == 0:
        return rows
    headers = re.split(r'\s{2,}', lines[separator - 1].strip())
    for line in lines[separator + 1:]:
        columns = re.split(r'\s{2,}', line.strip(), maxsplit=max(0, len(headers) - 1))
        if len(columns) < 2:
            continue
        rows.append({headers[i]: columns[i] if i < len(columns) else '' for i in range(len(headers))})
    return rows


def search(query: str) -> tuple[CommandResult, list[dict[str, str]]]:
    result = _run(['search', '--query', query, '--accept-source-agreements'], timeout=90)
    return result, _parse_table(result.stdout) if result.ok else []
