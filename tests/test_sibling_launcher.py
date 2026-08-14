"""Unit-Tests für sibling_launcher.py — modularer Geschwister-App-Starter.

Alle Tests laufen vollständig ohne echte Subprozesse (subprocess.Popen wird
gemockt) und ohne PySide6-Abhängigkeit.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Repo-Root eine Ebene über tests/ in den Suchpfad aufnehmen
sys.path.insert(0, str(Path(__file__).parent.parent))

from sibling_launcher import (
    LaunchOutcome,
    LaunchResult,
    launch_prosync,
    launch_sibling,
    launch_tool_process,
    normalize_configured_tool_path,
    resolve_prosync_launch_path,
)

# ---------------------------------------------------------------------------
# normalize_configured_tool_path
# ---------------------------------------------------------------------------

class TestNormalizeConfiguredToolPath(unittest.TestCase):

    def test_empty_returns_none(self):
        self.assertIsNone(normalize_configured_tool_path("/base", ""))

    def test_whitespace_only_returns_none(self):
        self.assertIsNone(normalize_configured_tool_path("/base", "   "))

    def test_absolute_path_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            expected = Path(tmp) / "tool.py"
            result = normalize_configured_tool_path("/base", str(expected))
            self.assertEqual(result, expected)

    def test_relative_path_anchored_to_base_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "ProFiler"
            result = normalize_configured_tool_path(str(base), "subdir/tool.py")
            self.assertEqual(result, base / "subdir" / "tool.py")

    def test_windows_percent_var_expanded(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["_PFTEST_VAR"] = tmp
            self.addCleanup(os.environ.pop, "_PFTEST_VAR", None)
            result = normalize_configured_tool_path("/base", r"%_PFTEST_VAR%\tool.py")
            self.assertEqual(result, Path(tmp) / "tool.py")

    def test_unknown_var_kept_as_literal(self):
        result = normalize_configured_tool_path("/base", "%NONEXISTENT_VAR_XYZ%")
        # Soll nicht werfen; resultierender Pfad enthält den Literalstring
        self.assertIn("NONEXISTENT_VAR_XYZ", str(result))


# ---------------------------------------------------------------------------
# resolve_prosync_launch_path
# ---------------------------------------------------------------------------

class TestResolveProSyncLaunchPath(unittest.TestCase):

    def test_configured_file_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "REL-PUB_ProFiler"
            base.mkdir()
            target = Path(tmp) / "custom" / "ProSync.exe"
            target.parent.mkdir()
            target.write_text("", encoding="utf-8")

            result = resolve_prosync_launch_path(base, str(target))

            self.assertEqual(result, target)

    def test_configured_dir_prefers_exe_over_py(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "REL-PUB_ProFiler"
            base.mkdir()
            cfg_dir = Path(tmp) / "custom"
            cfg_dir.mkdir()
            exe = cfg_dir / "ProSync.exe"
            py_ = cfg_dir / "ProSyncStart_V3.1.py"
            py_.write_text("", encoding="utf-8")
            exe.write_text("", encoding="utf-8")

            result = resolve_prosync_launch_path(base, str(cfg_dir))

            self.assertEqual(result, exe)

    def test_relative_path_resolves_from_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "REL-PUB_ProFiler"
            base.mkdir()
            tools_dir = base / "tools"
            tools_dir.mkdir()
            expected = tools_dir / "ProSyncStart_V3.1.py"
            expected.write_text("", encoding="utf-8")

            result = resolve_prosync_launch_path(base, "tools")

            self.assertEqual(result, expected)

    def test_sibling_dir_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "REL-PUB_ProFiler"
            base.mkdir()
            sibling = Path(tmp) / "REL-PUB_ProSync"
            sibling.mkdir()
            expected = sibling / "ProSyncStart_V3.1.py"
            expected.write_text("", encoding="utf-8")

            result = resolve_prosync_launch_path(base)

            self.assertEqual(result, expected)

    def test_not_found_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "REL-PUB_ProFiler"
            base.mkdir()

            result = resolve_prosync_launch_path(base)

            self.assertIsNone(result)

    def test_windows_env_var_in_configured_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "REL-PUB_ProFiler"
            base.mkdir()
            cfg_dir = Path(tmp) / "envtool"
            cfg_dir.mkdir()
            expected = cfg_dir / "ProSyncStart_V3.1.py"
            expected.write_text("", encoding="utf-8")
            os.environ["_PFTEST_SYNC_DIR"] = str(cfg_dir)
            self.addCleanup(os.environ.pop, "_PFTEST_SYNC_DIR", None)

            result = resolve_prosync_launch_path(base, r"%_PFTEST_SYNC_DIR%")

            self.assertEqual(result, expected)


# ---------------------------------------------------------------------------
# launch_tool_process
# ---------------------------------------------------------------------------

class TestLaunchToolProcess(unittest.TestCase):

    @patch("sibling_launcher.subprocess.Popen")
    def test_py_uses_sys_executable(self, mock_popen):
        with tempfile.TemporaryDirectory() as tmp:
            tool = Path(tmp) / "tool.py"
            tool.write_text("", encoding="utf-8")
            launch_tool_process(tool)
            mock_popen.assert_called_once_with(
                [sys.executable, str(tool)], cwd=tmp
            )

    @patch("sibling_launcher.subprocess.Popen")
    def test_bat_uses_cmd_c(self, mock_popen):
        with tempfile.TemporaryDirectory() as tmp:
            tool = Path(tmp) / "run.bat"
            tool.write_text("", encoding="utf-8")
            launch_tool_process(tool)
            mock_popen.assert_called_once_with(
                ["cmd", "/c", str(tool)], cwd=tmp
            )

    @patch("sibling_launcher.subprocess.Popen")
    def test_exe_called_directly(self, mock_popen):
        with tempfile.TemporaryDirectory() as tmp:
            tool = Path(tmp) / "App.exe"
            tool.write_text("", encoding="utf-8")
            launch_tool_process(tool)
            mock_popen.assert_called_once_with([str(tool)], cwd=tmp)

    @patch("sibling_launcher.subprocess.Popen", side_effect=OSError("no such file"))
    def test_raises_on_error(self, _mock):
        with tempfile.TemporaryDirectory() as tmp:
            tool = Path(tmp) / "tool.exe"
            tool.write_text("", encoding="utf-8")
            with self.assertRaises(OSError):
                launch_tool_process(tool)


# ---------------------------------------------------------------------------
# launch_prosync
# ---------------------------------------------------------------------------

class TestLaunchProSync(unittest.TestCase):

    def test_not_found_returns_not_found_outcome(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "REL-PUB_ProFiler"
            base.mkdir()

            outcome = launch_prosync(base)

            self.assertEqual(outcome.result, LaunchResult.NOT_FOUND)
            self.assertFalse(outcome.ok)
            self.assertIn("prosync_path", outcome.message)
            self.assertIsNone(outcome.path)

    @patch("sibling_launcher.subprocess.Popen")
    def test_success_returns_success_outcome(self, mock_popen):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "REL-PUB_ProFiler"
            base.mkdir()
            sibling = Path(tmp) / "REL-PUB_ProSync"
            sibling.mkdir()
            target = sibling / "ProSyncStart_V3.1.py"
            target.write_text("", encoding="utf-8")

            outcome = launch_prosync(base)

            self.assertEqual(outcome.result, LaunchResult.SUCCESS)
            self.assertTrue(outcome.ok)
            self.assertEqual(outcome.path, target)
            mock_popen.assert_called_once()

    @patch("sibling_launcher.subprocess.Popen", side_effect=OSError("boom"))
    def test_launch_error_returns_error_outcome(self, _mock):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "REL-PUB_ProFiler"
            base.mkdir()
            sibling = Path(tmp) / "REL-PUB_ProSync"
            sibling.mkdir()
            target = sibling / "ProSyncStart_V3.1.py"
            target.write_text("", encoding="utf-8")

            outcome = launch_prosync(base)

            self.assertEqual(outcome.result, LaunchResult.LAUNCH_ERROR)
            self.assertFalse(outcome.ok)
            self.assertIn("boom", outcome.message)

    @patch("sibling_launcher.subprocess.Popen")
    def test_configured_path_used(self, mock_popen):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "REL-PUB_ProFiler"
            base.mkdir()
            custom = Path(tmp) / "custom"
            custom.mkdir()
            target = custom / "ProSync.exe"
            target.write_text("", encoding="utf-8")

            outcome = launch_prosync(base, str(target))

            self.assertTrue(outcome.ok)
            self.assertEqual(outcome.path, target)


# ---------------------------------------------------------------------------
# launch_sibling
# ---------------------------------------------------------------------------

class TestLaunchSibling(unittest.TestCase):

    def test_not_found_message_contains_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "ProFiler"
            base.mkdir()

            outcome = launch_sibling("myfoo", "MyFoo", base)

            self.assertEqual(outcome.result, LaunchResult.NOT_FOUND)
            self.assertIn("myfoo_path", outcome.message)

    @patch("sibling_launcher.subprocess.Popen")
    def test_custom_candidates_fn_used(self, mock_popen):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "ProFiler"
            base.mkdir()
            custom_tool = Path(tmp) / "mytool.py"
            custom_tool.write_text("", encoding="utf-8")

            def my_candidates(bd, cfg):
                return [custom_tool]

            outcome = launch_sibling("mytool", "MyTool", base, candidates_fn=my_candidates)

            self.assertTrue(outcome.ok)
            self.assertEqual(outcome.path, custom_tool)
            mock_popen.assert_called_once()

    @patch("sibling_launcher.subprocess.Popen")
    def test_sibling_dir_found_via_display_name(self, mock_popen):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "REL-PUB_ProFiler"
            base.mkdir()
            sibling = Path(tmp) / "REL-PUB_TestApp"
            sibling.mkdir()
            target = sibling / "TestApp.exe"
            target.write_text("", encoding="utf-8")

            outcome = launch_sibling("testapp", "TestApp", base)

            self.assertTrue(outcome.ok)
            self.assertEqual(outcome.path, target)


# ---------------------------------------------------------------------------
# LaunchOutcome
# ---------------------------------------------------------------------------

class TestLaunchOutcome(unittest.TestCase):

    def test_ok_true_on_success(self):
        o = LaunchOutcome(result=LaunchResult.SUCCESS, message="ok")
        self.assertTrue(o.ok)

    def test_ok_false_on_not_found(self):
        o = LaunchOutcome(result=LaunchResult.NOT_FOUND, message="nf")
        self.assertFalse(o.ok)

    def test_ok_false_on_launch_error(self):
        o = LaunchOutcome(result=LaunchResult.LAUNCH_ERROR, message="err")
        self.assertFalse(o.ok)


if __name__ == "__main__":
    unittest.main()
