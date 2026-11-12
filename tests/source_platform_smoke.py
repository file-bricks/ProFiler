#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Source-level platform smoke tests for ProFiler Suite V15.

Cross-platform smoke tests exercising core contracts without requiring a display
server or hardware dependencies across Windows, Linux, and macOS desktop targets:
1. Supported desktop target (Windows, Linux, Darwin)
2. App paths & sandbox directory resolution
3. Workspace exchange unicode roundtrip (UTF-8, Umlauts, CJK, Cyrillic, without BOM, redacting secrets)
4. SQLite CRUD & unicode/umlaut roundtrip
5. OCR & PDF fallback graceful degradation
6. Tier-2 i18n 6-language resolution (de, en, es, zh, ja, ru)
7. Translation parity check (100% keys present across all 6 languages)
"""

from __future__ import annotations

import json
import os
import platform
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app_paths
import manage_translations
import translator
from version import APP_VERSION
import workspace_exchange


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


def test_supported_desktop_target() -> None:
    """Check 1: Supported desktop operating system and architecture."""
    current_system = platform.system()
    assert current_system in {"Windows", "Linux", "Darwin"}, f"Unsupported platform: {current_system}"
    machine = platform.machine()
    assert machine, "System machine architecture could not be determined"


def test_app_paths_and_sandbox() -> None:
    """Check 2: App paths and configuration directory resolution."""
    with tempfile.TemporaryDirectory(prefix="profiler-smoke-paths-") as tmpd:
        home_path = Path(tmpd)

        # 1. POSIX resolution
        posix_dir = app_paths.app_data_dir(platform="posix", home=home_path)
        assert posix_dir == home_path / ".profiler_suite"
        posix_cfg = app_paths.config_path("test_config.json", platform="posix", home=home_path)
        assert posix_cfg == posix_dir / "test_config.json"

        # 2. Windows resolution
        win_dir = app_paths.app_data_dir(platform="windows", home=home_path)
        assert "ProFilerSuite" in str(win_dir) or "profiler_suite" in str(win_dir).lower()

        # 3. Legacy directory fallback
        legacy_dir = app_paths.legacy_config_dir(home=home_path)
        legacy_dir.mkdir(parents=True, exist_ok=True)
        legacy_cfg = legacy_dir / "fallback_config.json"
        legacy_cfg.write_text('{"fallback": true}', encoding="utf-8")

        resolved = app_paths.resolve_read_path("fallback_config.json", platform="posix", home=home_path)
        assert resolved == legacy_cfg


def test_workspace_exchange_unicode_roundtrip() -> None:
    """Check 3: Workspace exchange unicode roundtrip (UTF-8, CJK, Cyrillic, BOM-free, secrets redacted)."""
    with tempfile.TemporaryDirectory(prefix="profiler-smoke-ws-") as tmpd:
        tmp = Path(tmpd)
        export_file = tmp / "profiler-workspace-smoke.json"

        # Multilingual workspace connection name and settings
        workspace_conn_name = "Verbindung_München_España_北京_東京_Москва"
        settings = {
            "theme": "dark",
            "ui_language": "ru",
            "ocr_language": "deu+eng+spa+chi_sim+jpn+rus",
            "delete_mode": "soft",
            "pdf_master_password_open": "CRITICAL_TOKEN_SECRET_987",
            "pdf_user_password_open": "SECRET_USER_PWD_654",
        }

        export_data = workspace_exchange.build_workspace_export(
            search_manager=_FakeSearchManager(),
            settings_manager=_FakeSettingsManager(settings),
            connection_manager=_FakeConnectionManager([{"name": workspace_conn_name, "enabled": True}]),
            privacy_config={"blacklist": ["vertraulich", "geheim", "Prüfung_äöü"], "whitelist": ["Öffentlich_公开_公開_Публичный"]},
        )

        assert export_data["schema"] == "profiler-workspace-v1"
        assert export_data["app"]["version"] == APP_VERSION
        assert export_data["workspace"]["name"] == workspace_conn_name
        assert export_data["settings"]["ui_language"] == "ru"
        assert export_data["settings"]["ocr_languages"] == ["deu+eng+spa+chi_sim+jpn+rus"]

        # Passwords must be completely omitted
        assert "pdf_master_password_open" not in export_data["settings"]
        assert "pdf_user_password_open" not in export_data["settings"]

        payload_bytes = json.dumps(export_data, ensure_ascii=False, indent=2).encode("utf-8")
        export_file.write_bytes(payload_bytes)

        # Check BOM-free
        raw_bytes = export_file.read_bytes()
        assert not raw_bytes.startswith(b"\xef\xbb\xbf"), "BOM detected in workspace exchange file!"
        decoded_text = raw_bytes.decode("utf-8")
        assert workspace_conn_name in decoded_text
        assert "CRITICAL_TOKEN_SECRET_987" not in decoded_text

        # Check roundtrip import
        import_mgr = _FakeSettingsManager()
        result = workspace_exchange.import_workspace(
            input_path=str(export_file),
            settings_manager=import_mgr,
            preview_path=str(tmp / "preview.json"),
        )
        assert "ui_language" in result["applied_settings"]
        assert import_mgr.data.get("ui_language") == "ru"
        assert "pdf_master_password_open" not in import_mgr.data


def test_sqlite_and_umlaut_roundtrip() -> None:
    """Check 4: SQLite in-memory and temp storage with unicode and umlaut roundtrip."""
    with tempfile.TemporaryDirectory(prefix="profiler-smoke-sqlite-") as tmpd:
        db_path = Path(tmpd) / "profiler_smoke.db"
        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE files (id INTEGER PRIMARY KEY, filename TEXT, category TEXT, note TEXT)")
            entries = [
                ("Jahresabrechnung_München_2026.pdf", "Finanzen & Steuern", "Überprüfung nötig"),
                ("Informe_España_Madrid.pdf", "Documentación", "Revisión completada"),
                ("财务报告_2026.pdf", "财务分类", "年度分析报告"),
                ("年次報告書_東京_2026.pdf", "財務データ", "確認完了"),
                ("Финансовый_Отчёт_2026.pdf", "Налоги и финансы", "Проверка завершена"),
            ]
            cursor.executemany(
                "INSERT INTO files (filename, category, note) VALUES (?, ?, ?)",
                entries,
            )
            conn.commit()

            cursor.execute("SELECT filename, category, note FROM files ORDER BY id ASC")
            rows = cursor.fetchall()
            assert len(rows) == 5
            assert rows[0] == entries[0]
            assert rows[1] == entries[1]
            assert rows[2] == entries[2]
            assert rows[3] == entries[3]
            assert rows[4] == entries[4]
        finally:
            conn.close()


def test_ocr_and_pdf_fallback() -> None:
    """Check 5: Graceful fallback when OCR or PDF dependencies are unavailable."""
    import Profiler_Suite_V15 as profiler

    with mock.patch.object(profiler, "HAS_OCR", False):
        try:
            profiler.PDFUtils.apply_ocr_to_pdf("sample.pdf", "output.pdf")
            raise AssertionError("Expected exception when HAS_OCR is False")
        except Exception as exc:
            assert "nicht installiert" in str(exc).lower() or "not installed" in str(exc).lower()


def test_tier2_i18n_resolution() -> None:
    """Check 6: Tier-2 6-language resolution (de, en, es, zh, ja, ru)."""
    ts = translator.TranslationSystem(app_dir=PROJECT_ROOT)
    supported = ts.get_supported_languages()
    expected = ("de", "en", "es", "zh", "ja", "ru")
    for lang in expected:
        assert lang in supported, f"Language '{lang}' missing from supported languages: {supported}"

    translations = {
        "de": ("Abbrechen", "Abbrechen"),
        "en": ("Abbrechen", "Cancel"),
        "es": ("Abbrechen", "Cancelar"),
        "zh": ("Abbrechen", "取消"),
        "ja": ("Abbrechen", "キャンセル"),
        "ru": ("Abbrechen", "Отмена"),
    }

    for lang, (key, expected_val) in translations.items():
        ts.set_language(lang)
        actual = ts.t(key)
        assert actual == expected_val, f"Translation for '{key}' in '{lang}' was '{actual}', expected '{expected_val}'"


def test_translation_parity_check() -> None:
    """Check 7: Translation parity check across all 6 languages."""
    result = manage_translations.check_translations()
    assert result == 0, f"check_translations() returned non-zero code {result}"


def main() -> int:
    """Run all 7 checks standalone."""
    print("=================================================================")
    print("  ProFiler Suite - Source Platform Smoke Suite")
    print("=================================================================")
    tests = [
        ("Check 1: Supported desktop target", test_supported_desktop_target),
        ("Check 2: App paths & sandbox resolution", test_app_paths_and_sandbox),
        ("Check 3: Workspace exchange unicode roundtrip", test_workspace_exchange_unicode_roundtrip),
        ("Check 4: SQLite CRUD & unicode roundtrip", test_sqlite_and_umlaut_roundtrip),
        ("Check 5: OCR & PDF fallback graceful degradation", test_ocr_and_pdf_fallback),
        ("Check 6: Tier-2 i18n 6-language resolution", test_tier2_i18n_resolution),
        ("Check 7: Translation parity check", test_translation_parity_check),
    ]

    for title, test_fn in tests:
        print(f"Running {title} ...", end=" ", flush=True)
        test_fn()
        print("[OK]")

    print("=================================================================")
    print("  ALL 7 SOURCE PLATFORM SMOKE CHECKS PASSED")
    print("=================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
