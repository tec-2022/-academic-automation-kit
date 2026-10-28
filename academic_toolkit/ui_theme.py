"""Dependency-free desktop design tokens and Tk/ttk styling.

The interface uses Fluent-inspired structure without representing itself as
Microsoft software or requiring an additional graphical dependency.
"""

from __future__ import annotations

from tkinter import ttk


COLORS = {
    "background": "#F3F6FA",
    "surface": "#FFFFFF",
    "surface_alt": "#EAF0F7",
    "border": "#D9E3ED",
    "text": "#152538",
    "muted": "#53657A",
    "subtle": "#6B7C90",
    "sidebar": "#13243A",
    "sidebar_hover": "#223A57",
    "sidebar_active": "#2A4B70",
    "accent": "#175CD3",
    "accent_hover": "#0E4BAD",
    "accent_pale": "#E7F0FF",
    "success": "#16794B",
    "success_pale": "#E7F6ED",
    "warning": "#96621C",
    "warning_pale": "#FFF3DB",
    "danger": "#B42332",
    "danger_hover": "#94202C",
    "white": "#FFFFFF",
}

FONT = "Segoe UI"


def configure_styles(style: ttk.Style) -> None:
    """Apply a predictable theme on Windows and Linux.

    The ``clam`` ttk theme exposes the surface/button/selection styling used by
    the design without pulling in third-party themes or assets.
    """
    if "clam" in style.theme_names():
        style.theme_use("clam")

    c = COLORS
    style.configure(".", font=(FONT, 10), background=c["background"], foreground=c["text"])
    style.configure("App.TFrame", background=c["background"])
    style.configure("Surface.TFrame", background=c["surface"])
    style.configure("Surface.TLabel", background=c["surface"], foreground=c["text"])
    style.configure("Muted.Surface.TLabel", background=c["surface"], foreground=c["muted"])
    style.configure("Muted.TLabel", background=c["background"], foreground=c["muted"])
    style.configure("Title.TLabel", background=c["background"], foreground=c["text"], font=(FONT, 23, "bold"))
    style.configure("Section.TLabel", background=c["background"], foreground=c["text"], font=(FONT, 17, "bold"))
    style.configure("PanelTitle.TLabel", background=c["surface"], foreground=c["text"], font=(FONT, 12, "bold"))
    style.configure("Primary.TButton", background=c["accent"], foreground=c["white"],
                    borderwidth=0, relief="flat", padding=(18, 11), font=(FONT, 10, "bold"))
    style.map("Primary.TButton", background=[("disabled", "#AFC4E4"), ("active", c["accent_hover"])],
              foreground=[("disabled", c["white"])])
    style.configure("Secondary.TButton", background=c["surface"], foreground=c["text"],
                    bordercolor=c["border"], borderwidth=1, relief="flat", padding=(15, 10), font=(FONT, 10))
    style.map("Secondary.TButton", background=[("active", c["surface_alt"]), ("disabled", c["surface_alt"])])
    style.configure("Danger.TButton", background=c["danger"], foreground=c["white"],
                    borderwidth=0, relief="flat", padding=(15, 10), font=(FONT, 10, "bold"))
    style.map("Danger.TButton", background=[("active", c["danger_hover"]), ("disabled", "#D8ADB2")])
    style.configure("TEntry", padding=(8, 9), fieldbackground=c["white"], bordercolor=c["border"])
    style.configure("TCombobox", padding=(7, 8), fieldbackground=c["white"], background=c["white"])
    style.configure("TCheckbutton", background=c["surface"], foreground=c["text"], font=(FONT, 10))
    style.map("TCheckbutton", background=[("active", c["surface"])])
    style.configure("Treeview", background=c["white"], fieldbackground=c["white"], foreground=c["text"],
                    rowheight=36, borderwidth=0, font=(FONT, 10))
    style.map("Treeview", background=[("selected", c["accent_pale"])],
              foreground=[("selected", c["text"])])
    style.configure("Treeview.Heading", background=c["surface_alt"], foreground=c["muted"],
                    relief="flat", padding=(9, 10), font=(FONT, 10, "bold"))
    style.map("Treeview.Heading", background=[("active", c["border"])])
    style.configure("Horizontal.TProgressbar", background=c["accent"], troughcolor=c["surface_alt"],
                    borderwidth=0)
