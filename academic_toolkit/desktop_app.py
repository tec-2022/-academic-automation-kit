"""Desktop interface for Academic Automation Kit.

Created by Fredy Luis Vidalón Lozano.
The GUI only exposes implemented operations from the deterministic toolkit engine.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from .ai import LocalAI
from .career_engine import build_plan, get_career, list_careers
from .health_checks import check_packages
from .predictor import predict, should_use_ai
from .software_manager import install, uninstall, verify_package, is_installed
from .system_prepare import clean_temporaries
from . import winget

APP_NAME = "Academic Automation Kit"
AUTHOR = "Fredy Luis Vidalón Lozano"


class DesktopApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} — {AUTHOR}")
        self.geometry("1120x740")
        self.minsize(960, 640)
        self.careers = list_careers()
        self.career_by_name = {c["name"]: c for c in self.careers}
        self._build_style()
        self._build_ui()
        self.after(150, self._load_home_status)

    def _build_style(self) -> None:
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("Sub.TLabel", font=("Segoe UI", 10))
        style.configure("Card.TLabelframe", padding=14)
        style.configure("Card.TLabelframe.Label", font=("Segoe UI", 11, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        style.configure("Treeview", rowheight=29)

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=(22, 18, 22, 8))
        header.pack(fill="x")
        ttk.Label(header, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Prepara, instala, diagnostica y mantiene tu PC sin necesitar conocimientos técnicos.",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(8, 12))
        self.home_tab = ttk.Frame(self.tabs, padding=18)
        self.career_tab = ttk.Frame(self.tabs, padding=18)
        self.software_tab = ttk.Frame(self.tabs, padding=18)
        self.clean_tab = ttk.Frame(self.tabs, padding=18)
        self.assistant_tab = ttk.Frame(self.tabs, padding=18)
        self.tabs.add(self.home_tab, text="Inicio")
        self.tabs.add(self.career_tab, text="Preparar mi PC")
        self.tabs.add(self.software_tab, text="Programas")
        self.tabs.add(self.clean_tab, text="Limpieza")
        self.tabs.add(self.assistant_tab, text="Asistente")
        self._build_home()
        self._build_career()
        self._build_software()
        self._build_clean()
        self._build_assistant()

        footer = ttk.Frame(self, padding=(20, 0, 20, 12))
        footer.pack(fill="x")
        ttk.Label(footer, text=f"Creado por {AUTHOR}").pack(side="left")
        self.global_status = tk.StringVar(value="Listo")
        ttk.Label(footer, textvariable=self.global_status).pack(side="right")

    def _build_home(self) -> None:
        ttk.Label(self.home_tab, text="¿Qué necesitas hacer?", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            self.home_tab,
            text="Elige una acción. Antes de modificar el sistema, la aplicación analiza el estado actual.",
        ).pack(anchor="w", pady=(4, 16))

        grid = ttk.Frame(self.home_tab)
        grid.pack(fill="x")
        actions = [
            ("Preparar mi PC para estudiar", "Selecciona tu carrera y revisa qué software necesitas.", 1),
            ("Instalar o quitar un programa", "Busca software disponible mediante Winget.", 2),
            ("Limpiar archivos temporales", "Revisa primero cuánto puede limpiarse de forma segura.", 3),
            ("Algo no funciona", "Describe el problema en lenguaje normal.", 4),
        ]
        for index, (title, desc, tab_index) in enumerate(actions):
            card = ttk.LabelFrame(grid, text=title, style="Card.TLabelframe")
            card.grid(row=index // 2, column=index % 2, padx=7, pady=7, sticky="nsew")
            ttk.Label(card, text=desc, wraplength=390).pack(anchor="w", pady=(0, 10))
            ttk.Button(card, text="Abrir", command=lambda i=tab_index: self.tabs.select(i)).pack(anchor="e")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        system = ttk.LabelFrame(self.home_tab, text="Estado del equipo", style="Card.TLabelframe")
        system.pack(fill="x", pady=(18, 0))
        self.home_status = tk.StringVar(value="Analizando...")
        ttk.Label(system, textvariable=self.home_status, justify="left").pack(anchor="w")

    def _build_career(self) -> None:
        top = ttk.Frame(self.career_tab)
        top.pack(fill="x")
        ttk.Label(top, text="Preparar PC por carrera", font=("Segoe UI", 18, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(top, text="Carrera:").grid(row=1, column=0, sticky="w", pady=(14, 4))
        self.career_var = tk.StringVar(value=self.careers[0]["name"] if self.careers else "")
        combo = ttk.Combobox(top, textvariable=self.career_var, values=list(self.career_by_name), state="readonly", width=48)
        combo.grid(row=2, column=0, sticky="w")
        combo.bind("<<ComboboxSelected>>", lambda _e: self._career_description())
        self.career_desc = tk.StringVar()
        ttk.Label(top, textvariable=self.career_desc, wraplength=760).grid(row=3, column=0, sticky="w", pady=(6, 10))
        self._career_description()

        tiers = ttk.Frame(top)
        tiers.grid(row=4, column=0, sticky="w", pady=(4, 12))
        self.tier_vars = {
            "essential": tk.BooleanVar(value=True),
            "recommended": tk.BooleanVar(value=True),
            "specialized": tk.BooleanVar(value=False),
        }
        for label, key in [("Esencial", "essential"), ("Recomendado", "recommended"), ("Especializado", "specialized")]:
            ttk.Checkbutton(tiers, text=label, variable=self.tier_vars[key]).pack(side="left", padx=(0, 18))
        ttk.Button(top, text="Analizar mi computadora", style="Primary.TButton", command=self._career_analyze).grid(row=5, column=0, sticky="w")

        self.career_tree = ttk.Treeview(self.career_tab, columns=("tier", "state", "compat"), show="tree headings")
        self.career_tree.heading("#0", text="Programa")
        self.career_tree.heading("tier", text="Nivel")
        self.career_tree.heading("state", text="Estado")
        self.career_tree.heading("compat", text="Compatibilidad")
        self.career_tree.column("#0", width=330)
        self.career_tree.column("tier", width=120)
        self.career_tree.column("state", width=160)
        self.career_tree.column("compat", width=280)
        self.career_tree.pack(fill="both", expand=True, pady=(16, 10))

        actions = ttk.Frame(self.career_tab)
        actions.pack(fill="x")
        self.prepare_btn = ttk.Button(actions, text="Preparar equipo", style="Primary.TButton", command=self._career_prepare, state="disabled")
        self.prepare_btn.pack(side="right")
        self.career_summary = tk.StringVar(value="Analiza el equipo para comenzar.")
        ttk.Label(actions, textvariable=self.career_summary).pack(side="left")
        self.current_plan: dict | None = None

    def _build_software(self) -> None:
        ttk.Label(self.software_tab, text="Instalar o quitar programas", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        row = ttk.Frame(self.software_tab)
        row.pack(fill="x", pady=(14, 10))
        self.search_var = tk.StringVar()
        entry = ttk.Entry(row, textvariable=self.search_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _e: self._search_software())
        ttk.Button(row, text="Buscar", command=self._search_software).pack(side="left", padx=(8, 0))

        self.software_tree = ttk.Treeview(self.software_tab, columns=("id", "version"), show="headings")
        self.software_tree.heading("id", text="ID de paquete")
        self.software_tree.heading("version", text="Versión / fuente")
        self.software_tree.column("id", width=480)
        self.software_tree.column("version", width=300)
        self.software_tree.pack(fill="both", expand=True)

        buttons = ttk.Frame(self.software_tab)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Instalar seleccionado", style="Primary.TButton", command=self._install_selected).pack(side="right")
        ttk.Button(buttons, text="Desinstalar seleccionado", command=self._uninstall_selected).pack(side="right", padx=(0, 8))
        self.software_info = tk.StringVar(value="Busca por nombre, por ejemplo: Python, Git, MySQL o RStudio.")
        ttk.Label(buttons, textvariable=self.software_info).pack(side="left")

    def _build_clean(self) -> None:
        ttk.Label(self.clean_tab, text="Limpieza segura", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            self.clean_tab,
            text="Solo revisa ubicaciones temporales. No toca Documentos, Descargas, Escritorio ni perfiles del navegador.",
            wraplength=820,
        ).pack(anchor="w", pady=(5, 18))
        panel = ttk.LabelFrame(self.clean_tab, text="Archivos temporales", style="Card.TLabelframe")
        panel.pack(fill="x")
        self.clean_result = tk.StringVar(value="Aún no se ha realizado el análisis.")
        ttk.Label(panel, textvariable=self.clean_result, font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 12))
        row = ttk.Frame(panel)
        row.pack(fill="x")
        ttk.Button(row, text="Analizar", command=self._clean_preview).pack(side="left")
        self.clean_btn = ttk.Button(row, text="Limpiar ahora", style="Primary.TButton", command=self._clean_execute, state="disabled")
        self.clean_btn.pack(side="left", padx=(8, 0))

    def _build_assistant(self) -> None:
        ttk.Label(self.assistant_tab, text="Asistente", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            self.assistant_tab,
            text="Describe lo que necesitas. Primero se usa predicción local instantánea; la IA es opcional.",
        ).pack(anchor="w", pady=(5, 14))
        self.assistant_input = tk.Text(self.assistant_tab, height=5, wrap="word", font=("Segoe UI", 11))
        self.assistant_input.pack(fill="x")
        buttons = ttk.Frame(self.assistant_tab)
        buttons.pack(fill="x", pady=(8, 12))
        ttk.Button(buttons, text="Interpretar", style="Primary.TButton", command=self._assistant_interpret).pack(side="left")
        self.ai_status = tk.StringVar(value=self._get_ai_status())
        ttk.Label(buttons, textvariable=self.ai_status).pack(side="right")
        ttk.Button(buttons, text="Instalar IA local", command=self._install_ai).pack(side="right", padx=(0, 10))
        output_box = ttk.LabelFrame(self.assistant_tab, text="Resultado", style="Card.TLabelframe")
        output_box.pack(fill="both", expand=True)
        self.assistant_output = tk.Text(output_box, wrap="word", state="disabled", font=("Consolas", 10))
        self.assistant_output.pack(fill="both", expand=True)

    def _load_home_status(self) -> None:
        def job():
            try:
                plan = build_plan(self.careers[0]["id"], ["essential"], online_audit=False) if self.careers else None
                device = plan["device"] if plan else {}
                text = (
                    f"Sistema: {device.get('os_name', 'desconocido')} {device.get('architecture', '')}\n"
                    f"RAM: {device.get('ram_gb', 'desconocida')} GB   |   Espacio libre: {device.get('free_disk_gb', '?')} GB\n"
                    f"Winget: {'Disponible' if device.get('winget') else 'No disponible'}   |   IA local: {self._get_ai_status()}"
                )
                self.after(0, lambda: self.home_status.set(text))
            except Exception as exc:
                self.after(0, lambda: self.home_status.set(f"No se pudo completar el diagnóstico: {exc}"))
        threading.Thread(target=job, daemon=True).start()

    def _career_description(self) -> None:
        item = self.career_by_name.get(self.career_var.get())
        self.career_desc.set(item["description"] if item else "")

    def _selected_tiers(self) -> list[str]:
        return [key for key, var in self.tier_vars.items() if var.get()]

    def _career_analyze(self) -> None:
        item = self.career_by_name.get(self.career_var.get())
        tiers = self._selected_tiers()
        if not item or not tiers:
            messagebox.showwarning(APP_NAME, "Selecciona una carrera y al menos un nivel de software.")
            return
        self._busy("Analizando programas y compatibilidad...")
        self.prepare_btn.configure(state="disabled")
        self.career_tree.delete(*self.career_tree.get_children())

        def job():
            try:
                plan = build_plan(item["id"], tiers, online_audit=True)
                self.after(0, lambda: self._show_plan(plan))
            except Exception as exc:
                self.after(0, lambda: self._error(str(exc)))
            finally:
                self.after(0, lambda: self._busy("Listo"))
        threading.Thread(target=job, daemon=True).start()

    def _show_plan(self, plan: dict) -> None:
        self.current_plan = plan
        self.career_tree.delete(*self.career_tree.get_children())
        pending = 0
        for item in plan["items"]:
            if item["installed"]:
                state = "Instalado"
            elif item["available"]:
                state = "Disponible"
                if item["compatible"]:
                    pending += 1
            else:
                state = "No disponible"
            compat = "Compatible" if item["compatible"] else item["reason"]
            self.career_tree.insert("", "end", text=item["name"], values=(item["tier"], state, compat))
        device = plan["device"]
        self.career_summary.set(
            f"{pending} pendiente(s) · RAM {device.get('ram_gb', '?')} GB · Libre {device.get('free_disk_gb', '?')} GB"
        )
        self.prepare_btn.configure(state="normal" if pending else "disabled")

    def _career_prepare(self) -> None:
        if not self.current_plan:
            return
        installable = [i for i in self.current_plan["items"] if i["compatible"] and i["available"] and not i["installed"]]
        if not installable:
            messagebox.showinfo(APP_NAME, "No hay programas pendientes que puedan instalarse.")
            return
        names = "\n".join(f"• {i['name']}" for i in installable)
        if not messagebox.askyesno(APP_NAME, f"Se instalarán {len(installable)} programas:\n\n{names}\n\n¿Continuar?"):
            return
        self.prepare_btn.configure(state="disabled")
        self._busy("Preparando equipo...")

        def job():
            errors: list[str] = []
            clean_temporaries(dry_run=False)
            career = get_career(self.current_plan["career"]["id"])
            package_meta = {p["id"]: p for p in career["packages"]}
            installed_meta = []
            for pkg in installable:
                self.after(0, lambda n=pkg["name"]: self._busy(f"Instalando {n}..."))
                try:
                    if not verify_package(pkg["package_id"]):
                        errors.append(f"{pkg['name']}: dejó de estar disponible en Winget")
                        continue
                    result = install(pkg["package_id"])
                    if result.returncode != 0 and not is_installed(pkg["package_id"]):
                        errors.append(f"{pkg['name']}: error {result.returncode}")
                        continue
                    installed_meta.append(package_meta[pkg["package_id"]])
                except Exception as exc:
                    errors.append(f"{pkg['name']}: {exc}")
            for check in check_packages(installed_meta):
                if not check["ok"]:
                    errors.append(f"{check['name']}: health check pendiente")
            self.after(0, lambda: self._finish_prepare(errors))
        threading.Thread(target=job, daemon=True).start()

    def _finish_prepare(self, errors: list[str]) -> None:
        self._busy("Listo")
        if errors:
            messagebox.showwarning(APP_NAME, "La preparación terminó con elementos que necesitan atención:\n\n" + "\n".join(errors))
        else:
            messagebox.showinfo(APP_NAME, "Preparación completada y verificada.")
        self._career_analyze()

    def _search_software(self) -> None:
        query = self.search_var.get().strip()
        if not query:
            return
        self.software_tree.delete(*self.software_tree.get_children())
        self._busy("Buscando en Winget...")

        def job():
            result, rows = winget.search(query)
            self.after(0, lambda: self._show_search(result.ok, rows, result.stderr))
        threading.Thread(target=job, daemon=True).start()

    def _show_search(self, ok: bool, rows: list[dict[str, str]], error: str) -> None:
        self._busy("Listo")
        if not ok:
            self.software_info.set(error.strip() or "No se pudo consultar Winget.")
            return
        for row in rows:
            values = list(row.values())
            package_id = row.get("Id") or row.get("ID") or (values[1] if len(values) > 1 else "")
            version = " · ".join(values[2:]) if len(values) > 2 else ""
            if package_id:
                self.software_tree.insert("", "end", values=(package_id, version))
        self.software_info.set(f"{len(rows)} resultado(s). Selecciona un paquete para instalar o quitar.")

    def _selected_package_id(self) -> str | None:
        selection = self.software_tree.selection()
        if not selection:
            messagebox.showwarning(APP_NAME, "Selecciona un programa de la lista.")
            return None
        return str(self.software_tree.item(selection[0], "values")[0])

    def _install_selected(self) -> None:
        package_id = self._selected_package_id()
        if not package_id:
            return
        if not messagebox.askyesno(APP_NAME, f"¿Instalar {package_id}?"):
            return
        self._package_action(package_id, "install")

    def _uninstall_selected(self) -> None:
        package_id = self._selected_package_id()
        if not package_id:
            return
        if not messagebox.askyesno(APP_NAME, f"¿Desinstalar {package_id}?\n\nEsta acción puede eliminar la aplicación y su configuración administrada por el instalador."):
            return
        self._package_action(package_id, "uninstall")

    def _package_action(self, package_id: str, action: str) -> None:
        self._busy(("Instalando " if action == "install" else "Desinstalando ") + package_id + "...")
        def job():
            try:
                result = install(package_id) if action == "install" else uninstall(package_id)
                ok = result.returncode == 0 or (action == "install" and is_installed(package_id))
                self.after(0, lambda: messagebox.showinfo(APP_NAME, "Operación completada." if ok else f"La operación devolvió código {result.returncode}."))
            except Exception as exc:
                self.after(0, lambda: self._error(str(exc)))
            finally:
                self.after(0, lambda: self._busy("Listo"))
        threading.Thread(target=job, daemon=True).start()

    def _clean_preview(self) -> None:
        self._busy("Analizando temporales...")
        def job():
            try:
                result = clean_temporaries(dry_run=True)
                mb = result.bytes_freed / (1024 ** 2)
                self.after(0, lambda: self._show_clean_preview(result.scanned, result.removed, result.failed, mb))
            except Exception as exc:
                self.after(0, lambda: self._error(str(exc)))
            finally:
                self.after(0, lambda: self._busy("Listo"))
        threading.Thread(target=job, daemon=True).start()

    def _show_clean_preview(self, scanned: int, removable: int, failed: int, mb: float) -> None:
        self.clean_result.set(f"{scanned} elementos revisados · {removable} procesables · aproximadamente {mb:.1f} MB")
        self.clean_btn.configure(state="normal" if removable else "disabled")

    def _clean_execute(self) -> None:
        if not messagebox.askyesno(APP_NAME, "¿Eliminar los archivos temporales detectados? Los archivos bloqueados se dejarán intactos."):
            return
        self._busy("Limpiando temporales...")
        def job():
            try:
                result = clean_temporaries(dry_run=False)
                mb = result.bytes_freed / (1024 ** 2)
                self.after(0, lambda: messagebox.showinfo(APP_NAME, f"Limpieza finalizada.\n{result.removed} elementos procesados.\n{mb:.1f} MB procesados/liberables."))
                self.after(0, lambda: self.clean_btn.configure(state="disabled"))
            except Exception as exc:
                self.after(0, lambda: self._error(str(exc)))
            finally:
                self.after(0, lambda: self._busy("Listo"))
        threading.Thread(target=job, daemon=True).start()

    def _assistant_interpret(self) -> None:
        text = self.assistant_input.get("1.0", "end").strip()
        if not text:
            return
        intent, confidence = predict(text)
        if intent != "unknown":
            self._assistant_write(self._intent_explanation(intent, confidence, "predicción local"))
            return
        if not should_use_ai(text) or not shutil.which("ollama"):
            self._assistant_write("No pude clasificar la solicitud con las reglas locales. Puedes instalar la IA local opcional o usar las secciones de la aplicación.")
            return
        self._busy("Interpretando con IA local...")
        def job():
            try:
                result = LocalAI().classify(text)
                output = self._intent_explanation(result.get("intent", "unknown"), float(result.get("confidence", 0)), "IA local")
                target = result.get("target")
                if target:
                    output += f"\nObjetivo detectado: {target}"
                self.after(0, lambda: self._assistant_write(output))
            except Exception as exc:
                self.after(0, lambda: self._assistant_write(f"La IA local no respondió correctamente: {exc}"))
            finally:
                self.after(0, lambda: self._busy("Listo"))
        threading.Thread(target=job, daemon=True).start()

    def _intent_explanation(self, intent: str, confidence: float, source: str) -> str:
        names = {
            "install_program": "Instalar un programa",
            "uninstall_program": "Desinstalar un programa",
            "prepare_career": "Preparar el equipo para una carrera",
            "clean_temporaries": "Limpiar archivos temporales",
            "diagnose_mysql": "Diagnosticar MySQL/MariaDB",
            "repair_mysql": "Reparar MySQL",
            "list_installed": "Revisar programas instalados",
            "unknown": "Solicitud no clasificada",
        }
        return f"Intención: {names.get(intent, intent)}\nConfianza: {confidence:.0%}\nMotor: {source}\n\nLa aplicación no ejecutará cambios críticos solo por esta predicción; primero mostrará el plan correspondiente."

    def _assistant_write(self, text: str) -> None:
        self.assistant_output.configure(state="normal")
        self.assistant_output.delete("1.0", "end")
        self.assistant_output.insert("1.0", text)
        self.assistant_output.configure(state="disabled")

    def _get_ai_status(self) -> str:
        if shutil.which("ollama"):
            return "IA local: Ollama instalado"
        return "IA local: no instalada (opcional)"

    def _install_ai(self) -> None:
        if shutil.which("ollama"):
            if messagebox.askyesno(APP_NAME, "Ollama ya está instalado. ¿Descargar/actualizar el modelo ligero qwen3:0.6b?"):
                self._pull_ai_model()
            return
        if not messagebox.askyesno(APP_NAME, "La IA es opcional. Se instalará Ollama y después un modelo local ligero. ¿Continuar?"):
            return
        self._busy("Validando Ollama en Winget...")
        def job():
            try:
                if not verify_package("Ollama.Ollama"):
                    raise RuntimeError("Ollama.Ollama no está disponible mediante Winget en este momento.")
                result = install("Ollama.Ollama")
                if result.returncode != 0 and not is_installed("Ollama.Ollama"):
                    raise RuntimeError(f"Winget devolvió código {result.returncode} al instalar Ollama.")
                self.after(0, self._pull_ai_model)
            except Exception as exc:
                self.after(0, lambda: self._error(str(exc)))
                self.after(0, lambda: self._busy("Listo"))
        threading.Thread(target=job, daemon=True).start()

    def _pull_ai_model(self) -> None:
        self._busy("Descargando modelo IA ligero...")
        def job():
            try:
                exe = shutil.which("ollama") or shutil.which("ollama.exe")
                if not exe:
                    raise RuntimeError("Ollama se instaló, pero Windows aún no actualizó PATH. Reinicia la app e intenta de nuevo.")
                result = subprocess.run([exe, "pull", "qwen3:0.6b"], text=True, capture_output=True, timeout=1800)
                if result.returncode != 0:
                    raise RuntimeError(result.stderr.strip() or "No se pudo descargar el modelo.")
                self.after(0, lambda: self.ai_status.set(self._get_ai_status()))
                self.after(0, lambda: messagebox.showinfo(APP_NAME, "IA local instalada. Seguirá siendo opcional y solo se usará cuando las reglas locales no basten."))
            except Exception as exc:
                self.after(0, lambda: self._error(str(exc)))
            finally:
                self.after(0, lambda: self._busy("Listo"))
        threading.Thread(target=job, daemon=True).start()

    def _busy(self, text: str) -> None:
        self.global_status.set(text)
        self.update_idletasks()

    def _error(self, text: str) -> None:
        messagebox.showerror(APP_NAME, text)


def main() -> int:
    app = DesktopApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
