"""
TranslationSystem - Multi-Language Support fuer Anwendungen
============================================================
Version: 2.0.0 (isoliert aus _LANG)
Quelle: ARC_EntwicklungsschleifeAdvanced/TranslationSystem.py v2.4

Verwendung:
-----------
from translator import TranslationSystem

translator = TranslationSystem('de')
label.setText(translator.t('Datei oeffnen'))
translator.set_language('en')
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set


class TranslationSystem:
    """Multi-Language Support System v2.0 with deterministic fallbacks."""

    SUPPORTED_LANGUAGES = ("de", "en", "es", "zh", "ja", "ru")
    FALLBACK_LANGUAGES = ("en", "de")

    def __init__(self, default_lang: str = 'de', app_dir: Path = None):
        """
        Initialisiert Translation-System.

        Args:
            default_lang: Standard-Sprache (eine unterstützte Sprache)
            app_dir: Verzeichnis der Anwendung (default: aktuelles Verzeichnis)
        """
        self.current_lang = default_lang if default_lang in self.SUPPORTED_LANGUAGES else "de"

        if app_dir is None:
            app_dir = Path(__file__).parent
        self.app_dir = Path(app_dir)

        self.translations_file = self.app_dir / "locales" / "translations.json"

        self.string_patterns = [
            re.compile(r'setText\s*\(\s*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'setWindowTitle\s*\(\s*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'QLabel\s*\(\s*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'QPushButton\s*\(\s*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'addAction\s*\([^,]*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'addTab\s*\([^,]+,\s*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'text\s*=\s*"([^"]+)"'),
        ]

        self.german_hints = [
            "datei", "bearbeiten", "ansicht", "hilfe", "oeffnen", "speichern",
            "schliessen", "einstellungen", "abbrechen", "ok", "ja", "nein",
            "start", "stop", "pause", "fortsetzen", "laden", "aktualisieren",
            "filter", "fehler", "export", "import", "optionen", "anzeigen",
        ]

        self.translations = {}
        self._load_translations()

    def _load_translations(self):
        if self.translations_file.exists():
            try:
                with open(self.translations_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
            except Exception:
                self.translations = {}
        else:
            self.translations = {}

    def _save_translations(self):
        self.translations_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.translations_file, 'w', encoding='utf-8') as f:
            json.dump(self.translations, f, indent=2, ensure_ascii=False)

    def t(self, key: str) -> str:
        """
        Uebersetzt einen Key in die aktuelle Sprache.

        Args:
            key: Translation-Key (oft der deutsche Originaltext)

        Returns:
            Uebersetzter Text oder Key als Fallback
        """
        entry = self.translations.get(key)
        if isinstance(entry, dict):
            for language in (self.current_lang, *self.FALLBACK_LANGUAGES):
                value = entry.get(language)
                if isinstance(value, str) and value:
                    return value

        if self._is_german(key):
            self.translations[key] = self._new_translation_entry(key, "")
            self._save_translations()

        return key

    def set_language(self, lang: str):
        if lang in self.SUPPORTED_LANGUAGES:
            self.current_lang = lang

    @classmethod
    def get_supported_languages(cls) -> List[str]:
        """Return the supported language codes without exposing mutable state."""
        return list(cls.SUPPORTED_LANGUAGES)

    def get_language(self) -> str:
        return self.current_lang

    def add_translation(self, key: str, de: str, en: str):
        self.translations[key] = self._new_translation_entry(de, en)
        self._save_translations()

    def scan_and_update(self, project_dir: Path = None) -> Dict:
        """Scannt Projekt-Dateien nach deutschen Strings und aktualisiert translations.json."""
        if project_dir is None:
            project_dir = self.app_dir

        found_strings = self._find_german_strings(project_dir)

        added = []
        for string in sorted(found_strings):
            if string not in self.translations:
                self.translations[string] = self._new_translation_entry(string, "")
                added.append(string)

        if added:
            self._save_translations()

        missing = [k for k, v in self.translations.items() if not v.get("en")]

        return {'added': added, 'missing': missing, 'total': len(self.translations)}

    def _find_german_strings(self, directory: Path) -> Set[str]:
        german_strings = set()
        skip_dirs = {'build', 'dist', 'venv', '.venv', '__pycache__', 'releases'}

        for py_file in directory.rglob("*.py"):
            if any(folder in py_file.parts for folder in skip_dirs):
                continue
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                continue

            for pattern in self.string_patterns:
                for match in pattern.findall(content):
                    if match and self._is_german(match):
                        german_strings.add(match.strip())

        return german_strings

    def _is_german(self, text: str) -> bool:
        if any(ch in text for ch in "äöüÄÖÜß"):
            return True
        text_lower = text.lower()
        return any(hint in text_lower for hint in self.german_hints)

    def get_missing_translations(self, language: str = "en") -> List[str]:
        """Return entries missing a reviewed value for one supported language."""
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")
        return [key for key, value in self.translations.items() if not value.get(language)]

    @classmethod
    def _new_translation_entry(cls, de: str, en: str) -> Dict[str, str]:
        """Create a complete language schema while leaving translations for review."""
        entry = {language: "" for language in cls.SUPPORTED_LANGUAGES}
        entry.update({"de": de, "en": en})
        return entry


if __name__ == "__main__":
    tr = TranslationSystem('de')
    print(f"Sprache: {tr.get_language()}")
    result = tr.scan_and_update()
    print(f"Scan: {result['total']} Strings, {len(result['added'])} neu, {len(result['missing'])} ohne EN")
