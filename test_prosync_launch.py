"""Smoke tests for the ProSync companion launcher."""

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path


def load_profiler_module():
    """Load the main ProFiler module via importlib."""
    module_path = Path(__file__).with_name("Profiler_Suite_V15.py")
    spec = importlib.util.spec_from_file_location("profiler_companion", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ResolveProSyncLaunchPathTests(unittest.TestCase):
    """Regression tests for the optional ProSync companion launcher."""

    @classmethod
    def setUpClass(cls):
        cls.profiler = load_profiler_module()

    def test_configured_file_path_wins(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            base_dir = tmp / "REL-PUB_ProFiler"
            base_dir.mkdir()
            configured_file = tmp / "custom" / "ProSync.exe"
            configured_file.parent.mkdir()
            configured_file.write_text("", encoding="utf-8")

            resolved = self.profiler.resolve_prosync_launch_path(base_dir, str(configured_file))

            self.assertEqual(resolved, configured_file)

    def test_relative_path_resolves_from_profiler_root(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            base_dir = tmp / "REL-PUB_ProFiler"
            base_dir.mkdir()
            tools_dir = base_dir / "tools"
            tools_dir.mkdir()
            expected = tools_dir / "ProSyncStart_V3.1.py"
            expected.write_text("", encoding="utf-8")

            resolved = self.profiler.resolve_prosync_launch_path(base_dir, "tools")

            self.assertEqual(resolved, expected)

    def test_windows_style_environment_variables_are_expanded(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            base_dir = tmp / "REL-PUB_ProFiler"
            base_dir.mkdir()
            configured_dir = tmp / "envtool"
            configured_dir.mkdir()
            expected = configured_dir / "ProSyncStart_V3.1.py"
            expected.write_text("", encoding="utf-8")
            os.environ["PROFILER_TEST_TOOL"] = str(configured_dir)
            self.addCleanup(os.environ.pop, "PROFILER_TEST_TOOL", None)

            resolved = self.profiler.resolve_prosync_launch_path(
                base_dir,
                r"%PROFILER_TEST_TOOL%",
            )

            self.assertEqual(resolved, expected)

    def test_sibling_fallback_works(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            base_dir = tmp / "REL-PUB_ProFiler"
            base_dir.mkdir()
            sibling_root = tmp / "REL-PUB_ProSync"
            sibling_root.mkdir()
            expected = sibling_root / "ProSyncStart_V3.1.py"
            expected.write_text("", encoding="utf-8")

            resolved = self.profiler.resolve_prosync_launch_path(base_dir)

            self.assertEqual(resolved, expected)


if __name__ == "__main__":
    unittest.main()
