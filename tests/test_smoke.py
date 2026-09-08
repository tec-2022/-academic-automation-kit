from __future__ import annotations

import csv
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run_script(relative: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(ROOT / relative), *args]
    return subprocess.run(command, cwd=cwd or ROOT, text=True, capture_output=True)


class AcademicAutomationSmokeTests(unittest.TestCase):
    def test_deadline_planner_creates_ics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "deadlines.csv"
            source.write_text(
                "title,due,subject,description\nEntrega,2026-09-15 23:59,Finanzas,Reporte\n",
                encoding="utf-8",
            )
            output = base / "deadlines.ics"
            result = run_script(
                "scripts/students/deadline-planner.py",
                str(source),
                "--output",
                str(output),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            text = output.read_text(encoding="utf-8")
            self.assertIn("BEGIN:VCALENDAR", text)
            self.assertIn("[Finanzas] Entrega", text)

    def test_gradebook_calculator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "grades.csv"
            source.write_text("nombre,tareas,examen\nAna,100,80\n", encoding="utf-8")
            output = base / "result.csv"
            result = run_script(
                "scripts/teachers/gradebook-calculator.py",
                str(source),
                "--weights",
                "tareas=50,examen=50",
                "--output",
                str(output),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with output.open(newline="", encoding="utf-8-sig") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["nombre"], "Ana")
            self.assertEqual(float(row["calificacion_final"]), 90.0)

    def test_attendance_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "attendance.csv"
            source.write_text(
                "nombre,fecha,estado\nAna,2026-09-01,Presente\nAna,2026-09-02,Falta\n",
                encoding="utf-8",
            )
            output = base / "summary.csv"
            result = run_script(
                "scripts/teachers/attendance-summary.py",
                str(source),
                "--output",
                str(output),
                "--min-percent",
                "80",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with output.open(newline="", encoding="utf-8-sig") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["faltas"], "1")
            self.assertEqual(row["alerta"], "SI")

    def test_csv_cleaner_does_not_overwrite_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "raw.csv"
            source.write_text(" Nombre , Calificación ,\n Ana , 90 ,\n", encoding="utf-8")
            output = base / "clean.csv"
            result = run_script(
                "scripts/data/csv-cleaner.py",
                str(source),
                "--output",
                str(output),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.exists())
            self.assertIn(" Nombre ", source.read_text(encoding="utf-8"))

    def test_toolkit_lists_catalog(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "toolkit.py"), "list", "--audience", "students"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("deadline-planner", result.stdout)


if __name__ == "__main__":
    unittest.main()
