"""Behavioral desktop tests that do not require a display server."""

from __future__ import annotations

import threading
import unittest
from unittest.mock import Mock

from academic_toolkit.desktop_app import DesktopApp
from academic_toolkit.ui_theme import COLORS


class DesktopInteractionTests(unittest.TestCase):
    def test_search_results_include_friendly_name_before_id(self) -> None:
        app = Mock()
        app._search_running = True
        app.software_tree.get_children.return_value = ("one",)
        DesktopApp._show_search(app, True, [{
            "Name": "Visual Studio Code", "Id": "Microsoft.VisualStudioCode",
            "Version": "1.0", "Source": "winget",
        }], "")
        app.software_tree.insert.assert_called_once_with(
            "", "end", values=("Visual Studio Code", "Microsoft.VisualStudioCode", "1.0 · winget"),
        )
        self.assertFalse(app._search_running)
        app.search_btn.configure.assert_called_once_with(state="normal")

    def test_installer_uses_package_id_not_friendly_name(self) -> None:
        app = Mock()
        app._software_busy = False
        app.software_tree.selection.return_value = ("one",)
        app.software_tree.item.return_value = ("Visual Studio Code", "Microsoft.VisualStudioCode", "1.0")
        self.assertEqual(DesktopApp._selected_package_id(app), "Microsoft.VisualStudioCode")

    def test_cancel_only_flags_queue_and_does_not_kill_installer(self) -> None:
        app = Mock()
        app._install_in_progress = True
        app._cancel_install = threading.Event()
        DesktopApp._request_cancel_install(app)
        self.assertTrue(app._cancel_install.is_set())
        app.cancel_prepare_btn.configure.assert_called_once_with(state="disabled")
        app.career_summary.set.assert_called_once()

    def test_nav_changes_page_and_heading(self) -> None:
        app = Mock()
        app._active_page = "home"
        app._pages = {"home": Mock(), "career": Mock()}
        app._nav = {"home": Mock(), "career": Mock()}
        app._page_metadata = {"career": ("Preparar mi PC", "Compatibilidad y plan de software")}
        DesktopApp._navigate(app, "career")
        app._pages["home"].pack_forget.assert_called_once()
        app._pages["career"].pack.assert_called_once_with(fill="both", expand=True)
        app.page_title.set.assert_called_once_with("Preparar mi PC")

    def test_ui_theme_has_distinct_semantic_states(self) -> None:
        self.assertNotEqual(COLORS["success"], COLORS["danger"])
        self.assertNotEqual(COLORS["surface"], COLORS["background"])


if __name__ == "__main__":
    unittest.main()
