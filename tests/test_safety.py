"""Safety regressions for cleanup, plan validity and deferred GUI errors."""
from __future__ import annotations

import os
import inspect
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from academic_toolkit import career_engine, system_prepare
from academic_toolkit.desktop_app import DesktopApp


class CleanupSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.owned = self.base / system_prepare.APP_TEMP_DIR
        self.owned.mkdir()
        self.root_patch = patch.object(system_prepare, "app_temp_root", return_value=self.owned)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def _make_stale(self, path: Path) -> None:
        timestamp = time.time() - 9 * 86400
        os.utime(path, (timestamp, timestamp))

    def test_dry_run_only_counts_old_managed_files(self) -> None:
        old = self.owned / "download.tmp"
        old.write_text("temporary data", encoding="utf-8")
        self._make_stale(old)
        (self.owned / "recent.tmp").write_text("new", encoding="utf-8")
        (self.owned / "important.txt").write_text("keep", encoding="utf-8")
        folder = self.owned / "other-program"
        folder.mkdir()
        (folder / "old.tmp").write_text("keep", encoding="utf-8")

        result = system_prepare.clean_temporaries(dry_run=True)

        self.assertEqual(result.removed, 1)
        self.assertEqual(result.bytes_freed, len("temporary data"))
        self.assertTrue(old.exists())
        self.assertTrue((folder / "old.tmp").exists())

    def test_execute_keeps_other_files_and_directories(self) -> None:
        old = self.owned / "old.cache"
        old.write_text("cache", encoding="utf-8")
        self._make_stale(old)
        unrelated = self.base / "unrelated.tmp"
        unrelated.write_text("not ours", encoding="utf-8")
        nested = self.owned / "nested"
        nested.mkdir()
        (nested / "nested.tmp").write_text("keep", encoding="utf-8")

        result = system_prepare.clean_temporaries(dry_run=False)

        self.assertEqual(result.removed, 1)
        self.assertFalse(old.exists())
        self.assertTrue(unrelated.exists())
        self.assertTrue((nested / "nested.tmp").exists())

    def test_symlinked_root_is_never_cleaned(self) -> None:
        target = self.base / "outside"
        target.mkdir()
        old = target / "secret.tmp"
        old.write_text("keep", encoding="utf-8")
        self._make_stale(old)
        self.owned.rmdir()
        try:
            self.owned.symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest("Creating symlinks is restricted on this platform")

        result = system_prepare.clean_temporaries(dry_run=False)

        self.assertEqual(result.removed, 0)
        self.assertTrue(old.exists())

    def test_age_floor_cannot_be_disabled(self) -> None:
        with self.assertRaises(ValueError):
            system_prepare.clean_temporaries(dry_run=False, min_age_days=0)


class CompatibilityTests(unittest.TestCase):
    def _device(self, *, ram: float | None = 4, disk: float = 2,
                virtualization: bool = False) -> career_engine.DeviceProfile:
        return career_engine.DeviceProfile("Windows", "AMD64", ram, disk, True, virtualization)

    def test_unknown_ram_is_not_assumed_compatible(self) -> None:
        compatible, reason = career_engine._compatible(
            {"requires": {"ram_gb": 8}}, self._device(ram=None))
        self.assertFalse(compatible)
        self.assertIn("RAM", reason)

    def test_low_disk_space_blocks_required_package(self) -> None:
        compatible, reason = career_engine._compatible(
            {"requires": {"disk_gb": 10}}, self._device(disk=2))
        self.assertFalse(compatible)
        self.assertIn("disk", reason)

    def test_virtualization_must_be_verified(self) -> None:
        compatible, _ = career_engine._compatible(
            {"requires": {"virtualization": True}}, self._device(virtualization=False))
        self.assertFalse(compatible)

    def test_virtualization_requires_positive_windows_probe(self) -> None:
        with patch.object(career_engine.platform, "system", return_value="Windows"), \
             patch.object(career_engine.shutil, "which", return_value="powershell.exe"), \
             patch.object(career_engine.subprocess, "run", return_value=SimpleNamespace(
                 returncode=0, stdout="False\n")):
            self.assertFalse(career_engine._virtualization_enabled())
        with patch.object(career_engine.platform, "system", return_value="Windows"), \
             patch.object(career_engine.shutil, "which", return_value="powershell.exe"), \
             patch.object(career_engine.subprocess, "run", return_value=SimpleNamespace(
                 returncode=0, stdout="True\n")):
            self.assertTrue(career_engine._virtualization_enabled())


class DesktopSafetyTests(unittest.TestCase):
    def test_preparation_does_not_invoke_cache_cleanup(self) -> None:
        source = inspect.getsource(DesktopApp._career_prepare)
        self.assertNotIn("clean_temporaries(", source)

    def test_deferred_exception_message_survives_except_block(self) -> None:
        callbacks = []
        fake = Mock()
        fake.after.side_effect = lambda _delay, callback: callbacks.append(callback)
        DesktopApp._schedule_error(fake, RuntimeError("winget falló"))
        self.assertEqual(len(callbacks), 1)
        callbacks[0]()
        fake._error.assert_called_once_with("winget falló")

    def test_changing_selection_invalidates_existing_plan(self) -> None:
        fake = Mock()
        fake.plan_epoch = 3
        fake.current_plan = {"career": {"id": "old"}}
        DesktopApp._invalidate_plan(fake)
        self.assertEqual(fake.plan_epoch, 4)
        self.assertIsNone(fake.current_plan)
        fake.prepare_btn.configure.assert_called_once_with(state="disabled")

    def test_prepare_rejects_stale_career_plan(self) -> None:
        fake = Mock()
        fake.current_plan = {"career": {"id": "old"}, "tiers": ["essential"], "items": []}
        fake.career_by_name = {"Civil": {"id": "civil"}}
        fake.career_var.get.return_value = "Civil"
        fake._selected_tiers.return_value = ["essential"]
        with patch("academic_toolkit.desktop_app.messagebox.showwarning") as warning:
            DesktopApp._career_prepare(fake)
        fake._invalidate_plan.assert_called_once()
        warning.assert_called_once()


class MySqlDefaultSafetyTests(unittest.TestCase):
    def test_lan_access_requires_explicit_switch(self) -> None:
        source = (Path(__file__).resolve().parents[1]
                  / "scripts/labs/mysql-smart-setup/mysql-smart-setup.ps1").read_text(encoding="utf-8")
        self.assertIn("[switch]$AllowLan", source)
        self.assertIn("$lanEnabled = [bool]$AllowLan", source)
        self.assertIn("'127.0.0.1'", source)
        self.assertIn("Set-LanFirewall -Instance $instance -SelectedPort $Port -LanEnabled:$false", source)


if __name__ == "__main__":
    unittest.main()
