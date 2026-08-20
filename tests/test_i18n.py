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


def test_repository_translation_entries_have_full_six_language_parity():
    translations_path = TranslationSystem().translations_file
    translations = json.loads(translations_path.read_text(encoding="utf-8"))

    assert translations
    assert len(translations) >= 100
    languages = TranslationSystem.get_supported_languages()
    for key, entry in translations.items():
        assert isinstance(entry, dict), f"Key '{key}' is not a dict"
        for lang in languages:
            val = entry.get(lang)
            assert isinstance(val, str) and val.strip(), (
                f"Key '{key}' is missing valid translation for language '{lang}'"
            )


def test_repository_missing_translations_is_empty_for_all_supported_languages():
    translator = TranslationSystem()
    for lang in TranslationSystem.get_supported_languages():
        missing = translator.get_missing_translations(lang)
        assert missing == [], f"Found missing translations for '{lang}': {missing}"


def test_language_names_and_display_mappings_cover_all_supported():
    names = TranslationSystem.get_language_names()
    display = TranslationSystem.get_language_display_names()
    supported = TranslationSystem.get_supported_languages()

    assert list(names.keys()) == supported
    assert list(display.keys()) == supported
    assert names["de"] == "Deutsch"
    assert names["en"] == "English"
    assert names["es"] == "Español"
    assert names["zh"] == "简体中文"
    assert names["ja"] == "日本語"
    assert names["ru"] == "Русский"


def test_store_manifests_include_all_supported_tier2_languages():
    root = TranslationSystem().app_dir
    pkg_file = root / "store_package.json"
    manifest_file = root / "store_package" / "ProFiler" / "AppxManifest.xml"

    pkg = json.loads(pkg_file.read_text(encoding="utf-8"))
    expected_store_codes = ["de-DE", "en-US", "es-ES", "zh-CN", "ja-JP", "ru-RU"]
    for code in expected_store_codes:
        assert code in pkg["languages"], f"Store package missing language code: {code}"

    manifest_text = manifest_file.read_text(encoding="utf-8").lower()
    expected_xml_codes = ["de-de", "en-us", "es-es", "zh-cn", "ja-jp", "ru-ru"]
    for code in expected_xml_codes:
        assert f'language="{code}"' in manifest_text, f"AppxManifest missing resource language: {code}"


def test_t_translates_sample_keys_in_all_six_languages():
    translator = TranslationSystem()
    key = "Ausgewählte Duplikate löschen"

    translator.set_language("de")
    assert translator.t(key) == "Ausgewählte Duplikate löschen"

    translator.set_language("en")
    assert translator.t(key) == "Delete Selected Duplicates"

    translator.set_language("es")
    assert translator.t(key) == "Eliminar duplicados seleccionados"

    translator.set_language("zh")
    assert translator.t(key) == "删除选中的重复项"

    translator.set_language("ja")
    assert translator.t(key) == "選択した重複項目を削除"

    translator.set_language("ru")
    assert translator.t(key) == "Удалить выбранные дубликаты"
