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
import weakref
from pathlib import Path
from typing import Dict, List, Set



class TranslationSystem:
    """Multi-Language Support System v2.0 with deterministic fallbacks."""

    SUPPORTED_LANGUAGES = ("de", "en", "es", "zh", "ja", "ru")
    FALLBACK_LANGUAGES = ("en", "de")
    LANGUAGE_NAMES = {
        "de": "Deutsch",
        "en": "English",
        "es": "Español",
        "zh": "简体中文",
        "ja": "日本語",
        "ru": "Русский",
    }
    LANGUAGE_DISPLAY_NAMES = {
        "de": "Deutsch (de)",
        "en": "English (en)",
        "es": "Español (es)",
        "zh": "简体中文 (zh)",
        "ja": "日本語 (ja)",
        "ru": "Русский (ru)",
    }

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

    def translate_ui(self, key: str, **format_values) -> str:
        """Read-only UI lookup with named formatting values and locale fallback.

        Unlike t(), this method never inserts or saves missing catalog keys,
        so rendering the interface cannot mutate the user's translation catalog.
        """
        entry = self.translations.get(key)
        template = key
        if isinstance(entry, dict):
            for language in (self.current_lang, *self.FALLBACK_LANGUAGES):
                value = entry.get(language)
                if isinstance(value, str) and value:
                    template = value
                    break

        if not format_values:
            return template

        class _MissingTemplateValues(dict):
            def __missing__(self, name):
                return "{" + name + "}"

        try:
            return template.format_map(_MissingTemplateValues(format_values))
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            return template

    def set_language(self, lang: str):
        if lang in self.SUPPORTED_LANGUAGES:
            self.current_lang = lang

    @classmethod
    def get_supported_languages(cls) -> List[str]:
        """Return the supported language codes without exposing mutable state."""
        return list(cls.SUPPORTED_LANGUAGES)

    @classmethod
    def get_language_names(cls) -> Dict[str, str]:
        """Return a mapping of language codes to native language names."""
        return dict(cls.LANGUAGE_NAMES)

    @classmethod
    def get_language_display_names(cls) -> Dict[str, str]:
        """Return a mapping of language codes to display strings."""
        return dict(cls.LANGUAGE_DISPLAY_NAMES)

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


def set_application_translator(app, translator: TranslationSystem) -> None:
    """Set the per-process UI translator and initialize explicit text bindings."""
    app._profiler_ui_translator = translator
    if not hasattr(app, "_profiler_ui_text_bindings"):
        app._profiler_ui_text_bindings = []


def load_translator_from_settings(settings_path=None, app_dir=None):
    """Load a translator using the persisted locale without writing settings."""
    if settings_path is None:
        try:
            from app_paths import resolve_read_path
            settings_path = resolve_read_path("profiler_settings.json")
        except ImportError:
            settings_path = None

    language = "de"
    if settings_path is not None:
        try:
            settings = json.loads(Path(settings_path).read_text(encoding="utf-8"))
            candidate = settings.get("ui_language", settings.get("language", "de"))
            if candidate in TranslationSystem.SUPPORTED_LANGUAGES:
                language = candidate
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            pass

    return TranslationSystem(language, app_dir=app_dir)


def install_translator_from_settings(app, settings_path=None, app_dir=None):
    """Install a translator using the persisted locale without writing settings."""
    translator = load_translator_from_settings(settings_path, app_dir=app_dir)
    set_application_translator(app, translator)
    return translator


def _render_for_app(app, key: str, format_values: Dict[str, object]) -> str:
    translator = getattr(app, "_profiler_ui_translator", None) if app else None
    if translator is not None:
        return translator.translate_ui(key, **format_values)
    if not format_values:
        return key

    class _MissingValues(dict):
        def __missing__(self, name):
            return "{" + name + "}"

    try:
        return key.format_map(_MissingValues(format_values))
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return key


def bind_ui_text(
    widget,
    key: str,
    setter: str = "setText",
    *,
    setter_args=(),
    format_values=None,
) -> str:
    """Set and remember one explicitly bound UI string for locale changes.

    Only call this for application-owned UI copy. User data and machine values
    should be set directly and therefore never enter this binding registry.
    """
    app = widget if hasattr(widget, "_profiler_ui_translator") else None
    if app is None:
        try:
            from PySide6.QtWidgets import QApplication
            app = QApplication.instance()
        except ImportError:
            app = None

    values = dict(format_values or {})
    text = _render_for_app(app, key, values)
    if app is not None:
        if not hasattr(app, "_profiler_ui_text_bindings"):
            app._profiler_ui_text_bindings = []
        registry = app._profiler_ui_text_bindings
        for record in registry:
            if record[0]() is widget:
                record[1][(setter, tuple(setter_args))] = (key, values, text)
                break
        else:
            try:
                reference = weakref.ref(widget)
            except TypeError:
                reference = lambda: None
            registry.append((reference, {(setter, tuple(setter_args)): (key, values, text)}))

    try:
        method = getattr(widget, setter)
        if setter == "setTabText":
            method(*tuple(setter_args), text)
        else:
            method(text, *tuple(setter_args))
    except (AttributeError, RuntimeError, TypeError):
        return text
    return text


def create_ui_widget(
    widget_type,
    key: str,
    *args,
    setter: str = "setText",
    setter_args=(),
    format_values=None,
    **kwargs,
):
    """Construct a widget whose first argument is explicitly translatable text."""
    values = dict(format_values or {})
    widget = widget_type(_render_for_app(_application_instance(), key, values), *args, **kwargs)
    bind_ui_text(widget, key, setter, setter_args=setter_args, format_values=values)
    return widget


def _application_instance():
    try:
        from PySide6.QtWidgets import QApplication
        return QApplication.instance()
    except ImportError:
        return None


def retranslate_registered_ui(app) -> None:
    """Reapply only explicitly registered UI copy in the current locale."""
    registry = getattr(app, "_profiler_ui_text_bindings", [])
    alive = []
    for reference, bindings in registry:
        widget = reference()
        if widget is None:
            continue
        current_bindings = {}
        for (setter, setter_args), (key, values, previous_text) in bindings.items():
            getter_name = {
                "setAccessibleDescription": "accessibleDescription",
                "setAccessibleName": "accessibleName",
                "setPlaceholderText": "placeholderText",
                "setStatusTip": "statusTip",
                "setToolTip": "toolTip",
                "setTitle": "title",
                "setWhatsThis": "whatsThis",
                "setWindowTitle": "windowTitle",
            }.get(setter)
            if setter == "setText":
                getter_name = "text"
            elif setter == "setPlainText":
                getter_name = "toPlainText"
            elif setter == "setTabText" and setter_args:
                getter_name = "tabText"

            if getter_name:
                try:
                    getter = getattr(widget, getter_name)
                    current_text = getter(*setter_args) if setter == "setTabText" else getter()
                except (AttributeError, RuntimeError, TypeError):
                    current_text = previous_text
                if current_text != previous_text:
                    continue

            text = _render_for_app(app, key, values)
            try:
                method = getattr(widget, setter)
                if setter == "setTabText":
                    method(*setter_args, text)
                else:
                    method(text, *setter_args)
            except (AttributeError, RuntimeError, TypeError):
                continue
            current_bindings[(setter, setter_args)] = (key, values, text)
        if current_bindings:
            alive.append((reference, current_bindings))
    app._profiler_ui_text_bindings = alive


if __name__ == "__main__":
    tr = TranslationSystem('de')
    print(f"Sprache: {tr.get_language()}")
    result = tr.scan_and_update()
    print(f"Scan: {result['total']} Strings, {len(result['added'])} neu, {len(result['missing'])} ohne EN")
