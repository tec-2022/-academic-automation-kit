"""Run GUI construction checks on a machine with a graphical desktop.

This is intentionally separate from the default headless unit-test discovery.
It does not install software, clean files or connect to external services.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from academic_toolkit.enhanced_gui import EnhancedDesktopApp  # noqa: E402


def main() -> None:
    app = EnhancedDesktopApp()
    try:
        # Simulate a compact laptop window and prove that key controls are
        # placed within its viewport before a user can run system operations.
        app.geometry("1000x690+10+10")
        app.update_idletasks()
        assert app._active_page == "home"
        screenshot_dir = os.environ.get("AAK_SCREENSHOT_DIR")
        if screenshot_dir:
            Path(screenshot_dir).mkdir(parents=True, exist_ok=True)
        for page, title in (
            ("career", "Preparar mi PC"), ("software", "Programas"),
            ("clean", "Mantenimiento"), ("assistant", "Asistente"),
            ("home", "Inicio"),
        ):
            app._navigate(page)
            app.update_idletasks()
            assert app.page_title.get() == title, page
            if page == "career":
                assert app.prepare_btn.winfo_height() > 20
            if page == "software":
                assert app.install_btn.winfo_height() > 20
            if screenshot_dir:
                try:
                    from PIL import ImageGrab
                    app.lift()
                    app.update()
                    x, y = app.winfo_rootx(), app.winfo_rooty()
                    w, h = app.winfo_width(), app.winfo_height()
                    ImageGrab.grab(bbox=(x, y, x + w, y + h),
                                   all_screens=True).save(Path(screenshot_dir) / f"{page}.png")
                except Exception as exc:
                    print(f"Optional screenshot unavailable ({page}): {exc}")
        assert app.prepare_btn.instate(["disabled"])
        assert app.install_btn.instate(["disabled"])
        assert app.uninstall_btn.instate(["disabled"])
        app._progress_begin(3)
        app._progress_step(2, 3, "Git")
        assert int(float(app.operation_progress["value"])) == 2
        print("Desktop UI smoke OK: navigation, initial safety states, progress")
    finally:
        app.destroy()


if __name__ == "__main__":
    main()
