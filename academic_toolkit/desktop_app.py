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
from .ui_theme import COLORS, FONT, configure_styles
from . import winget

APP_NAME = "Academic Automation Kit"
AUTHOR = "Fredy Luis Vidalón Lozano"


class DesktopApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} — {AUTHOR}")
        # Keep the window within the usable area on common student laptops.
        width = max(860, min(1180, self.winfo_screenwidth() - 60))
        height = max(560, min(780, self.winfo_screenheight() - 100))
        self.geometry(f"{width}x{height}")
        self.minsize(min(960, width), min(620, height))
        self.careers = list_careers()
        self.career_by_name = {c["name"]: c for c in self.careers}
        self._software_busy = False
        self._search_running = False
        self._install_in_progress = False
        self._cancel_install = threading.Event()
        self._app_icon = None
        self._sidebar_icon = None
        try:
            icon_path = Path(__file__).resolve().parents[1] / "assets" / "app-icon.png"
            self._app_icon = tk.PhotoImage(file=str(icon_path))
            self.iconphoto(True, self._app_icon)
            self._sidebar_icon = self._app_icon.subsample(5, 5)
        except (tk.TclError, OSError):
            # Non-critical: launchers remain functional without bundled imagery.
            pass
        self._build_style()
        self._build_ui()
        self.after(150, self._load_home_status)

    def _build_style(self) -> None:
        self.configure(bg=COLORS["background"])
        configure_styles(ttk.Style(self))

    def _build_ui(self) -> None:
        # One persistent navigation shell; switching pages never destroys
        # selections or interrupts an installation already in progress.
        shell = tk.Frame(self, bg=COLORS["background"])
        shell.pack(fill="both", expand=True)
        sidebar = tk.Frame(shell, bg=COLORS["sidebar"], width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        brand = tk.Frame(sidebar, bg=COLORS["sidebar"])
        brand.pack(fill="x", padx=24, pady=(28, 2))
        if self._sidebar_icon is not None:
            tk.Label(brand, image=self._sidebar_icon, bg=COLORS["sidebar"]).pack(side="left", padx=(0, 10))
        tk.Label(brand, text="AAK", fg=COLORS["white"], bg=COLORS["sidebar"],
                 font=(FONT, 24, "bold"), anchor="w").pack(side="left")
        tk.Label(sidebar, text="ADMINISTRACIÓN DE PC", fg="#A9BDD3", bg=COLORS["sidebar"],
                 font=(FONT, 9, "bold"), anchor="w").pack(fill="x", padx=24, pady=(0, 32))
        tk.Label(sidebar, text="HERRAMIENTAS", fg="#8EA8C3", bg=COLORS["sidebar"],
                 font=(FONT, 9, "bold"), anchor="w").pack(fill="x", padx=24, pady=(0, 12))
        self._nav = {}
        pages = (
            ("home", "Inicio", "Resumen y accesos rápidos"),
            ("career", "Preparar mi PC", "Compatibilidad y plan de software"),
            ("software", "Programas", "Catálogo de Winget"),
            ("clean", "Mantenimiento", "Limpieza segura de caché"),
            ("assistant", "Asistente", "Ayuda para tus tareas"),
        )
        self._page_metadata = {key: (title, subtitle) for key, title, subtitle in pages}
        for key, title, _subtitle in pages:
            btn = tk.Button(
                sidebar, text=title, command=lambda page=key: self._navigate(page),
                anchor="w", padx=20, pady=13, relief="flat", bd=0, cursor="hand2",
                bg=COLORS["sidebar"], fg="#DBE8F5", activebackground=COLORS["sidebar_hover"],
                activeforeground=COLORS["white"], font=(FONT, 11), takefocus=True,
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav[key] = btn
        tk.Label(sidebar, text="Atajos: Ctrl+1 a Ctrl+5\nIA local opcional",
                 wraplength=180, justify="left", fg="#A9BDD3", bg=COLORS["sidebar"],
                 font=(FONT, 9)).pack(side="bottom", anchor="w", padx=24, pady=25)

        main = tk.Frame(shell, bg=COLORS["background"])
        main.pack(side="left", fill="both", expand=True)
        header = tk.Frame(main, bg=COLORS["background"])
        header.pack(fill="x", padx=30, pady=(24, 14))
        self.page_title = tk.StringVar()
        self.page_subtitle = tk.StringVar()
        ttk.Label(header, textvariable=self.page_title, style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, textvariable=self.page_subtitle, style="Muted.TLabel").pack(anchor="w", pady=(5, 0))

        self.page_container = tk.Frame(main, bg=COLORS["background"])
        self.page_container.pack(fill="both", expand=True, padx=30, pady=(4, 10))
        self.home_tab = tk.Frame(self.page_container, bg=COLORS["background"])
        self.career_tab = tk.Frame(self.page_container, bg=COLORS["background"])
        self.software_tab = tk.Frame(self.page_container, bg=COLORS["background"])
        self.clean_tab = tk.Frame(self.page_container, bg=COLORS["background"])
        self.assistant_tab = tk.Frame(self.page_container, bg=COLORS["background"])
        self._pages = {
            "home": self.home_tab, "career": self.career_tab,
            "software": self.software_tab, "clean": self.clean_tab,
            "assistant": self.assistant_tab,
        }
        self._build_home()
        self._build_career()
        self._build_software()
        self._build_clean()
        self._build_assistant()

        self.status_mount = tk.Frame(main, bg=COLORS["background"])
        self.status_mount.pack(fill="x", padx=30, pady=(0, 6))
        footer = tk.Frame(main, bg=COLORS["background"])
        footer.pack(fill="x", padx=30, pady=(0, 17))
        ttk.Label(footer, text=f"© 2026 {AUTHOR}", style="Muted.TLabel").pack(side="left")
        self.global_status = tk.StringVar(value="Listo")
        ttk.Label(footer, textvariable=self.global_status, style="Muted.TLabel").pack(side="right")
        self._active_page = ""
        self._navigate("home")
        for index, key in enumerate(self._pages, start=1):
            self.bind_all(f"<Control-Key-{index}>", lambda _event, page=key: self._navigate(page))

    def _navigate(self, page: str) -> None:
        if page not in self._pages:
            raise ValueError(f"Pantalla desconocida: {page}")
        if self._active_page:
            self._pages[self._active_page].pack_forget()
        self._pages[page].pack(fill="both", expand=True)
        self._active_page = page
        title, subtitle = self._page_metadata[page]
        self.page_title.set(title)
        self.page_subtitle.set(subtitle)
        for key, button in self._nav.items():
            selected = key == page
            button.configure(
                bg=COLORS["sidebar_active"] if selected else COLORS["sidebar"],
                fg=COLORS["white"] if selected else "#DBE8F5",
                font=(FONT, 11, "bold" if selected else "normal"),
            )

    @staticmethod
    def _panel(parent: tk.Misc, *, padx: int = 20, pady: int = 18) -> tk.Frame:
        frame = tk.Frame(parent, bg=COLORS["surface"], highlightbackground=COLORS["border"],
                         highlightthickness=1, bd=0, padx=padx, pady=pady)
        return frame

    @staticmethod
    def _label(parent: tk.Misc, text: str, *, size: int = 10, bold: bool = False,
               muted: bool = False, wrap: int = 0) -> tk.Label:
        return tk.Label(
            parent, text=text, bg=COLORS["surface"],
            fg=COLORS["muted"] if muted else COLORS["text"],
            font=(FONT, size, "bold" if bold else "normal"),
            anchor="w", justify="left", wraplength=wrap,
        )

    def _build_home(self) -> None:
        hero = tk.Frame(self.home_tab, bg=COLORS["sidebar"], padx=24, pady=19)
        hero.pack(fill="x", pady=(0, 14))
        tk.Label(hero, text="Tu computadora, lista para trabajar",
                 bg=COLORS["sidebar"], fg=COLORS["white"],
                 font=(FONT, 17, "bold"), anchor="w").pack(fill="x")
        tk.Label(hero, text="Revisa la compatibilidad, instala herramientas y mantén el control de cada cambio.",
                 bg=COLORS["sidebar"], fg="#C4D8ED",
                 font=(FONT, 10), anchor="w", wraplength=660, justify="left").pack(fill="x", pady=(6, 0))

        grid = tk.Frame(self.home_tab, bg=COLORS["background"])
        grid.pack(fill="both", expand=True)
        actions = [
            ("Preparar mi PC", "Analiza tu equipo y crea un plan según tu carrera.", "Analizar equipo", "career"),
            ("Administrar programas", "Busca paquetes en Winget e instala lo que necesites.", "Ver programas", "software"),
            ("Mantenimiento seguro", "Revisa únicamente la caché de esta herramienta.", "Revisar caché", "clean"),
            ("Asistente de ayuda", "Explica lo que necesitas con tus propias palabras.", "Abrir asistente", "assistant"),
        ]
        for index, (title, desc, action, page) in enumerate(actions):
            card = self._panel(grid, padx=19, pady=14)
            card.grid(row=index // 2, column=index % 2, padx=(0, 7) if index % 2 == 0 else (7, 0),
                      pady=(0, 12), sticky="nsew")
            self._label(card, title, size=12, bold=True).pack(anchor="w")
            self._label(card, desc, muted=True, wrap=310).pack(anchor="w", fill="x", pady=(5, 10))
            ttk.Button(card, text=action, style="Secondary.TButton",
                       command=lambda target=page: self._navigate(target)).pack(anchor="w")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.rowconfigure(0, weight=1)
        grid.rowconfigure(1, weight=1)

        system = self._panel(self.home_tab, padx=20, pady=12)
        system.pack(fill="x", pady=(2, 0))
        self._label(system, "Estado del equipo", size=12, bold=True).pack(anchor="w", pady=(0, 5))
        self.home_status = tk.StringVar(value="Analizando...")
        tk.Label(system, textvariable=self.home_status, bg=COLORS["surface"], fg=COLORS["muted"],
                 font=(FONT, 10), anchor="w", justify="left").pack(fill="x")

    def _build_career(self) -> None:
        top = self._panel(self.career_tab)
        top.pack(fill="x", pady=(0, 12))
        self._label(top, "1. Configura tu perfil", size=13, bold=True).pack(anchor="w")
        self._label(top, "Selecciona la carrera y los niveles de herramientas que necesitas.",
                    muted=True).pack(anchor="w", pady=(4, 12))
        row = tk.Frame(top, bg=COLORS["surface"])
        row.pack(fill="x")
        self._label(row, "Carrera", bold=True).pack(side="left", padx=(0, 14))
        self.career_var = tk.StringVar(value=self.careers[0]["name"] if self.careers else "")
        self.career_combo = ttk.Combobox(row, textvariable=self.career_var, values=list(self.career_by_name),
                                         state="readonly", width=46)
        self.career_combo.pack(side="left", fill="x", expand=True)
        self.career_combo.bind("<<ComboboxSelected>>", lambda _e: self._career_selection_changed())
        self.career_desc = tk.StringVar()
        tk.Label(top, textvariable=self.career_desc, bg=COLORS["surface"], fg=COLORS["muted"],
                 font=(FONT, 10), anchor="w", justify="left", wraplength=675).pack(anchor="w", pady=(9, 8))
        self._career_description()

        tiers = ttk.Frame(top, style="Surface.TFrame")
        tiers.pack(fill="x", pady=(1, 0))
        self.tier_vars = {
            "essential": tk.BooleanVar(value=True),
            "recommended": tk.BooleanVar(value=True),
            "specialized": tk.BooleanVar(value=False),
        }
        self.tier_checks = []
        for label, key in [("Esencial", "essential"), ("Recomendado", "recommended"), ("Especializado", "specialized")]:
            check = ttk.Checkbutton(tiers, text=label, variable=self.tier_vars[key], command=self._invalidate_plan)
            check.pack(side="left", padx=(0, 18))
            self.tier_checks.append(check)
        self.analyze_btn = ttk.Button(tiers, text="Analizar mi PC", style="Primary.TButton",
                                       command=self._career_analyze)
        self.analyze_btn.pack(side="right")

        result = self._panel(self.career_tab, padx=14, pady=12)
        result.pack(fill="both", expand=True)
        self._label(result, "2. Revisa el plan de instalación", size=13, bold=True).pack(anchor="w", padx=4, pady=(2, 10))
        list_frame = ttk.Frame(result, style="Surface.TFrame")
        list_frame.pack(fill="both", expand=True)
        self.career_tree = ttk.Treeview(list_frame, columns=("tier", "state", "compat"), show="tree headings",
                                        selectmode="browse")
        self.career_tree.heading("#0", text="Programa")
        self.career_tree.heading("tier", text="Nivel")
        self.career_tree.heading("state", text="Estado")
        self.career_tree.heading("compat", text="Compatibilidad")
        self.career_tree.column("#0", width=235, minwidth=135, stretch=True)
        self.career_tree.column("tier", width=94, minwidth=80, stretch=False)
        self.career_tree.column("state", width=114, minwidth=90, stretch=False)
        self.career_tree.column("compat", width=240, minwidth=140, stretch=True)
        self.career_tree.tag_configure("installed", foreground=COLORS["success"])
        self.career_tree.tag_configure("unavailable", foreground=COLORS["muted"])
        career_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.career_tree.yview)
        career_horizontal = ttk.Scrollbar(list_frame, orient="horizontal", command=self.career_tree.xview)
        self.career_tree.configure(yscrollcommand=career_scroll.set, xscrollcommand=career_horizontal.set)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.career_tree.grid(row=0, column=0, sticky="nsew")
        career_scroll.grid(row=0, column=1, sticky="ns")
        career_horizontal.grid(row=1, column=0, sticky="ew")

        actions = tk.Frame(self.career_tab, bg=COLORS["background"])
        actions.pack(fill="x", pady=(12, 0))
        self.prepare_btn = ttk.Button(actions, text="Preparar equipo", style="Primary.TButton", command=self._career_prepare, state="disabled")
        self.prepare_btn.pack(side="right")
        self.cancel_prepare_btn = ttk.Button(actions, text="Detener después del actual",
                                              style="Secondary.TButton", command=self._request_cancel_install,
                                              state="disabled")
        self.cancel_prepare_btn.pack(side="right", padx=(0, 8))
        self.career_summary = tk.StringVar(value="Analiza el equipo para comenzar.")
        ttk.Label(actions, textvariable=self.career_summary, style="Muted.TLabel").pack(side="left")
        self.current_plan: dict | None = None
        self.plan_epoch = 0

    def _build_software(self) -> None:
        search_panel = self._panel(self.software_tab)
        search_panel.pack(fill="x", pady=(0, 12))
        self._label(search_panel, "Buscar en el catálogo de Windows", size=13, bold=True).pack(anchor="w")
        self._label(search_panel, "Escribe el nombre del programa. La búsqueda utiliza Winget.",
                    muted=True).pack(anchor="w", pady=(4, 12))
        row = ttk.Frame(search_panel, style="Surface.TFrame")
        row.pack(fill="x")
        self.search_var = tk.StringVar()
        entry = ttk.Entry(row, textvariable=self.search_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _e: self._search_software())
        self.search_btn = ttk.Button(row, text="Buscar programas", style="Primary.TButton",
                                      command=self._search_software)
        self.search_btn.pack(side="left", padx=(10, 0))

        results = self._panel(self.software_tab, padx=14, pady=12)
        results.pack(fill="both", expand=True)
        self._label(results, "Resultados", size=13, bold=True).pack(anchor="w", padx=4, pady=(2, 10))
        list_frame = ttk.Frame(results, style="Surface.TFrame")
        list_frame.pack(fill="both", expand=True)
        self.software_tree = ttk.Treeview(list_frame, columns=("name", "id", "version"), show="headings",
                                          selectmode="browse")
        self.software_tree.heading("name", text="Nombre")
        self.software_tree.heading("id", text="ID de paquete")
        self.software_tree.heading("version", text="Versión / fuente")
        self.software_tree.column("name", width=230, minwidth=130)
        self.software_tree.column("id", width=260, minwidth=140)
        self.software_tree.column("version", width=185, minwidth=115)
        software_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.software_tree.yview)
        software_horizontal = ttk.Scrollbar(list_frame, orient="horizontal", command=self.software_tree.xview)
        self.software_tree.configure(yscrollcommand=software_scroll.set,
                                     xscrollcommand=software_horizontal.set)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.software_tree.grid(row=0, column=0, sticky="nsew")
        software_scroll.grid(row=0, column=1, sticky="ns")
        software_horizontal.grid(row=1, column=0, sticky="ew")
        self.software_tree.bind("<<TreeviewSelect>>", lambda _e: self._update_software_actions())

        buttons = tk.Frame(self.software_tab, bg=COLORS["background"])
        buttons.pack(fill="x", pady=(12, 0))
        self.install_btn = ttk.Button(buttons, text="Instalar seleccionado", style="Primary.TButton",
                                       command=self._install_selected, state="disabled")
        self.install_btn.pack(side="right")
        self.uninstall_btn = ttk.Button(buttons, text="Desinstalar seleccionado", style="Secondary.TButton",
                                         command=self._uninstall_selected, state="disabled")
        self.uninstall_btn.pack(side="right", padx=(0, 8))
        self.software_info = tk.StringVar(value="Busca por nombre, por ejemplo: Python, Git, MySQL o RStudio.")
        ttk.Label(buttons, textvariable=self.software_info, style="Muted.TLabel").pack(side="left")

    def _build_clean(self) -> None:
        intro = self._panel(self.clean_tab)
        intro.pack(fill="x", pady=(0, 12))
        self._label(intro, "Limpieza limitada y bajo tu control", size=14, bold=True).pack(anchor="w")
        self._label(
            intro,
            "Esta función solo revisa archivos .tmp y .cache de Academic Automation Kit con más de siete días.",
            muted=True, wrap=690,
        ).pack(anchor="w", pady=(6, 10))
        self._label(intro, "No borra descargas, documentos ni temporales de otras aplicaciones.",
                    size=10, bold=True, wrap=690).pack(anchor="w")
        panel = self._panel(self.clean_tab)
        panel.pack(fill="x")
        self._label(panel, "Archivos temporales encontrados", size=13, bold=True).pack(anchor="w", pady=(0, 10))
        self.clean_result = tk.StringVar(value="Aún no se ha realizado el análisis.")
        tk.Label(panel, textvariable=self.clean_result, bg=COLORS["surface"], fg=COLORS["muted"],
                 font=(FONT, 11), anchor="w", justify="left").pack(fill="x", pady=(0, 16))
        row = ttk.Frame(panel, style="Surface.TFrame")
        row.pack(fill="x")
        ttk.Button(row, text="Analizar caché", style="Secondary.TButton",
                   command=self._clean_preview).pack(side="left")
        self.clean_btn = ttk.Button(row, text="Eliminar archivos revisados", style="Danger.TButton",
                                     command=self._clean_execute, state="disabled")
        self.clean_btn.pack(side="left", padx=(8, 0))
        hint = self._panel(self.clean_tab)
        hint.pack(fill="x", pady=(12, 0))
        self._label(hint, "¿Quieres liberar espacio de Windows?", size=12, bold=True).pack(anchor="w")
        self._label(hint, "Utiliza Configuración → Sistema → Almacenamiento. Esta aplicación no modifica esas carpetas.",
                    muted=True, wrap=690).pack(anchor="w", pady=(6, 0))

    def _build_assistant(self) -> None:
        prompt = self._panel(self.assistant_tab)
        prompt.pack(fill="x", pady=(0, 12))
        self._label(prompt, "¿En qué necesitas ayuda?", size=13, bold=True).pack(anchor="w")
        self._label(prompt, "Por ejemplo: «Quiero instalar Git» o «Necesito preparar mi PC para informática».",
                    muted=True, wrap=680).pack(anchor="w", pady=(5, 12))
        self.assistant_input = tk.Text(prompt, height=4, wrap="word", font=(FONT, 11),
                                       relief="flat", bd=0, padx=12, pady=10,
                                       bg=COLORS["background"], fg=COLORS["text"],
                                       insertbackground=COLORS["text"], highlightthickness=1,
                                       highlightbackground=COLORS["border"],
                                       highlightcolor=COLORS["accent"])
        self.assistant_input.pack(fill="x")
        buttons = ttk.Frame(prompt, style="Surface.TFrame")
        buttons.pack(fill="x", pady=(12, 0))
        ttk.Button(buttons, text="Interpretar", style="Primary.TButton", command=self._assistant_interpret).pack(side="left")
        self.ai_status = tk.StringVar(value=self._get_ai_status())
        ttk.Label(buttons, textvariable=self.ai_status, style="Muted.Surface.TLabel").pack(side="right")
        ttk.Button(buttons, text="Configurar IA local", style="Secondary.TButton",
                   command=self._install_ai).pack(side="right", padx=(0, 10))
        output_box = self._panel(self.assistant_tab)
        output_box.pack(fill="both", expand=True)
        self._label(output_box, "Resultado del análisis", size=13, bold=True).pack(anchor="w", pady=(0, 10))
        self.assistant_output = tk.Text(output_box, wrap="word", state="disabled",
                                        font=(FONT, 11), relief="flat", bd=0, padx=12, pady=10,
                                        bg=COLORS["background"], fg=COLORS["text"])
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
                message = f"No se pudo completar el diagnóstico: {exc}"
                self.after(0, lambda text=message: self.home_status.set(text))
        threading.Thread(target=job, daemon=True).start()

    def _career_description(self) -> None:
        item = self.career_by_name.get(self.career_var.get())
        self.career_desc.set(item["description"] if item else "")

    def _career_selection_changed(self) -> None:
        self._career_description()
        self._invalidate_plan()

    def _invalidate_plan(self) -> None:
        self.plan_epoch += 1
        self.current_plan = None
        self.prepare_btn.configure(state="disabled")
        self.career_summary.set("Selección modificada. Analiza de nuevo antes de instalar.")

    def _set_career_controls_busy(self, busy: bool) -> None:
        self.career_combo.configure(state="disabled" if busy else "readonly")
        self.analyze_btn.configure(state="disabled" if busy else "normal")
        for check in self.tier_checks:
            check.configure(state="disabled" if busy else "normal")
        self.cancel_prepare_btn.configure(state="normal" if busy else "disabled")

    def _request_cancel_install(self) -> None:
        if not self._install_in_progress:
            return
        self._cancel_install.set()
        self.cancel_prepare_btn.configure(state="disabled")
        self.career_summary.set("Se detendrá antes de iniciar el siguiente programa.")

    def _progress_begin(self, total: int) -> None:
        """Extension point for the enhanced progress strip."""

    def _progress_step(self, completed: int, total: int, package: str) -> None:
        """Extension point for the enhanced progress strip."""

    def _selected_tiers(self) -> list[str]:
        return [key for key, var in self.tier_vars.items() if var.get()]

    def _career_analyze(self) -> None:
        if self._install_in_progress:
            return
        item = self.career_by_name.get(self.career_var.get())
        tiers = self._selected_tiers()
        if not item or not tiers:
            messagebox.showwarning(APP_NAME, "Selecciona una carrera y al menos un nivel de software.")
            return
        self._busy("Analizando programas y compatibilidad...")
        self.prepare_btn.configure(state="disabled")
        self.current_plan = None
        self.career_tree.delete(*self.career_tree.get_children())
        self.plan_epoch += 1  # A newer analysis supersedes older background jobs.
        request_epoch = self.plan_epoch

        def job():
            try:
                plan = build_plan(item["id"], tiers, online_audit=True)
                self.after(0, lambda p=plan, epoch=request_epoch: self._show_plan(p)
                           if epoch == self.plan_epoch else None)
            except Exception as exc:
                self._schedule_error(exc)
            finally:
                self.after(0, lambda epoch=request_epoch: self._busy("Listo")
                           if epoch == self.plan_epoch else None)
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
            tag = ("installed",) if item["installed"] else (("unavailable",) if not item["available"] else ())
            self.career_tree.insert("", "end", text=item["name"],
                                    values=(item["tier"], state, compat), tags=tag)
        device = plan["device"]
        self.career_summary.set(
            f"{pending} pendiente(s) · RAM {device.get('ram_gb', '?')} GB · Libre {device.get('free_disk_gb', '?')} GB"
        )
        self.prepare_btn.configure(state="normal" if pending else "disabled")

    def _career_prepare(self) -> None:
        if self._install_in_progress or not self.current_plan:
            return
        selected = self.career_by_name.get(self.career_var.get())
        if (not selected or selected["id"] != self.current_plan["career"]["id"]
                or set(self._selected_tiers()) != set(self.current_plan["tiers"])):
            self._invalidate_plan()
            messagebox.showwarning(APP_NAME, "La selección cambió. Vuelve a analizar antes de instalar.")
            return
        plan_snapshot = self.current_plan
        installable = [i for i in plan_snapshot["items"] if i["compatible"] and i["available"] and not i["installed"]]
        if not installable:
            messagebox.showinfo(APP_NAME, "No hay programas pendientes que puedan instalarse.")
            return
        names = "\n".join(f"• {i['name']}" for i in installable)
        if not messagebox.askyesno(APP_NAME, f"Se instalarán {len(installable)} programas:\n\n{names}\n\n¿Continuar?"):
            self.career_summary.set(f"Plan listo: {len(installable)} programas pendientes.")
            return
        self._install_in_progress = True
        self._cancel_install.clear()
        self._set_career_controls_busy(True)
        self.prepare_btn.configure(state="disabled")
        self._progress_begin(len(installable))
        self._busy("Preparando equipo...")

        def job():
            errors: list[str] = []
            cancelled = False
            try:
                career = get_career(plan_snapshot["career"]["id"])
                package_meta = {p["id"]: p for p in career["packages"]}
                installed_meta = []
                for number, pkg in enumerate(installable, start=1):
                    if self._cancel_install.is_set():
                        cancelled = True
                        break
                    self.after(0, lambda n=pkg["name"], i=number, total=len(installable):
                               self._busy(f"Instalando {i}/{total}: {n}..."))
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
                    finally:
                        self.after(0, lambda i=number, total=len(installable), name=pkg["name"]:
                                   self._progress_step(i, total, name))
                for check in check_packages(installed_meta):
                    if not check["ok"]:
                        errors.append(f"{check['name']}: health check pendiente")
            except Exception as exc:
                errors.append(f"La preparación se interrumpió: {exc}")
            self.after(0, lambda was_cancelled=cancelled: self._finish_prepare(errors, was_cancelled))
        threading.Thread(target=job, daemon=True).start()

    def _finish_prepare(self, errors: list[str], cancelled: bool = False) -> None:
        self._install_in_progress = False
        self._set_career_controls_busy(False)
        self._busy("Listo")
        if cancelled:
            message = "Se detuvo la cola de instalación. No se interrumpió el programa que ya estaba en curso."
            if errors:
                message += "\n\nElementos que necesitan atención:\n" + "\n".join(errors)
            messagebox.showwarning(APP_NAME, message)
        elif errors:
            messagebox.showwarning(APP_NAME, "La preparación terminó con elementos que necesitan atención:\n\n" + "\n".join(errors))
        else:
            messagebox.showinfo(APP_NAME, "Preparación completada y verificada.")
        self._career_analyze()

    def _search_software(self) -> None:
        query = self.search_var.get().strip()
        if not query or self._software_busy or self._search_running:
            return
        self._search_running = True
        self.software_tree.delete(*self.software_tree.get_children())
        self._update_software_actions()
        self.search_btn.configure(state="disabled")
        self.software_info.set(f"Buscando «{query}»…")
        self._busy("Buscando en Winget...")

        def job():
            try:
                result, rows = winget.search(query)
                self.after(0, lambda: self._show_search(result.ok, rows, result.stderr))
            except Exception as exc:
                error = str(exc)
                self.after(0, lambda message=error: self._show_search(False, [], message))
        threading.Thread(target=job, daemon=True).start()

    def _show_search(self, ok: bool, rows: list[dict[str, str]], error: str) -> None:
        self._search_running = False
        self._busy("Listo")
        self.search_btn.configure(state="normal")
        if not ok:
            self.software_info.set((error.strip() or "No se pudo consultar Winget.")[:180])
            return
        for row in rows:
            values = list(row.values())
            package_id = row.get("Id") or row.get("ID") or (values[1] if len(values) > 1 else "")
            name = row.get("Name") or row.get("Nombre") or (values[0] if values else package_id)
            version = " · ".join(values[2:]) if len(values) > 2 else ""
            if package_id:
                self.software_tree.insert("", "end", values=(name, package_id, version))
        found = len(self.software_tree.get_children())
        self.software_info.set(f"{found} resultado(s)." if found else "Sin resultados. Prueba con otro nombre.")

    def _update_software_actions(self) -> None:
        selected = bool(self.software_tree.selection()) and not self._software_busy
        state = "normal" if selected else "disabled"
        self.install_btn.configure(state=state)
        self.uninstall_btn.configure(state=state)

    def _set_software_busy(self, busy: bool) -> None:
        self._software_busy = busy
        self.search_btn.configure(state="disabled" if busy or self._search_running else "normal")
        self._update_software_actions()

    def _selected_package_id(self) -> str | None:
        if self._software_busy:
            return None
        selection = self.software_tree.selection()
        if not selection:
            messagebox.showwarning(APP_NAME, "Selecciona un programa de la lista.")
            return None
        return str(self.software_tree.item(selection[0], "values")[1])

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
        if self._software_busy:
            return
        self._set_software_busy(True)
        self._busy(("Instalando " if action == "install" else "Desinstalando ") + package_id + "...")
        def job():
            try:
                result = install(package_id) if action == "install" else uninstall(package_id)
                ok = result.returncode == 0 or (action == "install" and is_installed(package_id))
                self.after(0, lambda: messagebox.showinfo(APP_NAME, "Operación completada." if ok else f"La operación devolvió código {result.returncode}."))
            except Exception as exc:
                self._schedule_error(exc)
            finally:
                self.after(0, self._finish_package_action)
        threading.Thread(target=job, daemon=True).start()

    def _finish_package_action(self) -> None:
        self._set_software_busy(False)
        self._busy("Listo")
        self.software_info.set("Operación finalizada. Vuelve a buscar para consultar el estado actualizado.")

    def _clean_preview(self) -> None:
        self.clean_btn.configure(state="disabled")
        self._busy("Analizando temporales...")
        def job():
            try:
                result = clean_temporaries(dry_run=True)
                mb = result.bytes_freed / (1024 ** 2)
                self.after(0, lambda: self._show_clean_preview(result.scanned, result.removed, result.failed, mb))
            except Exception as exc:
                self._schedule_error(exc)
            finally:
                self.after(0, lambda: self._busy("Listo"))
        threading.Thread(target=job, daemon=True).start()

    def _show_clean_preview(self, scanned: int, removable: int, failed: int, mb: float) -> None:
        self.clean_result.set(f"{scanned} elementos revisados · {removable} procesables · aproximadamente {mb:.1f} MB")
        self.clean_btn.configure(state="normal" if removable else "disabled")

    def _clean_execute(self) -> None:
        if not messagebox.askyesno(APP_NAME, "¿Eliminar solo archivos de caché antiguos de Academic Automation Kit? No se limpiarán temporales de otras aplicaciones."):
            self.clean_result.set("Limpieza cancelada. No se eliminaron archivos.")
            return
        self.clean_btn.configure(state="disabled")
        self._busy("Limpiando temporales...")
        def job():
            try:
                result = clean_temporaries(dry_run=False)
                mb = result.bytes_freed / (1024 ** 2)
                self.after(0, lambda: messagebox.showinfo(APP_NAME, f"Limpieza finalizada.\n{result.removed} elementos procesados.\n{mb:.1f} MB procesados/liberables."))
                self.after(0, lambda: self.clean_btn.configure(state="disabled"))
            except Exception as exc:
                self._schedule_error(exc)
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
                message = f"La IA local no respondió correctamente: {exc}"
                self.after(0, lambda text=message: self._assistant_write(text))
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
                self._schedule_error(exc)
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
                self._schedule_error(exc)
            finally:
                self.after(0, lambda: self._busy("Listo"))
        threading.Thread(target=job, daemon=True).start()

    def _busy(self, text: str) -> None:
        self.global_status.set(text)
        self.update_idletasks()

    def _error(self, text: str) -> None:
        messagebox.showerror(APP_NAME, text)

    def _schedule_error(self, exc: Exception) -> None:
        # Python clears exception variables when an `except` block exits.
        message = str(exc)
        self.after(0, lambda text=message: self._error(text))


def main() -> int:
    app = DesktopApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
