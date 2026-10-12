"""Regressionstests — bugfix-library-transfer 2026-06-21."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import manage_translations as mt


class TestD1QMenuParent(unittest.TestCase):
    """BUG-D1: QMenu ohne Parent-Argument — GC-Risiko."""

    def test_datenschutzampel_tray_menu_has_parent(self):
        """ProFiler_Datenschutzampel.py: tray_menu = QMenu() muss parent haben."""
        src = (Path(__file__).parent.parent / "ProFiler_Datenschutzampel.py").read_text(encoding="utf-8")
        idx = src.find("tray_menu = QMenu")
        self.assertGreater(idx, 0, "tray_menu QMenu-Zeile nicht gefunden")
        snippet = src[idx:idx + 40]
        self.assertIn("QMenu(self", snippet,
                      "tray_menu ohne Parent — BUG-D1 in ProFiler_Datenschutzampel.py")

    def test_v15_no_bare_qmenu(self):
        """Profiler_Suite_V15.py: kein QMenu() ohne Parent-Argument (vollständiger Scan)."""
        src = (Path(__file__).parent.parent / "Profiler_Suite_V15.py").read_text(encoding="utf-8")
        occurrences = []
        start = 0
        while True:
            idx = src.find("QMenu()", start)
            if idx == -1:
                break
            line_no = src[:idx].count("\n") + 1
            occurrences.append(line_no)
            start = idx + 1
        self.assertEqual(occurrences, [],
                         f"QMenu() ohne Parent in V15 — BUG-D1, Zeilen: {occurrences}")


class TestD3SubprocessTimeout(unittest.TestCase):
    """BUG-D3: subprocess.run ohne timeout= konnte GUI-Thread blockieren."""

    def test_soffice_conversion_has_timeout(self):
        """subprocess.run für LibreOffice-Konvertierung muss timeout= enthalten."""
        src = (Path(__file__).parent.parent / "Profiler_Suite_V15.py").read_text(encoding="utf-8")
        idx = src.find("'soffice'")
        self.assertGreater(idx, 0, "soffice-Aufruf in V15 nicht gefunden")
        snippet = src[idx:idx + 200]
        self.assertIn("timeout", snippet,
                      "subprocess.run für soffice ohne timeout= — BUG-D3")


class TestU1MakedirsExistOk(unittest.TestCase):
    """BUG-U1: os.makedirs ohne exist_ok=True."""

    def test_ensure_folder_uses_exist_ok(self):
        """import_excel_to_profiler.py: ensure_folder muss exist_ok=True nutzen."""
        src = (Path(__file__).parent.parent / "import_excel_to_profiler.py").read_text(encoding="utf-8")
        idx = src.find("def ensure_folder")
        self.assertGreater(idx, 0, "ensure_folder nicht gefunden")
        snippet = src[idx:idx + 180]
        self.assertIn("exist_ok", snippet,
                      "Ordneranlage ohne exist_ok=True — BUG-U1 in import_excel_to_profiler.py")
        self.assertIn("parents=True", snippet)


class TestU2ManageTranslations(unittest.TestCase):
    """BUG-U2: manage_translations lud korrupte JSON ohne JSONDecodeError-Handler."""

    def test_corrupted_json_does_not_raise(self):
        """Korrupte translations.json darf keine unkontrollierte Exception werfen."""
        with tempfile.TemporaryDirectory() as tmpdir:
            trans_file = os.path.join(tmpdir, "locales", "translations.json")
            os.makedirs(os.path.dirname(trans_file), exist_ok=True)
            with open(trans_file, "w", encoding="utf-8") as f:
                f.write("{corrupted json")
            try:
                mt.manage_translations(tmpdir)
            except json.JSONDecodeError:
                self.fail("JSONDecodeError nicht gefangen — BUG-U2 in manage_translations")


class TestD4VisibleGermanUmlauts(unittest.TestCase):
    """BUG-D4: Sichtbare deutsche UI-Texte verloren Umlaute."""

    def test_v15_visible_text_keeps_real_umlauts(self):
        """Bekannte sichtbare UI-Verlustformen dürfen nicht mehr vorkommen."""
        src = (Path(__file__).parent.parent / "Profiler_Suite_V15.py").read_text(encoding="utf-8")
        forbidden = [
            "Abwhlen [SPACE]",
            "Loeschen (Papierkorb)",
            "Loeschen (Permanent)",
            "Loeschen bestätigen",
            "Uebernommene Einstellungen",
            "nicht uebernommen",
            "Ungueltiger Export",
            "Kann jetzt eingefgt werden",
            "enthaelt keine Dateien",
        ]
        for text in forbidden:
            with self.subTest(text=text):
                self.assertNotIn(text, src)

        required = [
            "Abwählen [SPACE]",
            "Löschen (Papierkorb)",
            "Löschen (Permanent)",
            "Löschen bestätigen",
            "Übernommene Einstellungen",
            "nicht übernommen",
            "Ungültiger Export",
            "Kann jetzt eingefügt werden",
            "enthält keine Dateien",
        ]
        for text in required:
            with self.subTest(text=text):
                self.assertIn(text, src)


class TestD5FileActionControlFlow(unittest.TestCase):
    """BUG-D5: Dateiaktionen enthielten alten Doppelcode und defekte Clipboard-Pfade."""

    def test_unhide_selected_does_not_run_restore_duplicate(self):
        """Nach safety_unhide darf kein alter restore_version-Doppelblock weiterlaufen."""
        src = (Path(__file__).parent.parent / "Profiler_Suite_V15.py").read_text(encoding="utf-8")
        start = src.index("def unhide_selected")
        end = src.index("def copy_selected", start)
        block = src[start:end]
        self.assertIn("safety_unhide_version", block)
        self.assertNotIn("restore_version", block)
        self.assertNotIn("Stellt gelschte Dateien", block)

    def test_copy_selected_non_windows_path_imports_qmimedata_and_has_no_dangling_result(self):
        """Der Nicht-Windows-Clipboard-Pfad braucht QMimeData und darf kein fremdes result nutzen."""
        src = (Path(__file__).parent.parent / "Profiler_Suite_V15.py").read_text(encoding="utf-8")
        self.assertIn("QMimeData", src.split("from PySide6.QtCore import", 1)[1].split(")", 1)[0])

        start = src.index("def copy_selected")
        end = src.index("def rename_selected", start)
        block = src[start:end]
        self.assertNotIn("result['id']", block)
        self.assertNotIn("result['db']", block)


class TestCrossPlatformTestSandbox(unittest.TestCase):
    """The pytest sandbox narrowly permits null-sink opens and redirects Qt paths."""

    def test_null_sink_open_is_allowed_but_device_mutations_remain_blocked(self):
        from conftest import _REPO_ROOT, _SANDBOX, _path_is_sandboxed, _sandbox_audit

        self.assertFalse(_path_is_sandboxed(os.devnull))
        self.assertTrue(_path_is_sandboxed(_SANDBOX / "expected-write.txt"))
        self.assertFalse(_path_is_sandboxed(_REPO_ROOT / "README.md"))
        _sandbox_audit("open", (os.devnull, "w", os.O_WRONLY))
        outside_probe = _REPO_ROOT.parent / "dev-other"
        with self.assertRaises(PermissionError):
            _sandbox_audit("open", (outside_probe, "w", os.O_WRONLY | os.O_CREAT))
        with self.assertRaises(PermissionError):
            _sandbox_audit("os.remove", (os.devnull,))
        with self.assertRaises(PermissionError):
            _sandbox_audit("os.chmod", (os.devnull, 0o600))

    def test_qt_writable_and_search_locations_stay_in_task_sandbox(self):
        from conftest import (
            _REPO_ROOT,
            _SANDBOX,
            _qt_sandbox_path_map,
            _redirect_qt_location,
            _redirect_qt_locations,
        )
        from PySide6.QtCore import QStandardPaths

        outside_result = str(_REPO_ROOT.parent / "runner-preferences")
        fake_original = lambda _location: outside_result
        sandbox_paths = _qt_sandbox_path_map(QStandardPaths)
        config_path = _SANDBOX / "qt-app-config"
        self.assertEqual(
            _redirect_qt_location(
                QStandardPaths.AppConfigLocation, sandbox_paths, fake_original
            ),
            str(config_path),
        )
        self.assertEqual(
            _redirect_qt_locations(
                QStandardPaths.AppConfigLocation, sandbox_paths, fake_original
            ),
            [str(config_path)],
        )

        locations = (
            QStandardPaths.AppConfigLocation,
            QStandardPaths.AppDataLocation,
            QStandardPaths.CacheLocation,
            QStandardPaths.GenericCacheLocation,
            QStandardPaths.GenericDataLocation,
            QStandardPaths.HomeLocation,
            QStandardPaths.RuntimeLocation,
            QStandardPaths.TempLocation,
        )
        sandbox = _SANDBOX.resolve()
        for location in locations:
            writable = Path(QStandardPaths.writableLocation(location)).resolve()
            self.assertTrue(writable.is_relative_to(sandbox), str(writable))
            standard = QStandardPaths.standardLocations(location)
            self.assertTrue(standard)
            self.assertTrue(
                all(Path(path).resolve().is_relative_to(sandbox) for path in standard),
                f"{location}: {standard}",
            )


    def test_open_file_descriptors_are_allowed_only_when_their_paths_are_sandboxed(self):
        import tempfile

        from conftest import _REPO_ROOT, _path_is_sandboxed, _sandbox_audit

        with tempfile.TemporaryDirectory(dir=os.environ["TEMP"]) as temp_root:
            sandbox_file = Path(temp_root) / "owned.txt"
            sandbox_file.write_text("sandbox", encoding="utf-8")
            sandbox_fd = os.open(sandbox_file, os.O_RDONLY)
            outside_fd = os.open(_REPO_ROOT / "README.md", os.O_RDONLY)
            try:
                self.assertTrue(_path_is_sandboxed(sandbox_fd))
                self.assertFalse(_path_is_sandboxed(outside_fd))
                self.assertFalse(_path_is_sandboxed(-1))
                self.assertFalse(_path_is_sandboxed("README.md", dir_fd=-1))
                with self.assertRaises(PermissionError):
                    _sandbox_audit("os.remove", ("README.md", -1))
                sandbox_relative_to_repo = os.path.relpath(sandbox_file, _REPO_ROOT)
                self.assertFalse(
                    _path_is_sandboxed(sandbox_relative_to_repo, dir_fd=outside_fd)
                )
                with self.assertRaises(PermissionError):
                    _sandbox_audit("os.remove", (sandbox_relative_to_repo, outside_fd))
            finally:
                os.close(outside_fd)
                os.close(sandbox_fd)

    def test_dir_fd_cleanup_is_confined_to_resolved_sandbox_directory(self):
        import shutil
        import tempfile

        from conftest import _REPO_ROOT, _path_is_sandboxed, _sandbox_audit

        if os.remove not in getattr(os, "supports_dir_fd", set()):
            with self.assertRaises(PermissionError):
                _sandbox_audit("os.remove", ("README.md", 999999))
            return

        with tempfile.TemporaryDirectory(dir=os.environ["TEMP"]) as temp_root:
            sandbox_root = Path(temp_root)
            staging = sandbox_root / "staging"
            staging.mkdir()
            (staging / "payload.txt").write_text("owned test data", encoding="utf-8")
            sandbox_fd = os.open(sandbox_root, os.O_RDONLY)
            outside_fd = os.open(_REPO_ROOT, os.O_RDONLY)
            try:
                self.assertTrue(
                    _path_is_sandboxed("staging/payload.txt", dir_fd=sandbox_fd)
                )
                _sandbox_audit("os.remove", ("staging/payload.txt", sandbox_fd))
                shutil.rmtree("staging", dir_fd=sandbox_fd)
                self.assertFalse(staging.exists())

                self.assertFalse(_path_is_sandboxed("README.md", dir_fd=outside_fd))
                with self.assertRaises(PermissionError):
                    _sandbox_audit("os.remove", ("README.md", outside_fd))

                escape_link = sandbox_root / "repo-escape"
                os.symlink(_REPO_ROOT, escape_link)
                with self.assertRaises(PermissionError):
                    _sandbox_audit(
                        "os.remove", ("repo-escape/README.md", sandbox_fd)
                    )
                _sandbox_audit("os.remove", ("repo-escape", sandbox_fd))
                os.remove("repo-escape", dir_fd=sandbox_fd)
                self.assertFalse(escape_link.is_symlink())
            finally:
                os.close(outside_fd)
                os.close(sandbox_fd)

class TestBugsweepDatenschutzampelToolLinks(unittest.TestCase):
    """BUGSWEEP-2026-09-13: _build_tool_links muss privacy_data und resolve_read_path unterstützen."""

    def test_build_tool_links_source_has_privacy_data_fallback(self):
        src = (Path(__file__).parent.parent / "workspace_exchange.py").read_text(encoding="utf-8")
        self.assertIn("def _build_tool_links(", src)
        self.assertIn("privacy_data: dict[str, Any] | None = None", src)
        self.assertIn("resolve_read_path(PRIVACY_CONFIG_PATH.name).exists()", src)


class TestBugsweepWorkspaceExchangeAndExcelImport(unittest.TestCase):
    """BUGSWEEP-2026-09-20: Workspace Exchange & Excel Import Robustheit."""

    def test_summarize_database_with_none_sources_does_not_raise(self):
        from workspace_exchange import PathRedactor, _summarize_database

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.write(b"")
            db_file = Path(f.name)
        try:
            conn = {"id": "c1", "name": "Index", "sources": None}
            summary = _summarize_database(db_file, conn, PathRedactor())
            self.assertEqual(summary["sources_count"], 0)
        finally:
            if db_file.exists():
                db_file.unlink()

    def test_path_redactor_and_validation_handles_file_urls(self):
        from workspace_exchange import PathRedactor, WorkspaceFormatError, _validate_safe_tree

        redactor = PathRedactor()
        self.assertTrue(PathRedactor._is_absolute_path("file:///C:/Users/User/docs"))
        redacted = redactor.redact("file:///C:/Users/User/docs")
        self.assertEqual(redacted, "[path-1]")

        with self.assertRaises(WorkspaceFormatError):
            _validate_safe_tree({"leak": "file:///C:/Users/User/secret.txt"})

    def test_validate_import_settings_rejects_out_of_bounds_trash_retention(self):
        from workspace_exchange import WorkspaceFormatError, _validate_import_settings

        with self.assertRaises(WorkspaceFormatError):
            _validate_import_settings({"trash_retention_days": -1})
        with self.assertRaises(WorkspaceFormatError):
            _validate_import_settings({"trash_retention_days": 5000})

    def test_excel_sanitize_filename_handles_windows_reserved_names(self):
        from import_excel_to_profiler import sanitize_filename

        self.assertEqual(sanitize_filename("CON"), "_CON")
        self.assertEqual(sanitize_filename("prn"), "_prn")
        self.assertEqual(sanitize_filename("NUL"), "_NUL")

    def test_excel_importer_deduplicates_tags(self):
        import sqlite3
        from import_excel_to_profiler import ProfilerAutismoImporter

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "test.db"
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE tags(id INTEGER PRIMARY KEY, file_id INTEGER, tag TEXT)")
            conn.close()

            with ProfilerAutismoImporter(db_path, tmp_path / "out") as importer:
                importer.add_tags(1, ["alpha", "alpha", "beta"])
                importer.add_tags(1, ["beta", "gamma"])

            conn = sqlite3.connect(db_path)
            try:
                rows = conn.execute("SELECT tag FROM tags WHERE file_id = 1 ORDER BY id").fetchall()
                tags = [r[0] for r in rows]
                self.assertEqual(tags, ["alpha", "beta", "gamma"])
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()

