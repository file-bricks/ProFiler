import json

import manage_translations
from translator import TranslationSystem


def _translator(tmp_path, translations):
    locales = tmp_path / "locales"
    locales.mkdir(exist_ok=True)
    (locales / "translations.json").write_text(
        json.dumps(translations, ensure_ascii=False), encoding="utf-8"
    )
    return TranslationSystem(app_dir=tmp_path)


def test_supported_languages_are_complete_and_ordered():
    assert TranslationSystem.get_supported_languages() == ["de", "en", "es", "zh", "ja", "ru"]


def test_invalid_default_language_falls_back_to_german(tmp_path):
    assert TranslationSystem("fr", app_dir=tmp_path).get_language() == "de"


def test_t_falls_back_to_english_then_german_for_untranslated_languages(tmp_path):
    translator = _translator(tmp_path, {"Öffnen": {"de": "Öffnen", "en": "Open", "es": ""}})

    translator.set_language("es")
    assert translator.t("Öffnen") == "Open"

    translator.set_language("zh")
    assert translator.t("Öffnen") == "Open"

    translator = _translator(tmp_path, {"Öffnen": {"de": "Öffnen", "en": ""}})
    translator.set_language("ja")
    assert translator.t("Öffnen") == "Öffnen"
    assert translator.t("untranslated-key") == "untranslated-key"

    translator = _translator(tmp_path, {"Unübersetzt": {"de": "", "en": "", "es": ""}})
    translator.set_language("es")
    assert translator.t("Unübersetzt") == "Unübersetzt"


def test_t_prefers_a_reviewed_tier_two_translation_and_reports_missing_values(tmp_path):
    translator = _translator(tmp_path, {"Öffnen": {"de": "Öffnen", "en": "Open", "es": "Abrir"}})

    translator.set_language("es")
    assert translator.t("Öffnen") == "Abrir"
    assert translator.get_missing_translations("es") == []
    assert translator.get_missing_translations("ru") == ["Öffnen"]


def test_new_entries_use_the_full_language_schema(tmp_path):
    translator = TranslationSystem(app_dir=tmp_path)
    translator.add_translation("Speichern", "Speichern", "Save")

    assert translator.translations["Speichern"] == {
        "de": "Speichern",
        "en": "Save",
        "es": "",
        "zh": "",
        "ja": "",
        "ru": "",
    }


def test_scanner_entries_use_the_full_language_schema(tmp_path):
    (tmp_path / "sample.py").write_text('button.setText("Öffnen")', encoding="utf-8")
    translator = TranslationSystem(app_dir=tmp_path)

    result = translator.scan_and_update(tmp_path)

    assert result["added"] == ["Öffnen"]
    assert set(translator.translations["Öffnen"]) == set(TranslationSystem.get_supported_languages())


def test_legacy_translation_manager_uses_the_full_language_schema(tmp_path):
    (tmp_path / "sample.py").write_text('button.setText("Öffnen")', encoding="utf-8")

    manage_translations.manage_translations(tmp_path)

    translations = json.loads((tmp_path / "locales" / "translations.json").read_text(encoding="utf-8"))
    assert set(translations["Öffnen"]) == set(TranslationSystem.get_supported_languages())


def test_repository_translation_entries_keep_de_and_en_integrity():
    translations_path = TranslationSystem().translations_file
    translations = json.loads(translations_path.read_text(encoding="utf-8"))

    assert translations
    assert all(
        isinstance(entry, dict)
        and isinstance(entry.get("de"), str)
        and entry["de"]
        and isinstance(entry.get("en"), str)
        and entry["en"]
        for entry in translations.values()
    )
