"""Enhanced desktop shell with visible progress for every long-running action.

Created by Fredy Luis Vidalón Lozano.
This module extends the functional GUI without duplicating the deterministic engine.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .desktop_app import APP_NAME, DesktopApp


class EnhancedDesktopApp(DesktopApp):
    """DesktopApp with a persistent operation/status strip and local feedback."""

    def _build_ui(self) -> None:
        super()._build_ui()

        self.operation_status = tk.StringVar(value="Listo para trabajar")
        self.operation_detail = tk.StringVar(value="No hay operaciones en curso.")

        panel = ttk.LabelFrame(self, text="Estado de la operación", padding=(12, 8))
        panel.pack(fill="x", padx=20, pady=(0, 10))

        header = ttk.Frame(panel)
        header.pack(fill="x")
        ttk.Label(header, textvariable=self.operation_status, font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Label(header, textvariable=self.operation_detail).pack(side="right")

        self.operation_progress = ttk.Progressbar(panel, mode="indeterminate", length=700)
        self.operation_progress.pack(fill="x", pady=(7, 0))

        # Keep the existing footer status synchronized with the more visible strip.
        self._operation_running = False

    def _busy(self, text: str) -> None:
        """Show long-running work in a persistent, visible progress strip."""
        self.global_status.set(text)
        if not hasattr(self, "operation_progress"):
            self.update_idletasks()
            return

        normalized = text.strip().casefold()
        idle = normalized in {"listo", "listo.", "ready"}
        if idle:
            self.operation_status.set("Listo")
            self.operation_detail.set("Operación finalizada.")
            if self._operation_running:
                self.operation_progress.stop()
                self._operation_running = False
            self.configure(cursor="")
        else:
            self.operation_status.set(text.rstrip("."))
            self.operation_detail.set("Puedes seguir viendo el estado aquí mientras termina.")
            if not self._operation_running:
                self.operation_progress.start(12)
                self._operation_running = True
            self.configure(cursor="watch")
        self.update_idletasks()

    def _career_analyze(self) -> None:
        if hasattr(self, "career_summary"):
            self.career_summary.set("Analizando equipo, programas instalados y compatibilidad…")
        super()._career_analyze()

    def _show_plan(self, plan: dict) -> None:
        super()._show_plan(plan)
        total = len(plan.get("items", []))
        installed = sum(1 for item in plan.get("items", []) if item.get("installed"))
        unavailable = sum(1 for item in plan.get("items", []) if not item.get("available") and not item.get("installed"))
        self.operation_detail.set(
            f"Análisis completo: {total} revisados · {installed} instalados · {unavailable} no disponibles"
        )

    def _career_prepare(self) -> None:
        if hasattr(self, "career_summary"):
            self.career_summary.set("Preparación pendiente de confirmación…")
        super()._career_prepare()

    def _search_software(self) -> None:
        query = self.search_var.get().strip() if hasattr(self, "search_var") else ""
        if query and hasattr(self, "software_info"):
            self.software_info.set(f"Buscando “{query}” en Winget…")
        super()._search_software()

    def _package_action(self, package_id: str, action: str) -> None:
        if hasattr(self, "software_info"):
            verb = "Instalando" if action == "install" else "Desinstalando"
            self.software_info.set(f"{verb} {package_id}… No cierres la aplicación.")
        super()._package_action(package_id, action)

    def _clean_preview(self) -> None:
        if hasattr(self, "clean_result"):
            self.clean_result.set("Analizando ubicaciones temporales seguras…")
        super()._clean_preview()

    def _clean_execute(self) -> None:
        if hasattr(self, "clean_result"):
            self.clean_result.set("Esperando confirmación para iniciar la limpieza…")
        super()._clean_execute()

    def _assistant_interpret(self) -> None:
        text = self.assistant_input.get("1.0", "end").strip() if hasattr(self, "assistant_input") else ""
        if text:
            self._assistant_write("Interpretando tu solicitud…")
        super()._assistant_interpret()

    def _install_ai(self) -> None:
        if hasattr(self, "ai_status"):
            self.ai_status.set("IA local: comprobando instalación…")
        super()._install_ai()


def main() -> int:
    app = EnhancedDesktopApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
