"""Hermetic contract and regression tests for manage_translations.py CLI and TranslationSystem."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import manage_translations
from translator import TranslationSystem

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_manage_translations_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["manage_translations.py", "--help"])
    with pytest.raises(SystemExit) as exc:
        manage_translations.main()
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "--check" in captured.out
    assert "--dir" in captured.out


def test_manage_translations_check_flag_exits_cleanly(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["manage_translations.py", "--check"])
    exit_code = manage_translations.main()
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "100%" in captured.out
    assert "966" in captured.out


def test_manage_translations_check_flag_does_not_create_phantom_directory(tmp_path, monkeypatch):
    phantom_dir = tmp_path / "--check"
    monkeypatch.setattr(
        sys, "argv", ["manage_translations.py", "--check", "--dir", str(tmp_path)]
    )
    manage_translations.main()
    assert not phantom_dir.exists()


def test_check_translations_detects_missing_keys(tmp_path):
    locales_dir = tmp_path / "locales"
    locales_dir.mkdir(parents=True)
    catalog = {
        "_meta": {"version": "1.0"},
        "viewer_empty": {"de": "", "en": "", "es": "", "zh": "", "ja": "", "ru": ""},
        "sample_key": {
            "de": "Datei",
            "en": "File",
            "es": "Archivo",
            "zh": "",  # missing in zh
            "ja": "ファイル",
            "ru": "Файл",
        },
    }
    (locales_dir / "translations.json").write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")

    exit_code = manage_translations.check_translations(str(tmp_path))
    assert exit_code == 1


def test_check_translations_passes_with_viewer_empty_and_full_parity(tmp_path):
    locales_dir = tmp_path / "locales"
    locales_dir.mkdir(parents=True)
    catalog = {
        "_meta": {"version": "1.0"},
        "viewer_empty": {"de": "", "en": "", "es": "", "zh": "", "ja": "", "ru": ""},
        "sample_key": {
            "de": "Datei",
            "en": "File",
            "es": "Archivo",
            "zh": "文件",
            "ja": "ファイル",
            "ru": "Файл",
        },
    }
    (locales_dir / "translations.json").write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")

    exit_code = manage_translations.check_translations(str(tmp_path))
    assert exit_code == 0


def test_find_german_strings_excludes_tests_and_helpers(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "source_platform_smoke.py").write_text(
        'sample = "# Überschrift\\n\\nÄpfel, Öl, Übergabe."', encoding="utf-8"
    )
    (tests_dir / "test_sample.py").write_text('text = "Fehler im Test"', encoding="utf-8")

    src_file = tmp_path / "gui_widget.py"
    src_file.write_text('btn = QPushButton("Datei öffnen")', encoding="utf-8")

    found = manage_translations.find_german_strings(str(tmp_path))
    assert "Datei öffnen" in found
    assert not any("Äpfel" in s for s in found)
    assert not any("Fehler im Test" in s for s in found)


def test_atomic_write_json_creates_clean_file(tmp_path):
    target = tmp_path / "locales" / "translations.json"
    data = {"hello": {"de": "Hallo", "en": "Hello"}}
    manage_translations._atomic_write_json(str(target), data)

    assert target.exists()
    loaded = json.loads(target.read_text(encoding="utf-8"))
    assert loaded == data
    tmp_files = list(tmp_path.glob("**/*.tmp*"))
    assert tmp_files == []


def test_ensure_utf8_streams_safe_execution():
    manage_translations._ensure_utf8_streams()


def test_translator_find_german_strings_excludes_tests_and_helpers(tmp_path):
    ts = TranslationSystem("de", app_dir=tmp_path)
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "source_platform_smoke.py").write_text(
        'sample = "# Überschrift\\n\\nÄpfel, Öl, Übergabe."', encoding="utf-8"
    )
    (tmp_path / "component.py").write_text('lbl = QLabel("Einstellungen")', encoding="utf-8")

    found = ts._find_german_strings(tmp_path)
    assert "Einstellungen" in found
    assert not any("Äpfel" in s for s in found)


def test_translator_save_translations_atomic(tmp_path):
    ts = TranslationSystem("de", app_dir=tmp_path)
    ts.translations = {"Test": {"de": "Test", "en": "Test", "es": "", "zh": "", "ja": "", "ru": ""}}
    ts._save_translations()

    trans_file = tmp_path / "locales" / "translations.json"
    assert trans_file.exists()
    loaded = json.loads(trans_file.read_text(encoding="utf-8"))
    assert loaded["Test"]["de"] == "Test"
    tmp_files = list(tmp_path.glob("**/*.tmp*"))
    assert tmp_files == []
