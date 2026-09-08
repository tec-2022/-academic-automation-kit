#!/usr/bin/env python3
"""Convierte un CSV de entregas académicas en un calendario iCalendar (.ics)."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
import uuid

REQUIRED = {"title", "due"}


def escape_ics(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def parse_due(value: str) -> datetime:
    value = value.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            if fmt == "%Y-%m-%d":
                dt = dt.replace(hour=23, minute=59)
            return dt
        except ValueError:
            pass
    raise ValueError(f"Fecha inválida: {value}. Usa YYYY-MM-DD o YYYY-MM-DD HH:MM")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="CSV con columnas title,due y opcionales subject,description")
    parser.add_argument("--output", default="deadlines.ics")
    parser.add_argument("--reminder-hours", type=int, default=24)
    args = parser.parse_args()

    source = Path(args.input)
    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        if not REQUIRED.issubset(fields):
            parser.error("El CSV debe contener al menos las columnas: title,due")
        rows = list(reader)

    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Academic Automation Kit//Deadline Planner//ES",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for row in rows:
        due = parse_due(row["due"])
        title = row["title"].strip()
        subject = (row.get("subject") or "").strip()
        description = (row.get("description") or "").strip()
        summary = f"[{subject}] {title}" if subject else title
        uid = f"{uuid.uuid4()}@academic-automation-kit"
        local_stamp = due.strftime("%Y%m%dT%H%M%S")

        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now}",
                f"DTSTART:{local_stamp}",
                f"DTEND:{(due + timedelta(minutes=30)).strftime('%Y%m%dT%H%M%S')}",
                f"SUMMARY:{escape_ics(summary)}",
                f"DESCRIPTION:{escape_ics(description)}",
            ]
        )

        if args.reminder_hours >= 0:
            lines.extend(
                [
                    "BEGIN:VALARM",
                    f"TRIGGER:-PT{args.reminder_hours}H",
                    "ACTION:DISPLAY",
                    f"DESCRIPTION:{escape_ics('Recordatorio: ' + summary)}",
                    "END:VALARM",
                ]
            )

        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    Path(args.output).write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    print(f"Calendario generado: {args.output} ({len(rows)} eventos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
