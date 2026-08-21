#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproduzierbarer macOS-Plattform-Smoke für ProFiler Suite V15.

Der Smoke deckt die geplante macOS-Source-Linie ab:
- POSIX/macOS-App-Pfade via app_paths.py und Legacy-Fallback (~/.profiler_suite)
- Headless/Offscreen PySide6 UnifiedMainWindow-Initialisierung
- macOS-spezifische Datei- und Ordneröffner-Pfade ('open' und 'open -R')
- Cross-Platform Sibling-Launcher für Begleitmodule (.py, .sh, .command)
- Redigierter Workspace-Export (profiler-workspace-v1.json) ohne Secrets/BOM
- SQLite-CRUD und UTF-8-Umlaut-Roundtrip
- Graceful-Fallback bei fehlenden OCR-/PDF-Abhängigkeiten
- Tier-2 i18n Übersetzungssystem (de, en, es, zh, ja, ru) auf macOS
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication

import app_paths
import sibling_launcher
import translator
import workspace_exchange


def _ensure_app() -> QApplication:
    return QApplication.instance() or QApplication(sys.argv[:1])


def test_macos_app_paths_and_legacy_fallback() -> None:
    """Test 1: POSIX/macOS-Pfadauflösung und Legacy-Fallback."""
    print("Test 1: macOS App-Pfade und Legacy-Fallback")
    with tempfile.TemporaryDirectory(prefix="profiler-macos-home-") as temp_home:
        home_path = Path(temp_home)

        # 1. Standard POSIX app_data_dir
        app_dir = app_paths.app_data_dir(platform="darwin", home=home_path)
        expected_dir = home_path / ".profiler_suite"
        assert app_dir == expected_dir, f"app_dir {app_dir} != {expected_dir}"

        # 2. Config-Pfade
        cfg = app_paths.config_path("settings.json", platform="darwin", home=home_path)
        assert cfg == expected_dir / "settings.json"

        # 3. Legacy-Lesepfad Fallback
        legacy_dir = app_paths.legacy_config_dir(home=home_path)
        legacy_dir.mkdir(parents=True, exist_ok=True)
        legacy_file = legacy_dir / "profiler_settings.json"
        legacy_file.write_text(json.dumps({"theme": "dark", "lang": "de"}), encoding="utf-8")

        read_path = app_paths.resolve_read_path("profiler_settings.json", platform="darwin", home=home_path)
        assert read_path == legacy_file
    print("  OK  macOS App-Pfade und Fallbacks validiert\n")


def test_macos_offscreen_window_creation() -> None:
    """Test 2: Offscreen PySide6 UnifiedMainWindow auf macOS."""
    print("Test 2: Offscreen UnifiedMainWindow auf macOS")
    app = _ensure_app()
    with tempfile.TemporaryDirectory(prefix="profiler-macos-win-") as tmpd:
        tmp = Path(tmpd)
        import Profiler_Suite_V15 as profiler

        with mock.patch.object(profiler, "_CONFIG_DIR", tmp), \
             mock.patch.object(profiler, "SEARCH_CONFIG_PATH", str(tmp / "search.json")), \
             mock.patch.object(profiler, "SYNC_CONFIG_PATH", str(tmp / "profiler.json")), \
             mock.patch.object(profiler, "SETTINGS_PATH", str(tmp / "settings.json")):

            win = profiler.UnifiedMainWindow()
            try:
                assert win.isVisible() is False
                assert "ProFiler" in win.windowTitle()
                app.processEvents()
            finally:
                win.close()
                app.processEvents()
    print("  OK  Offscreen Hauptfenster erfolgreich erzeugt\n")


def test_macos_file_and_folder_open_dispatch() -> None:
    """Test 3: macOS System-Öffner ('open' und 'open -R')."""
    print("Test 3: macOS System-Öffner ('open' und 'open -R')")
    _ensure_app()
    import Profiler_Suite_V15 as profiler

    with tempfile.TemporaryDirectory(prefix="profiler-macos-open-") as tmpd:
        sample_file = Path(tmpd) / "Dokument_äöü.pdf"
        sample_file.write_text("dummy", encoding="utf-8")

        with mock.patch.object(sys, "platform", "darwin"), \
             mock.patch("subprocess.run") as mock_run:

            # 1. Datei öffnen
            win = MagicMock()
            win.get_selected_results.return_value = [{"path": str(sample_file)}]
            profiler.SearchWidgetHybrid.open_selected_file(win)
            mock_run.assert_called_with(["open", str(sample_file)], timeout=10)

            # 2. Im Finder anzeigen ('open -R')
            mock_run.reset_mock()
            profiler.SearchWidgetHybrid.show_in_explorer(win)
            mock_run.assert_called_with(["open", "-R", str(sample_file)], timeout=10)

    print("  OK  macOS 'open' und 'open -R' Dispatch verifiziert\n")


def test_macos_sibling_launcher() -> None:
    """Test 4: Sibling-Launcher auf Darwin (.py, .sh, .command)."""
    print("Test 4: Sibling-Launcher auf Darwin")
    with tempfile.TemporaryDirectory(prefix="profiler-macos-launch-") as tmpd:
        base = Path(tmpd) / "REL-PUB_ProFiler"
        base.mkdir()
        sibling = Path(tmpd) / "REL-PUB_ProSync"
        sibling.mkdir()
        script = sibling / "ProSyncStart_V3.1.py"
        script.write_text("#!/usr/bin/env python3\nprint('prosync')\n", encoding="utf-8")

        resolved = sibling_launcher.resolve_prosync_launch_path(base)
        assert resolved == script

        # Launch tool process mit Shell-Skript
        sh_tool = base / "tool.command"
        sh_tool.write_text("#!/bin/sh\necho test\n", encoding="utf-8")

        with mock.patch("sibling_launcher.subprocess.Popen") as mock_popen:
            sibling_launcher.launch_tool_process(sh_tool)
            mock_popen.assert_called_once_with(["sh", str(sh_tool)], cwd=str(base))

    print("  OK  Darwin Sibling-Launcher verifiziert\n")


class _FakeSearchManager:
    def __init__(self, dbs=None):
        self.dbs = list(dbs or [])


class _FakeSettingsManager:
    def __init__(self, data=None):
        self.data = dict(data or {})

    def set(self, key, value):
        self.data[key] = value


class _FakeConnectionManager:
    def __init__(self, connections=None):
        self._connections = list(connections or [])

    def list_connections(self):
        return list(self._connections)


def test_macos_workspace_exchange_without_bom_or_secrets() -> None:
    """Test 5: Workspace-Export auf macOS ohne Secrets und ohne UTF-8 BOM."""
    print("Test 5: Workspace-Export auf macOS")
    with tempfile.TemporaryDirectory(prefix="profiler-macos-ws-") as tmpd:
        tmp = Path(tmpd)
        export_file = tmp / "profiler-workspace-v1.json"

        settings = {
            "theme": "dark",
            "ui_language": "es",
            "pdf_master_password_open": "SUPER_SECRET_PWD_123",
            "pdf_user_password_open": "SECRET_USER_PWD_456",
        }

        export_data = workspace_exchange.build_workspace_export(
            search_manager=_FakeSearchManager(),
            settings_manager=_FakeSettingsManager(settings),
            connection_manager=_FakeConnectionManager(),
            privacy_config={"blacklist": ["geheim"], "whitelist": []},
        )

        assert export_data["schema"] == "profiler-workspace-v1"
        assert export_data["app"]["version"] == "15.0.0"
        # Secrets müssen ausgeschlossen sein
        assert "pdf_master_password_open" not in export_data["settings"]
        assert "pdf_user_password_open" not in export_data["settings"]

        # Export auf Festplatte schreiben und auf BOM prüfen
        payload_bytes = json.dumps(export_data, ensure_ascii=False, indent=2).encode("utf-8")
        export_file.write_bytes(payload_bytes)

        raw_bytes = export_file.read_bytes()
        assert not raw_bytes.startswith(b"\xef\xbb\xbf"), "BOM gefunden!"
        text = raw_bytes.decode("utf-8")
        assert "SUPER_SECRET_PWD_123" not in text
        assert "SECRET_USER_PWD_456" not in text

        # Import-Validierung
        import_mgr = _FakeSettingsManager()
        result = workspace_exchange.import_workspace(
            input_path=str(export_file),
            settings_manager=import_mgr,
            preview_path=str(tmp / "preview.json"),
        )
        assert "ui_language" in result["applied_settings"]
        assert import_mgr.data.get("ui_language") == "es"
        assert "pdf_master_password_open" not in import_mgr.data

    print("  OK  Workspace-Export auf macOS sicher und BOM-frei\n")


def test_macos_sqlite_and_umlaut_roundtrip() -> None:
    """Test 6: SQLite CRUD und Unicode/Umlaut-Verarbeitung auf macOS."""
    print("Test 6: SQLite CRUD und Umlaut-Roundtrip")
    with tempfile.TemporaryDirectory(prefix="profiler-macos-sqlite-") as tmpd:
        db_path = Path(tmpd) / "profiler_index.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE files (id INTEGER PRIMARY KEY, filename TEXT, category TEXT)")
        cursor.execute(
            "INSERT INTO files (filename, category) VALUES (?, ?)",
            ("Prüfbericht_Überweisung_2026.pdf", "Geschäftsdokumente & Verträge"),
        )
        conn.commit()

        cursor.execute("SELECT filename, category FROM files WHERE id=1")
        row = cursor.fetchone()
        assert row == ("Prüfbericht_Überweisung_2026.pdf", "Geschäftsdokumente & Verträge")
        conn.close()

    print("  OK  SQLite & Unicode-Roundtrip erfolgreich\n")


def test_macos_ocr_and_pdf_fallback() -> None:
    """Test 7: Graceful Fallback bei fehlendem Tesseract/Poppler."""
    print("Test 7: OCR / PDF Fallback auf macOS")
    import Profiler_Suite_V15 as profiler

    # Wenn HAS_OCR False ist
    with mock.patch.object(profiler, "HAS_OCR", False):
        try:
            profiler.PDFUtils.apply_ocr_to_pdf("dummy.pdf", "out.pdf")
            assert False, "Exception erwartet"
        except Exception as exc:
            assert "nicht installiert" in str(exc).lower()

    print("  OK  OCR Graceful Fallback verifiziert\n")


def test_macos_tier2_i18n_resolution() -> None:
    """Test 8: Tier-2 Übersetzungssystem auf macOS."""
    print("Test 8: Tier-2 i18n Übersetzungssystem auf macOS")
    ts = translator.TranslationSystem(app_dir=PROJECT_ROOT)
    supported = ts.get_supported_languages()
    for code in ["de", "en", "es", "zh", "ja", "ru"]:
        assert code in supported, f"Sprache {code} fehlt im TranslationSystem"

    with mock.patch.dict(os.environ, {"LANG": "es_ES.UTF-8", "LC_ALL": "es_ES.UTF-8"}):
        ts.set_language("es")
        translated = ts.t("Abbrechen")
        assert translated == "Cancelar", f"Unerwartete Übersetzung: {translated}"

        ts.set_language("zh")
        translated_zh = ts.t("Abbrechen")
        assert translated_zh == "取消", f"Unerwartete Übersetzung: {translated_zh}"

    print("  OK  Tier-2 i18n auf macOS verifiziert\n")


def main() -> int:
    print("=== ProFiler Suite V15 - macOS Platform Smoke ===\n")
    test_macos_app_paths_and_legacy_fallback()
    test_macos_offscreen_window_creation()
    test_macos_file_and_folder_open_dispatch()
    test_macos_sibling_launcher()
    test_macos_workspace_exchange_without_bom_or_secrets()
    test_macos_sqlite_and_umlaut_roundtrip()
    test_macos_ocr_and_pdf_fallback()
    test_macos_tier2_i18n_resolution()
    print("=== ALL macOS PLATFORM SMOKE CHECKS PASSED ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
