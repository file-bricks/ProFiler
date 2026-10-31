"""
manage_translations.py - Multi-Language Translation Manager & CI Gate
======================================================================
Policy P-006: Tier-2 Multi-Language Standard (DE, EN, ES, ZH, JA, RU)

Verwendung:
    python manage_translations.py [--check] [--dir PROJEKTVERZEICHNIS]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
SUPPORTED_LANGUAGES = ("de", "en", "es", "zh", "ja", "ru")
TRANSLATION_FILE = "locales/translations.json"


def _ensure_utf8_streams() -> None:
    """Sichert UTF-8-Stream-Encoding für stdout und stderr unter Windows."""
    for stream in (sys.stdout, sys.stderr):
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError, AttributeError):
                pass


STRING_PATTERNS = [
    re.compile(r'text\s*=\s*"([^"\n]+)"'),
    re.compile(r'setText\s*\(\s*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'setWindowTitle\s*\(\s*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'QLabel\s*\(\s*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'QPushButton\s*\(\s*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'addAction\s*\([^,\n]*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'addTab\s*\([^,\n]+,\s*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'setToolTip\s*\(\s*["\']([^"\'\n]+)["\']\s*\)'),
    re.compile(r'setPlaceholderText\s*\(\s*["\']([^"\'\n]+)["\']\s*\)'),
]

GERMAN_HINTS = [
    "datei", "filter", "fehler", "laden", "speichern",
    "ansicht", "optionen", "zurueck", "anzeigen", "export",
    "import", "einstellungen", "abbrechen", "hilfe", "bearbeiten",
    "oeffnen", "schliessen", "start", "aktualisieren",
    "pruefen", "sicherheit", "dokument", "ordner", "ueber",
    "daten", "bericht", "auswahl", "profil", "suche",
]


def is_german(text: str) -> bool:
    if any(ch in text for ch in "äöüÄÖÜß"):
        return True
    text_lower = text.lower()
    return any(w in text_lower for w in GERMAN_HINTS)


def find_german_strings(source_dir: str | Path | None = None) -> set[str]:
    if source_dir is None:
        source_dir = str(APP_DIR)
    else:
        source_dir = str(source_dir)
    german_strings: set[str] = set()
    skip_dirs = {
        "build",
        "dist",
        "venv",
        ".venv",
        "__pycache__",
        "releases",
        "scratch",
        "tests",
        "scripts",
        "flutter_port",
        "web_companion",
        ".git",
        ".pytest_temp",
    }
    skip_files = {
        "run_tests.py",
        "manage_translations.py",
        "translator.py",
        "source_platform_smoke.py",
        "indent_gui_checker.py",
    }

    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for file in files:
            if file.endswith(".py") and not file.startswith("test_") and file not in skip_files:
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception:
                    continue
                for pattern in STRING_PATTERNS:
                    for match in pattern.findall(content):
                        if is_german(match):
                            german_strings.add(match.strip())
    return german_strings


def new_translation_entry(de: str, en: str = "") -> dict[str, str]:
    entry = {language: "" for language in SUPPORTED_LANGUAGES}
    entry.update({"de": de, "en": en})
    return entry


def _atomic_write_json(file_path: str, data: dict) -> None:
    dirname = os.path.dirname(file_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    temp_path = f"{file_path}.tmp.{os.getpid()}"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        if os.path.exists(file_path):
            try:
                os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
            except (OSError, PermissionError):
                pass
        os.replace(temp_path, file_path)
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        raise


def check_translations(source_dir: str | Path | None = None) -> int:
    """CI Check: Überprüft Vollständigkeit aller 6 Zielsprachen in translations.json."""
    _ensure_utf8_streams()
    if source_dir is None:
        source_dir = str(APP_DIR)
    else:
        source_dir = str(source_dir)
    trans_file = os.path.join(source_dir, TRANSLATION_FILE)
    if not os.path.exists(trans_file):
        print(f"[FAIL] Übersetzungsdatei {trans_file} existiert nicht!")
        return 1

    try:
        with open(trans_file, "r", encoding="utf-8") as f:
            translations = json.load(f)
    except (json.JSONDecodeError, OSError, Exception) as e:
        print(f"[FAIL] Fehler beim Parsen von {trans_file}: {e}")
        return 1

    total_keys = 0
    missing_by_lang: dict[str, list[str]] = {lang: [] for lang in SUPPORTED_LANGUAGES}

    for key, val in translations.items():
        if key.startswith("_"):
            continue
        total_keys += 1
        if not isinstance(val, dict):
            for lang in SUPPORTED_LANGUAGES:
                missing_by_lang[lang].append(key)
            continue
        for lang in SUPPORTED_LANGUAGES:
            target_val = val.get(lang)
            if key == "viewer_empty":
                if target_val is None or not isinstance(target_val, str):
                    missing_by_lang[lang].append(key)
            else:
                if not target_val or not str(target_val).strip():
                    missing_by_lang[lang].append(key)

    if total_keys == 0:
        print(f"[FAIL] Keine Übersetzungsschlüssel in {trans_file} gefunden!")
        return 1

    has_error = False
    for lang, missing in missing_by_lang.items():
        if missing:
            has_error = True
            print(f"[!] {len(missing)}/{total_keys} fehlende Übersetzungen für Sprache '{lang}':")
            for k in missing[:5]:
                print(f"    - {k}")
            if len(missing) > 5:
                print(f"    ... und {len(missing) - 5} weitere")

    if has_error:
        print("\n[FAIL] Übersetzungsprüfung fehlgeschlagen. Nicht alle Schlüssel vollständig übersetzt.")
        return 1

    print(
        f"[OK] 100% Übersetzungsparität: Alle {total_keys} Schlüssel in allen 6 Sprachen vorhanden ({', '.join(SUPPORTED_LANGUAGES)})."
    )
    return 0


def manage_translations(source_dir: str | Path | None = None) -> None:
    _ensure_utf8_streams()
    if source_dir is None:
        source_dir = str(APP_DIR)
    else:
        source_dir = str(source_dir)
    trans_file = os.path.join(source_dir, TRANSLATION_FILE)

    if os.path.exists(trans_file):
        try:
            with open(trans_file, "r", encoding="utf-8") as f:
                translations = json.load(f)
        except (json.JSONDecodeError, OSError):
            translations = {}
    else:
        translations = {}

    found = find_german_strings(source_dir)

    added: list[str] = []
    upgraded: list[str] = []
    for s in sorted(found):
        if s not in translations:
            translations[s] = {lang: (s if lang == "de" else "") for lang in SUPPORTED_LANGUAGES}
            added.append(s)
        else:
            for lang in SUPPORTED_LANGUAGES:
                if lang not in translations[s]:
                    translations[s][lang] = ""
                    if s not in upgraded:
                        upgraded.append(s)

    _atomic_write_json(trans_file, translations)

    if added:
        print(f"[+] {len(added)} neue Einträge hinzugefügt:")
        for s in added[:10]:
            print(f"    - {s}")
        if len(added) > 10:
            print(f"    ... und {len(added) - 10} weitere")
    else:
        print("[i] Keine neuen deutschen Strings gefunden.")

    if upgraded:
        print(f"[+] {len(upgraded)} bestehende Einträge um neue Sprach-Slots erweitert")

    total_keys = len([k for k in translations if not k.startswith("_")])
    print(f"\n[i] Gesamt: {total_keys} Übersetzungsschlüssel in {trans_file}")
    print(f"[i] Sprachen: {', '.join(SUPPORTED_LANGUAGES)}")


def main() -> int:
    _ensure_utf8_streams()
    parser = argparse.ArgumentParser(description="ProFiler Translation Manager (Policy P-006 Tier-2)")
    parser.add_argument("--check", action="store_true", help="Validiert 100%% Sprachabdeckung aller 6 Zielsprachen")
    parser.add_argument("--dir", default=str(APP_DIR), help="Wurzelverzeichnis des Projekts (Default: Skriptpfad)")
    args, _ = parser.parse_known_args()

    if args.check:
        return check_translations(args.dir)
    manage_translations(args.dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
