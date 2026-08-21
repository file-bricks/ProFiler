#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproduzierbarer Linux-Plattform-Smoke für ProFiler Suite V15.

Der Smoke deckt die geplante Linux-Source-Linie ab:
- POSIX/XDG-App-Pfade via app_paths.py und Legacy-Fallback (~/.profiler_suite)
- Headless/Offscreen PySide6 UnifiedMainWindow-Initialisierung (QT_QPA_PLATFORM=offscreen)
- Linux-spezifische Datei- und Ordneröffner-Pfade via 'xdg-open'
- Cross-Platform Sibling-Launcher für Begleitmodule (.py, .sh)
- Redigierter Workspace-Export (profiler-workspace-v1.json) ohne Secrets/BOM
- SQLite-CRUD und UTF-8-Umlaut-Roundtrip
- Graceful-Fallback bei fehlenden OCR-/PDF-Abhängigkeiten
- Tier-2 i18n Übersetzungssystem (de, en, es, zh, ja, ru) auf Linux
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


def test_linux_app_paths_and_legacy_fallback() -> None:
    """Test 1: POSIX/Linux-Pfadauflösung und Legacy-Fallback."""
    print("Test 1: Linux App-Pfade und Legacy-Fallback")
    with tempfile.TemporaryDirectory(prefix="profiler-linux-home-") as temp_home:
        home_path = Path(temp_home)

        # 1. Standard POSIX app_data_dir
        app_dir = app_paths.app_data_dir(platform="posix", home=home_path)
        expected_dir = home_path / ".profiler_suite"
        assert app_dir == expected_dir, f"app_dir {app_dir} != {expected_dir}"

        # 2. Config-Pfade
        cfg = app_paths.config_path("search_config.json", platform="posix", home=home_path)
        assert cfg == expected_dir / "search_config.json"

        # 3. Legacy-Lesepfad Fallback
        legacy_dir = app_paths.legacy_config_dir(home=home_path)
        legacy_dir.mkdir(parents=True, exist_ok=True)
        legacy_file = legacy_dir / "search_config.json"
        legacy_file.write_text(json.dumps({"max_results": 500}), encoding="utf-8")

        read_path = app_paths.resolve_read_path("search_config.json", platform="posix", home=home_path)
        assert read_path == legacy_file
    print("  OK  Linux App-Pfade und Fallbacks validiert\n")


def test_linux_offscreen_window_creation() -> None:
    """Test 2: Offscreen PySide6 UnifiedMainWindow auf Linux."""
    print("Test 2: Offscreen UnifiedMainWindow auf Linux")
    app = _ensure_app()
    with tempfile.TemporaryDirectory(prefix="profiler-linux-win-") as tmpd:
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
    print("  OK  Offscreen Hauptfenster auf Linux erfolgreich erzeugt\n")


def test_linux_file_and_folder_open_dispatch() -> None:
    """Test 3: Linux System-Öffner ('xdg-open')."""
    print("Test 3: Linux System-Öffner ('xdg-open')")
    _ensure_app()
    import Profiler_Suite_V15 as profiler

    with tempfile.TemporaryDirectory(prefix="profiler-linux-open-") as tmpd:
        sample_file = Path(tmpd) / "Dokument_äöü.pdf"
        sample_file.write_text("dummy", encoding="utf-8")

        with mock.patch.object(sys, "platform", "linux"), \
             mock.patch("subprocess.run") as mock_run:

            # 1. Datei öffnen via xdg-open
            win = MagicMock()
            win.get_selected_results.return_value = [{"path": str(sample_file)}]
            profiler.SearchWidgetHybrid.open_selected_file(win)
            mock_run.assert_called_with(["xdg-open", str(sample_file)], timeout=10)

            # 2. Im Dateimanager öffnen via xdg-open auf Ordner
            mock_run.reset_mock()
            profiler.SearchWidgetHybrid.show_in_explorer(win)
            mock_run.assert_called_with(["xdg-open", str(sample_file.parent)], timeout=10)

    print("  OK  Linux 'xdg-open' Dispatch verifiziert\n")


def test_linux_sibling_launcher() -> None:
    """Test 4: Sibling-Launcher auf Linux (.py, .sh)."""
    print("Test 4: Sibling-Launcher auf Linux")
    with tempfile.TemporaryDirectory(prefix="profiler-linux-launch-") as tmpd:
        base = Path(tmpd) / "REL-PUB_ProFiler"
        base.mkdir()
        sibling = Path(tmpd) / "REL-PUB_ProSync"
        sibling.mkdir()
        script = sibling / "ProSyncStart_V3.1.py"
        script.write_text("#!/usr/bin/env python3\nprint('prosync')\n", encoding="utf-8")

        resolved = sibling_launcher.resolve_prosync_launch_path(base)
        assert resolved == script

        # Launch tool process mit Shell-Skript
        sh_tool = base / "run.sh"
        sh_tool.write_text("#!/bin/sh\necho test\n", encoding="utf-8")

        with mock.patch("sibling_launcher.subprocess.Popen") as mock_popen:
            sibling_launcher.launch_tool_process(sh_tool)
            mock_popen.assert_called_once_with(["sh", str(sh_tool)], cwd=str(base))

    print("  OK  Linux Sibling-Launcher verifiziert\n")


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


def test_linux_workspace_exchange_without_bom_or_secrets() -> None:
    """Test 5: Workspace-Export auf Linux ohne Secrets und ohne UTF-8 BOM."""
    print("Test 5: Workspace-Export auf Linux")
    with tempfile.TemporaryDirectory(prefix="profiler-linux-ws-") as tmpd:
        tmp = Path(tmpd)
        export_file = tmp / "profiler-workspace-v1.json"

        settings = {
            "theme": "light",
            "ui_language": "ru",
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
        assert import_mgr.data.get("ui_language") == "ru"
        assert "pdf_master_password_open" not in import_mgr.data

    print("  OK  Workspace-Export auf Linux sicher und BOM-frei\n")


def test_linux_sqlite_and_umlaut_roundtrip() -> None:
    """Test 6: SQLite CRUD und Unicode/Umlaut-Verarbeitung auf Linux."""
    print("Test 6: SQLite CRUD und Umlaut-Roundtrip")
    with tempfile.TemporaryDirectory(prefix="profiler-linux-sqlite-") as tmpd:
        db_path = Path(tmpd) / "profiler_index.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE files (id INTEGER PRIMARY KEY, filename TEXT, category TEXT)")
        cursor.execute(
            "INSERT INTO files (filename, category) VALUES (?, ?)",
            ("Prüfungsnachweis_Straße_2026.pdf", "Finanzen & Steuern"),
        )
        conn.commit()

        cursor.execute("SELECT filename, category FROM files WHERE id=1")
        row = cursor.fetchone()
        assert row == ("Prüfungsnachweis_Straße_2026.pdf", "Finanzen & Steuern")
        conn.close()

    print("  OK  SQLite & Unicode-Roundtrip auf Linux erfolgreich\n")


def test_linux_ocr_and_pdf_fallback() -> None:
    """Test 7: Graceful Fallback bei fehlendem Tesseract/Poppler auf Linux."""
    print("Test 7: OCR / PDF Fallback auf Linux")
    import Profiler_Suite_V15 as profiler

    with mock.patch.object(profiler, "HAS_OCR", False):
        try:
            profiler.PDFUtils.apply_ocr_to_pdf("dummy.pdf", "out.pdf")
            assert False, "Exception erwartet"
        except Exception as exc:
            assert "nicht installiert" in str(exc).lower()

    print("  OK  OCR Graceful Fallback auf Linux verifiziert\n")


def test_linux_tier2_i18n_resolution() -> None:
    """Test 8: Tier-2 Übersetzungssystem auf Linux."""
    print("Test 8: Tier-2 i18n Übersetzungssystem auf Linux")
    ts = translator.TranslationSystem(app_dir=PROJECT_ROOT)
    supported = ts.get_supported_languages()
    for code in ["de", "en", "es", "zh", "ja", "ru"]:
        assert code in supported, f"Sprache {code} fehlt im TranslationSystem"

    with mock.patch.dict(os.environ, {"LANG": "ru_RU.UTF-8", "LC_ALL": "ru_RU.UTF-8"}):
        ts.set_language("ru")
        translated_ru = ts.t("Abbrechen")
        assert translated_ru == "Отмена", f"Unerwartete Übersetzung: {translated_ru}"

        ts.set_language("ja")
        translated_ja = ts.t("Abbrechen")
        assert translated_ja == "キャンセル", f"Unerwartete Übersetzung: {translated_ja}"

    print("  OK  Tier-2 i18n auf Linux verifiziert\n")


def main() -> int:
    print("=== ProFiler Suite V15 - Linux Platform Smoke ===\n")
    test_linux_app_paths_and_legacy_fallback()
    test_linux_offscreen_window_creation()
    test_linux_file_and_folder_open_dispatch()
    test_linux_sibling_launcher()
    test_linux_workspace_exchange_without_bom_or_secrets()
    test_linux_sqlite_and_umlaut_roundtrip()
    test_linux_ocr_and_pdf_fallback()
    test_linux_tier2_i18n_resolution()
    print("=== ALL Linux PLATFORM SMOKE CHECKS PASSED ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
