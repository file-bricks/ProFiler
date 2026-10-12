import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QEvent

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton, QLineEdit, QTextEdit, QTreeWidget

import Profiler_Suite_V15 as profiler


class DummySettings:
    def __init__(self):
        self.data = {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value


def _button_by_accessible_name(widget, name):
    for button in widget.findChildren(QPushButton):
        if button.accessibleName() == name:
            return button
    raise AssertionError(f"Button mit Accessible Name {name!r} nicht gefunden")


def test_compact_picker_buttons_expose_accessible_context():
    app = QApplication.instance() or QApplication([])

    autosync = profiler.AutoSyncWidget(DummySettings())
    source_button = _button_by_accessible_name(autosync, "Quellordner auswählen")
    target_button = _button_by_accessible_name(autosync, "Zielordner auswählen")

    assert source_button.text() == "📁"
    assert source_button.toolTip() == "Quellordner auswählen"
    assert "überwachten Quellordners" in source_button.accessibleDescription()

    assert target_button.text() == "📁"
    assert target_button.toolTip() == "Zielordner auswählen"
    assert "Synchronisationsziels" in target_button.accessibleDescription()

    dialog = profiler.ConnectionDialog()
    db_button = _button_by_accessible_name(dialog, "Datenbankdatei auswählen")

    assert db_button.text() == "..."
    assert db_button.toolTip() == "Datenbankdatei auswählen"
    assert "Datenbankdatei" in db_button.accessibleDescription()

    dialog.close()
    autosync.close()
    app.quit()


def test_batch_dialog_compact_action_buttons_expose_accessible_context():
    app = QApplication.instance() or QApplication([])

    copy_dialog = profiler.BatchDialog(["demo.pdf"], "copy", "Dateien kopieren")
    copy_button = _button_by_accessible_name(copy_dialog, "Zielordner auswählen")
    assert copy_button.text() == "..."
    assert copy_button.toolTip() == "Zielordner auswählen"
    assert "Batch-Kopie" in copy_button.accessibleDescription()

    encrypt_dialog = profiler.BatchDialog(["demo.pdf"], "pdf_encrypt", "PDF verschlüsseln")
    show_password_button = _button_by_accessible_name(encrypt_dialog, "Passwort anzeigen")
    assert show_password_button.text() == "👁"
    assert show_password_button.toolTip() == "Passwort anzeigen, solange gedrückt"
    assert "solange" in show_password_button.accessibleDescription()

    extract_dialog = profiler.BatchDialog(["demo.pdf"], "pdf_extract_text", "Text extrahieren")
    output_button = _button_by_accessible_name(extract_dialog, "Ausgabeordner auswählen")
    assert output_button.text() == "..."
    assert output_button.toolTip() == "Ausgabeordner auswählen"
    assert "Textextraktion" in output_button.accessibleDescription()

    copy_dialog.close()
    encrypt_dialog.close()
    extract_dialog.close()
    app.quit()


@pytest.mark.parametrize(
    ("delete_mode", "expected_operation"),
    [("soft", "soft"), ("hard", "hard"), ("safety", "safety"), ("legacy", "safety")],
)
def test_group_cleanup_action_deletes_only_older_versions_in_configured_mode(
    monkeypatch, delete_mode, expected_operation
):
    """Run the context-menu callback with fake database rows and preserve newest item."""
    captured_actions = []
    calls = []

    class FakeMenu:
        def __init__(self, _parent):
            pass

        def addAction(self, text, callback=None):
            if callback is not None:
                captured_actions.append((text, callback))

        def addSeparator(self):
            pass

        def exec(self, _position):
            pass

    class FakeChild:
        def __init__(self, version_id):
            self.version_id = version_id

        def data(self, _column, _role):
            return {"id": self.version_id, "db": "sandbox.sqlite"}

    class FakeGroup:
        children = [FakeChild("newest"), FakeChild("older-a"), FakeChild("older-b")]

        def isExpanded(self):
            return False

        def childCount(self):
            return len(self.children)

        def child(self, index):
            return self.children[index]

    class FakeTree:
        def mapToGlobal(self, position):
            return position

    class FakeDatabase:
        def __init__(self, _path):
            pass

        def soft_delete_version(self, version_id):
            calls.append(("soft", version_id))

        def hard_delete_version(self, version_id):
            calls.append(("hard", version_id))

        def safety_hide_version(self, version_id):
            calls.append(("safety", version_id))

        def close(self):
            pass

    monkeypatch.setattr(profiler, "QMenu", FakeMenu)
    monkeypatch.setattr(profiler, "ConnectionDB", FakeDatabase)
    monkeypatch.setattr(profiler, "_ui_text", lambda value, **_kwargs: value)
    monkeypatch.setattr(
        profiler,
        "_ui_message_box",
        lambda *_args, **_kwargs: profiler.QMessageBox.StandardButton.Yes,
    )
    fake_self = SimpleNamespace(
        result_tree=FakeTree(),
        settings=DummySettings(),
        perform_search=lambda: calls.append(("refresh", None)),
        expand_all_groups=lambda: None,
        collapse_all_groups=lambda: None,
    )
    fake_self.settings.set("delete_mode", delete_mode)

    profiler.SearchWidgetHybrid.show_group_context_menu(fake_self, (0, 0), FakeGroup())
    cleanup_callbacks = [
        callback
        for _label, callback in captured_actions
        if getattr(callback, "__name__", "") == "delete_old_versions"
    ]
    assert len(cleanup_callbacks) == 1
    cleanup_callbacks[0]()

    assert calls == [
        (expected_operation, "older-a"),
        (expected_operation, "older-b"),
        ("refresh", None),
    ]


def test_search_workspaces_expose_screen_reader_context():
    app = QApplication.instance() or QApplication([])
    search = profiler.SearchWidgetHybrid(SimpleNamespace(dbs=[]), DummySettings())

    search_input = search.findChild(QLineEdit)
    assert search_input is not None
    assert search_input.accessibleName() == "Dateisuche"
    assert "Dokumentensammlungen" in search_input.accessibleDescription()
    assert search_input.toolTip() == "Dateien und Dokumente durchsuchen"

    results = search.findChild(QTreeWidget)
    assert results is not None
    assert results.accessibleName() == "Suchergebnisse"
    assert "Pfeiltasten" in results.accessibleDescription()
    assert "verschoben" in results.toolTip()

    preview = search.findChild(QTextEdit)
    assert preview is not None
    assert preview.isReadOnly()
    assert preview.accessibleName() == "Dateivorschau"
    assert "ausgewählten Datei" in preview.accessibleDescription()
    assert preview.toolTip() == "Vorschau der ausgewählten Datei"

    search.close()
    app.quit()


def test_settings_dialog_exposes_accessible_context_and_umlauts():
    app = QApplication.instance() or QApplication([])
    settings = DummySettings()
    dialog = profiler.SettingsDialog(settings)

    assert dialog.accessibleName() == "Programmeinstellungen"
    assert "Konfigurationsdialog" in dialog.accessibleDescription()

    tabs = dialog.findChild(profiler.QTabWidget)
    assert tabs is not None
    assert tabs.count() == 4
    assert tabs.tabText(0) == "Allgemein"
    assert tabs.tabText(1) == "Löschen"
    assert tabs.tabText(2) == "PDF"
    assert tabs.tabText(3) == "Externe Tools"

    # Tab 1: Allgemein
    assert dialog.combo_ui_lang.accessibleName() == "Oberflächensprache"
    assert dialog.combo_ui_lang.toolTip() == "Oberflächensprache auswählen"

    # Tab 2: Löschen
    assert dialog.radio_soft.accessibleName() == "Soft-Delete Modus"
    assert dialog.radio_hard.accessibleName() == "Hard-Delete Modus"
    assert dialog.radio_safety.accessibleName() == "Safety-Mode"
    assert dialog.spin_retention.accessibleName() == "Aufbewahrungsdauer im Papierkorb"
    assert dialog.cb_auto_cleanup.accessibleName() == "Automatisches Aufräumen beim Start"
    assert dialog.combo_spawn_format.accessibleName() == "Standard-Spawn-Format"
    assert dialog.cb_rename_filesystem.accessibleName() == "Umbenennung im Dateisystem anwenden"

    # Tab 3: PDF & echte Umlaute
    assert dialog.master_pwd1.accessibleName() == "Masterpasswort 1 zum Öffnen"
    assert dialog.cb_show_pwd1.accessibleName() == "Masterpasswort 1 im Klartext anzeigen"
    assert dialog.cb_show_pwd1.toolTip() == "Masterpasswort 1 im Klartext anzeigen"
    assert dialog.master_pwd2.accessibleName() == "Masterpasswort 2 zum Speichern"
    assert dialog.cb_show_pwd2.accessibleName() == "Masterpasswort 2 im Klartext anzeigen"
    assert dialog.cb_ocr_enabled.accessibleName() == "OCR-Texterkennung aktivieren"
    assert dialog.combo_ocr_lang.accessibleName() == "OCR-Sprache"

    # Prüfe, dass echte deutsche Umlaute verwendet werden ("Masterpasswörter" statt "Masterpasswrter")
    groupboxes = [gb.title() for gb in dialog.findChildren(profiler.QGroupBox)]
    assert "Masterpasswörter" in groupboxes
    assert "Masterpasswrter" not in groupboxes

    # Tab 4: Externe Tools
    assert dialog.pythonbox_path.accessibleName() == "PythonBox-Pfad"
    assert dialog.sqlite_path.accessibleName() == "SQLite-Viewer-Pfad"
    assert dialog.formconstr_path.accessibleName() == "FormConstructor-Pfad"

    dialog.close()
    app.quit()


def test_pdf_password_dialog_exposes_accessible_context():
    app = QApplication.instance() or QApplication([])
    settings = DummySettings()

    # Encrypt-Modus
    enc_dialog = profiler.PDFPasswordDialog(["sample1.pdf", "sample2.pdf"], mode="encrypt", settings=settings)
    assert enc_dialog.windowTitle() == "PDF-Verschlüsselung"
    assert enc_dialog.accessibleName() == "PDF-Passwortdialog"
    assert enc_dialog.radio_individual.accessibleName() == "Individuelles Passwort wählen"
    assert enc_dialog.password_input.accessibleName() == "Passworteingabe"
    assert enc_dialog.password_input.toolTip() == "Passwort für die PDF-Operation eingeben"
    assert enc_dialog.radio_master.accessibleName() == "Hinterlegtes Masterpasswort verwenden"
    assert enc_dialog.cb_show_password.accessibleName() == "Passwort im Klartext anzeigen"
    assert enc_dialog.cb_show_password.toolTip() == "Passwort im Klartext anzeigen"

    # Decrypt-Modus
    dec_dialog = profiler.PDFPasswordDialog(["sample1.pdf"], mode="decrypt", settings=settings)
    assert dec_dialog.windowTitle() == "PDF-Entschlüsselung"
    assert dec_dialog.accessibleName() == "PDF-Passwortdialog"

    enc_dialog.close()
    dec_dialog.close()
    app.quit()


def test_search_widget_deleted_checkbox_and_tree_keyboard_navigation():
    app = QApplication.instance() or QApplication([])
    search = profiler.SearchWidgetHybrid(SimpleNamespace(dbs=[]), DummySettings())

    # 1. Echte Umlaute auf Checkbox (behebt "Gelschte anzeigen")
    assert search.cb_show_deleted.text() == "Gelöschte anzeigen"
    assert search.cb_show_deleted.accessibleName() == "Gelöschte Dateien anzeigen"
    assert "Gelöschte Dateien" in search.cb_show_deleted.toolTip()

    # 2. AccessibleResultTree Instanz & Barrierefreiheit
    assert isinstance(search.result_tree, profiler.AccessibleResultTree)
    assert isinstance(search.result_tree, QTreeWidget)

    # 3. Tastaturnavigation via keyPressEvent
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeyEvent

    called_events = []
    search.open_selected_file = lambda: called_events.append("open")
    search.delete_selected = lambda: called_events.append("delete")
    search.perform_search = lambda: called_events.append("search")

    # Enter/Return
    key_enter = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
    search.result_tree.keyPressEvent(key_enter)
    assert "open" in called_events

    # Delete
    key_del = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Delete, Qt.KeyboardModifier.NoModifier)
    search.result_tree.keyPressEvent(key_del)
    assert "delete" in called_events

    # F5
    key_f5 = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_F5, Qt.KeyboardModifier.NoModifier)
    search.result_tree.keyPressEvent(key_f5)
    assert "search" in called_events

    # focus_search_input
    search.show()
    search.focus_search_input()
    assert search.search_input.isVisible()

    search.close()
    app.quit()


def test_shortcuts_dialog_lists_current_shortcuts_and_scope():
    app = QApplication.instance() or QApplication([])
    dialog = profiler.ShortcutsDialog()

    assert dialog.windowTitle() == "Tastaturkürzel & Navigation"
    assert dialog.accessibleName() == "Tastaturkürzel & Navigation"
    assert "Tastenkombinationen" in dialog.accessibleDescription()
    assert "Konformitätsangaben" not in dialog.accessibleDescription()
    labels = [label.text() for label in dialog.findChildren(profiler.QLabel)]
    assert any("Vorhandene Tastenkürzel" in label for label in labels)
    assert any("keine formale BITV- oder WCAG-Konformitätsbewertung" in label for label in labels)
    assert not any("Erfüllt BITV" in label for label in labels)

    # Tabelle prüfen
    assert dialog.table.columnCount() == 3
    assert dialog.table.horizontalHeaderItem(0).text() == "Tastenkombination"
    assert dialog.table.horizontalHeaderItem(1).text() == "Aktion / Funktion"
    assert dialog.table.horizontalHeaderItem(2).text() == "Bereich"
    assert dialog.table.rowCount() >= 15

    keys = [dialog.table.item(row, 0).text() for row in range(dialog.table.rowCount())]
    assert "F1" in keys
    assert "Ctrl+F" in keys
    assert "Ctrl+1" in keys
    assert "Ctrl+," in keys
    assert "Ctrl+Q" in keys
    assert "Enter / Return" in keys
    assert "Entf / Backspace" in keys
    assert "F5" in keys

    # Schließen Button & Escape
    assert dialog.btn_close.accessibleName() == "Dialog schließen"

    dialog.close()
    app.quit()


def test_shortcuts_dialog_renders_in_all_supported_locales():
    app = QApplication.instance() or QApplication([])
    previous_translator = getattr(app, "_profiler_ui_translator", None)
    previous_bindings = getattr(app, "_profiler_ui_text_bindings", None)
    translator = profiler.TranslationSystem(
        "de", app_dir=Path(profiler.__file__).resolve().parent
    )
    profiler._set_application_translator(app, translator)
    expected = {
        "de": ("Tastaturkürzel & Navigation", "Tastenkombination", "Übersicht zu Tastaturkürzeln und Navigation öffnen", "Global"),
        "en": ("Keyboard Shortcuts & Navigation", "Shortcut", "Open keyboard shortcuts and navigation overview", "Global"),
        "es": ("Atajos de teclado y navegación", "Combinación de teclas", "Abrir el resumen de atajos de teclado y navegación", "Global"),
        "zh": ("键盘快捷键与导航", "快捷键", "打开键盘快捷键与导航概览", "全局"),
        "ja": ("キーボードショートカットとナビゲーション", "ショートカット", "キーボードショートカットとナビゲーションの一覧を開く", "グローバル"),
        "ru": ("Сочетания клавиш и навигация", "Сочетание клавиш", "Открыть обзор сочетаний клавиш и навигации", "Глобально"),
    }
    try:
        for language, (title, key_header, first_action, scope) in expected.items():
            translator.set_language(language)
            dialog = profiler.ShortcutsDialog()
            assert dialog.windowTitle() == title
            assert dialog.table.horizontalHeaderItem(0).text() == key_header
            assert dialog.table.item(0, 1).text() == first_action
            assert dialog.table.item(0, 2).text() == scope
            dialog.close()
    finally:
        if previous_translator is None:
            delattr(app, "_profiler_ui_translator")
        else:
            app._profiler_ui_translator = previous_translator
        if previous_bindings is None:
            if hasattr(app, "_profiler_ui_text_bindings"):
                delattr(app, "_profiler_ui_text_bindings")
        else:
            app._profiler_ui_text_bindings = previous_bindings
def test_unified_main_window_menu_mnemonics_shortcuts_and_a11y_tabs():
    app = QApplication.instance() or QApplication([])
    settings = DummySettings()
    win = profiler.UnifiedMainWindow(settings=settings)

    # 1. Barrierefreie Tabs
    assert win.tabs.accessibleName() == "Hauptbereiche"
    assert "Hauptnavigation" in win.tabs.accessibleDescription()
    assert win.tabs.count() == 3

    # 2. Menüleiste Mnemonics
    menu_titles = [m.title() for m in win.menuBar().findChildren(profiler.QMenu)]
    assert "&Datei" in menu_titles
    assert "&Tools" in menu_titles
    assert "&Hilfe" in menu_titles

    # 3. Aktionen & Shortcuts
    assert win.act_settings.shortcut().toString() == "Ctrl+,"
    assert win.act_settings.text() == "⚙️ Einstellungen"

    assert win.act_close.shortcut().toString() == "Ctrl+Q"
    assert win.act_close.text() == "❌ Beenden"

    assert win.act_shortcuts.shortcut().toString() == "F1"
    assert win.act_shortcuts.text() == "⌨️ Tastaturkürzel & Navigation"

    # 4. Globale Shortcuts (Ctrl+F, F5, Ctrl+1, Ctrl+2, Ctrl+3)
    assert hasattr(win, "shortcut_find")
    assert hasattr(win, "shortcut_refresh")
    assert hasattr(win, "shortcut_tab1")

    # 5. focus_search test
    win.tabs.setCurrentIndex(1)
    assert win.tabs.currentIndex() == 1
    win.focus_search()
    assert win.tabs.currentIndex() == 0

    # 6. Shortcuts Dialog über Fenster öffnen
    dlg = win.show_shortcuts_dialog()
    assert dlg is not None

    win.close()
    app.quit()

def test_ui_language_save_retranslates_navigation_and_keeps_machine_values(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    settings_path = tmp_path / "settings.json"
    monkeypatch.setattr(profiler, "SEARCH_CONFIG_PATH", str(tmp_path / "search.json"))
    monkeypatch.setattr(profiler, "SYNC_CONFIG_PATH", str(tmp_path / "connections.json"))
    monkeypatch.setattr(profiler, "SETTINGS_PATH", str(settings_path))
    monkeypatch.setattr(profiler, "resolve_read_path", lambda name: tmp_path / name)

    settings = profiler.SettingsManager()
    settings.set("default_spawn_format", "docx")
    settings.set("ocr_language", "fra")
    settings.set("ui_language", "de")
    settings.set("language", "de")
    window = profiler.UnifiedMainWindow(settings=settings)

    # Retranslating persistent widgets must preserve the active view and user
    # state rather than recreating the search or connection controls.
    window.tabs.setCurrentIndex(1)
    search = window.search_widget.search_input
    search.blockSignals(True)
    search.setText("quarterly report")
    search.blockSignals(False)
    window.search_widget.search_timer.stop()
    for checkbox in (window.search_widget.cb_show_deleted, window.search_widget.cb_show_hidden):
        checkbox.blockSignals(True)
        checkbox.setChecked(True)
        checkbox.blockSignals(False)
    type_filter = window.search_widget.type_checks["Dokumente"]
    type_filter.blockSignals(True)
    type_filter.setChecked(True)
    type_filter.blockSignals(False)

    connection = profiler.ConnectionDialog(
        window,
        {
            "id": "conn-test",
            "name": "Demo Datei",
            "sources": [str(tmp_path / "source")],
            "target": str(tmp_path / "target"),
            "direction": "one_way",
            "db_path": str(tmp_path / "index.db"),
        },
    )
    original_connection = connection.get_result()

    expected_file_menu = {
        "de": "&Datei",
        "en": "&File",
        "es": "&Archivo",
        "zh": "&文件",
        "ja": "ファイル(&F)",
        "ru": "&Файл",
    }
    expected_search_tab = {
        "de": "Suche & Explorer",
        "en": "Search & Explorer",
        "es": "Búsqueda y explorador",
        "zh": "搜索与资源管理器",
        "ja": "検索＆エクスプローラー",
        "ru": "Поиск и проводник",
    }
    expected_document_filter = {
        "de": "Dokumente",
        "en": "Documents",
        "es": "Documentos",
        "zh": "文档",
        "ja": "文書",
        "ru": "Документы",
    }
    expected_direction_label = {
        "de": "Einweg-Sync",
        "en": "One-way",
        "es": "Unidireccional",
        "zh": "单向",
        "ja": "一方向",
        "ru": "В одну сторону",
    }
    expected_result_headers = {
        "de": ["Datei", "Typ", "Größe", "Datum"],
        "en": ["File", "Type", "Size", "Date"],
        "es": ["Archivo", "Tipo", "Tamaño", "Fecha"],
        "zh": ["文件", "类型", "大小", "日期"],
        "ja": ["ファイル", "種類", "サイズ", "日付"],
        "ru": ["Файл", "Тип", "Размер", "Дата"],
    }
    initial_result_column_width = window.search_widget.result_tree.columnWidth(0)
    for language, menu_title in expected_file_menu.items():
        window.ui_translator.set_language(language)
        window.retranslate_ui()
        assert window.file_menu.title() == menu_title
        assert window.tabs.tabText(0) == expected_search_tab[language]
        assert window.tabs.currentIndex() == 1
        assert search.text() == "quarterly report"
        assert window.search_widget.cb_show_deleted.isChecked()
        assert window.search_widget.cb_show_hidden.isChecked()
        assert window.search_widget.type_checks["Dokumente"] is type_filter
        assert type_filter.isChecked()
        assert type_filter.text() == expected_document_filter[language]
        result_headers = window.search_widget.result_tree.headerItem()
        assert [result_headers.text(index) for index in range(result_headers.columnCount())] == expected_result_headers[language]
        assert window.search_widget.result_tree.columnWidth(0) == initial_result_column_width
        assert connection.get_result() == original_connection

        localized_connection = profiler.ConnectionDialog(
            window,
            {
                "id": "locale-probe",
                "name": "Locale probe",
                "sources": [str(tmp_path / "source")],
                "target": str(tmp_path / "target"),
                "direction": "one_way",
                "db_path": str(tmp_path / "index.db"),
            },
        )
        assert localized_connection.direction.currentText() == expected_direction_label[language]
        assert localized_connection.direction.currentData() == "one_way"
        assert localized_connection.get_result()["direction"] == "one_way"
        localized_connection.close()

    window.ui_translator.set_language("de")
    window.retranslate_ui()

    with monkeypatch.context() as clock:
        clock.setattr(profiler.time, "monotonic", lambda: 10.0)
        window._show_status("Bereit", 1000)
        deadline = window._status_message[2]
        clock.setattr(profiler.time, "monotonic", lambda: 10.6)
        window.ui_translator.set_language("en")
        window.retranslate_ui()
        assert window.statusBar().currentMessage() == "Ready"
        assert window._status_message[2] == deadline

        clock.setattr(profiler.time, "monotonic", lambda: 11.1)
        window.retranslate_ui()
        assert window.statusBar().currentMessage() == ""
        assert window._status_message == ("", {}, None)

    window.ui_translator.set_language("de")
    window._show_status("Bereit")

    def save_spanish(dialog):
        dialog.combo_ui_lang.setCurrentIndex(dialog.combo_ui_lang.findData("es"))
        dialog.save_and_close()
        return dialog.result()

    monkeypatch.setattr(profiler.SettingsDialog, "exec", save_spanish)
    settings_dialog = window.show_settings()

    assert settings_dialog.result() == profiler.QDialog.DialogCode.Accepted
    assert settings.get("ui_language") == "es"
    assert settings.get("language") == "es"
    assert window.ui_translator.get_language() == "es"
    assert window.file_menu.title() == "&Archivo"
    assert window.act_settings.text() == "⚙️ Configuración"
    assert window.tabs.tabText(0) == "Búsqueda y explorador"
    assert window.statusBar().currentMessage() == "Listo"
    assert window.tabs.currentIndex() == 1
    assert search.text() == "quarterly report"
    assert window.search_widget.cb_show_deleted.isChecked()
    assert window.search_widget.cb_show_hidden.isChecked()
    assert type_filter.isChecked()
    assert type_filter.text() == "Documentos"
    assert connection.get_result() == original_connection
    assert window.tray_show_action.text() == "Mostrar"
    assert window.tray_exit_action.text() == "❌ Salir"
    assert settings.get("default_spawn_format") == "docx"
    assert settings.get("ocr_language") == "fra"

    reloaded = profiler.SettingsManager()
    assert reloaded.get("ui_language") == "es"
    window.close()

    reopened = profiler.UnifiedMainWindow(settings=reloaded)
    assert reopened.ui_translator.get_language() == "es"
    assert reopened.act_settings.text() == "⚙️ Configuración"

    def cancel_settings(dialog):
        dialog.combo_ui_lang.setCurrentIndex(dialog.combo_ui_lang.findData("ru"))
        dialog.reject()
        return dialog.result()

    monkeypatch.setattr(profiler.SettingsDialog, "exec", cancel_settings)
    canceled = reopened.show_settings()
    assert canceled.result() == profiler.QDialog.DialogCode.Rejected
    assert reloaded.get("ui_language") == "es"
    assert reopened.ui_translator.get_language() == "es"

    connection = profiler.ConnectionDialog(reopened, original_connection)
    assert connection.direction.currentData() == "one_way"
    assert connection.direction.currentText() == "Unidireccional"
    connection.direction.setCurrentIndex(connection.direction.findData("two_way"))
    assert connection.direction.currentText() == "Bidireccional"
    assert connection.get_result()["direction"] == "two_way"

    connection.close()
    canceled.close()
    reopened.close()

    reloaded.set("ui_language", "unsupported-locale")
    invalid_locale_window = profiler.UnifiedMainWindow(settings=reloaded)
    assert invalid_locale_window.ui_translator.get_language() == "de"
    assert invalid_locale_window.file_menu.title() == "&Datei"
    invalid_locale_window.close()
    app.quit()


def test_message_box_does_not_retranslate_user_text_and_preserves_question_result(monkeypatch):
    app = QApplication.instance() or QApplication([])
    previous_translator = getattr(app, "_profiler_ui_translator", None)
    previous_bindings = getattr(app, "_profiler_ui_text_bindings", None)
    translator = profiler.TranslationSystem("en")
    translator.translations["Ja"] = {"de": "Ja", "en": "Yes"}
    translator.translations["Nein"] = {"de": "Nein", "en": "No"}
    translator.translations["Abbrechen"] = {"de": "Abbrechen", "en": "Cancel"}
    translator.translations["Schließen"] = {"de": "Schließen", "en": "Close"}
    profiler._set_application_translator(app, translator)
    real_message_box = profiler.QMessageBox
    standard = real_message_box.StandardButton
    class FakeButton:
        def __init__(self):
            self.text = None

        def setText(self, text):
            self.text = text

    class FakeMessageBox:
        Icon = real_message_box.Icon
        StandardButton = standard
        instance = None
        next_result = standard.No

        def __init__(self, icon, title, text, buttons, parent):
            self.icon = icon
            self.title = title
            self.text = text
            self.buttons = buttons
            self.parent = parent
            self.default_button = standard.NoButton
            self.button_widgets = {
                button: FakeButton()
                for button in (standard.Yes, standard.No, standard.Cancel, standard.Close)
            }
            FakeMessageBox.instance = self

        def button(self, button):
            return self.button_widgets.get(button)

        def setDefaultButton(self, button):
            self.default_button = button

        def exec(self):
            return FakeMessageBox.next_result

    try:
        monkeypatch.setattr(profiler, "QMessageBox", FakeMessageBox)
        title = profiler._ui_text("Datei")
        # The body is user-provided text that also happens to be a catalog key.
        body = profiler._ui_text("{value0}", value0="Datei")
        result = profiler._ui_message_box("question", None, title, body)

        box = FakeMessageBox.instance
        assert box.title == "File"
        assert box.text == "Datei"
        assert box.buttons == standard.Yes | standard.No
        assert box.default_button == standard.NoButton
        assert result == standard.No
        assert box.button_widgets[standard.Yes].text == "Yes"
        assert box.button_widgets[standard.No].text == "No"

        explicit_buttons = standard.Yes | standard.No | standard.Cancel | standard.Close
        FakeMessageBox.next_result = standard.Close
        close_result = profiler._ui_message_box(
            "question",
            None,
            title,
            body,
            explicit_buttons,
            standard.Close,
        )
        close_box = FakeMessageBox.instance
        assert close_box.buttons == explicit_buttons
        assert close_box.default_button == standard.Close
        assert close_result == standard.Close
        assert close_box.button_widgets[standard.Cancel].text == "Cancel"
        assert close_box.button_widgets[standard.Close].text == "Close"
    finally:
        if previous_translator is None:
            delattr(app, "_profiler_ui_translator")
        else:
            app._profiler_ui_translator = previous_translator
        if previous_bindings is None:
            if hasattr(app, "_profiler_ui_text_bindings"):
                delattr(app, "_profiler_ui_text_bindings")
        else:
            app._profiler_ui_text_bindings = previous_bindings


def test_privacy_ampel_renders_localized_tabs_dynamic_status_and_tray_without_host_data(
    monkeypatch, tmp_path
):
    import ProFiler_Datenschutzampel as privacy

    app = QApplication.instance() or QApplication([])
    previous_translator = getattr(app, "_profiler_ui_translator", None)

    class FakeSignal:
        def connect(self, callback):
            self.callback = callback

    class FakeClipboard:
        def __init__(self):
            self.dataChanged = FakeSignal()
            self.read_count = 0

        def text(self):
            self.read_count += 1
            return ""

        def clear(self):
            raise AssertionError("The locale render test must not clear a clipboard")

    clipboard = FakeClipboard()
    monkeypatch.setattr(
        privacy,
        "QApplication",
        SimpleNamespace(instance=QApplication.instance, clipboard=lambda: clipboard),
    )
    monkeypatch.setattr(privacy, "CONFIG_PATH", tmp_path / "datenschutzampel.json")
    monkeypatch.setattr(privacy, "resolve_read_path", lambda name: tmp_path / name)

    expected = {
        "de": {
            "title": "🚦 ProFiler Datenschutzampel",
            "tabs": ["📋 Listen (Blacklist/Whitelist)", "🚦 Ampel-Steuerung", "🕘 Verlauf"],
            "status": "Status: ROT - probe-value",
            "tray": ["📂 Öffnen", "❌ Beenden"],
        },
        "en": {
            "title": "🚦 ProFiler Privacy Light",
            "tabs": ["📋 Lists (blacklist/whitelist)", "🚦 Privacy light controls", "🕘 History"],
            "status": "Status: RED - probe-value",
            "tray": ["📂 Open", "❌ Quit"],
        },
        "es": {
            "title": "🚦 Indicador de privacidad de ProFiler",
            "tabs": ["📋 Listas (bloqueo/permitidos)", "🚦 Controles del indicador de privacidad", "🕘 Historial"],
            "status": "Estado: ROJO - probe-value",
            "tray": ["📂 Abrir", "❌ Salir"],
        },
        "zh": {
            "title": "🚦 ProFiler 隐私指示灯",
            "tabs": ["📋 列表（黑名单/白名单）", "🚦 隐私指示灯控制", "🕘 历史记录"],
            "status": "状态：红色 - probe-value",
            "tray": ["📂 打开", "❌ 退出"],
        },
        "ja": {
            "title": "🚦 ProFiler プライバシーライト",
            "tabs": ["📋 リスト（ブラックリスト/ホワイトリスト）", "🚦 プライバシーライトの操作", "🕘 履歴"],
            "status": "状態: 赤 - probe-value",
            "tray": ["📂 開く", "❌ 終了"],
        },
        "ru": {
            "title": "🚦 Индикатор конфиденциальности ProFiler",
            "tabs": ["📋 Списки (черный/белый)", "🚦 Управление индикатором конфиденциальности", "🕘 История"],
            "status": "Статус: КРАСНЫЙ — probe-value",
            "tray": ["📂 Открыть", "❌ Выход"],
        },
    }

    try:
        for language, labels in expected.items():
            translator = profiler.TranslationSystem(language, app_dir=Path(profiler.__file__).parent)
            profiler._set_application_translator(app, translator)
            window = privacy.DatenschutzAmpel()
            tabs = window.findChild(privacy.QTabWidget)
            assert window.windowTitle() == labels["title"]
            assert tabs is not None and tabs.count() == 3
            assert [tabs.tabText(index) for index in range(tabs.count())] == labels["tabs"]

            window.set_ampel("rot", "probe-value")
            assert window.ampel_text.text() == labels["status"]
            assert [action.text() for action in window.tray_icon.contextMenu().actions() if action.text()] == labels["tray"]
            assert window.clip_history == []
            assert clipboard.read_count == 0

            window.tray_icon.hide()
            window.hide()
            window.deleteLater()
            app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            app.processEvents()
    finally:
        if previous_translator is None:
            if hasattr(app, "_profiler_ui_translator"):
                delattr(app, "_profiler_ui_translator")
        else:
            app._profiler_ui_translator = previous_translator


def test_sqlite_viewer_initial_surface_is_localized_without_database_io(monkeypatch):
    if os.name != "nt" and not os.environ.get("DISPLAY"):
        pytest.skip("Tk requires a display; run the SQLite UI smoke on a desktop host")

    import SQLiteViewer as sqlite_viewer
    from tkinter import ttk

    previous_translator = sqlite_viewer._UI_TRANSLATOR
    expected = {
        "de": ("Mini SQL-Ansicht (SQLite)", "Keine Datenbank geöffnet", "Refresh", "Tabelle:"),
        "en": ("Mini SQL Viewer (SQLite)", "No database is open", "Refresh", "Table:"),
        "es": ("Visor SQL mini (SQLite)", "No hay ninguna base de datos abierta", "Actualizar", "Tabla:"),
        "zh": ("SQLite 迷你 SQL 查看器", "没有打开数据库", "刷新", "表格："),
        "ja": ("SQLite ミニ SQL ビューアー", "データベースが開かれていません", "更新", "テーブル:"),
        "ru": ("Мини-просмотрщик SQL (SQLite)", "База данных не открыта", "Обновить", "Таблица:"),
    }

    try:
        for language, (title, status, refresh, table_label) in expected.items():
            sqlite_viewer._UI_TRANSLATOR = profiler.TranslationSystem(
                language, app_dir=Path(profiler.__file__).parent
            )
            window = sqlite_viewer.SqlViewer()
            window.withdraw()

            assert window.title() == title
            assert window.status_var.get() == status
            assert window.refresh_btn.cget("text") == refresh

            descendants = []
            pending = list(window.winfo_children())
            while pending:
                child = pending.pop()
                descendants.append(child)
                pending.extend(child.winfo_children())
            assert any(
                isinstance(child, ttk.Label) and child.cget("text") == table_label
                for child in descendants
            )
            assert window.conn is None
            assert window.db_path is None
            window.destroy()
    finally:
        sqlite_viewer._UI_TRANSLATOR = previous_translator


def test_worker_messages_picker_accessibility_and_pdf_intro_follow_ui_locale(monkeypatch):
    app = QApplication.instance() or QApplication([])
    previous_translator = getattr(app, "_profiler_ui_translator", None)
    translator = profiler.TranslationSystem("en", app_dir=Path(profiler.__file__).parent)
    button = QPushButton()
    dialog = None

    try:
        profiler._set_application_translator(app, translator)
        protected_user_value = "Zielordner auswählen"
        message = profiler._ui_message(
            "Durchsuche: {value0} ({value1}/{value2})",
            value0=protected_user_value,
            value1=2,
            value2=5,
        )
        assert profiler._render_ui_message(message) == "Scanning: Zielordner auswählen (2/5)"

        # Batch log templates translate on the GUI side, while filenames and
        # exception details remain data even when they match a catalog key.
        filename = "Zielordner auswählen"
        batch_dialog = profiler.BatchDialog([filename], "copy", "Copy files")
        batch_dialog._on_progress(1, 1, filename)
        assert batch_dialog.status_label.text() == f"Processing 1/1: {filename}"

        batch_processor = profiler.BatchProcessor([filename], "copy", {})
        batch_logs = []
        completed = []
        batch_processor.log_message.connect(batch_logs.append)
        batch_processor.file_completed.connect(
            lambda name, success, result: completed.append((name, success, result))
        )
        batch_processor.run()
        assert completed == [(filename, False, "Kein Zielordner angegeben")]
        assert profiler._render_ui_message(batch_logs[0]) == (
            f"✗ {filename} — No destination folder was specified"
        )
        batch_dialog._on_log(batch_logs[0])
        assert batch_dialog.log_text.toPlainText() == (
            f"✗ {filename} — No destination folder was specified"
        )

        exception_processor = profiler.BatchProcessor([filename], "copy", {})

        def raise_catalog_key_as_external_error(_filepath):
            raise RuntimeError(filename)

        exception_processor._copy_file = raise_catalog_key_as_external_error
        exception_logs = []
        exception_processor.log_message.connect(exception_logs.append)
        exception_processor.run()
        assert profiler._render_ui_message(exception_logs[0]) == (
            f"✗ {filename} — Error: {filename}"
        )

        # A PDF library error may happen to equal a catalog key; its origin is
        # still external exception data and must not be translated.
        monkeypatch.setattr(profiler, "HAS_PDF", True)

        def raise_catalog_key_from_pdf_reader(_filepath):
            raise RuntimeError("Kein Zielordner angegeben")

        monkeypatch.setattr(profiler, "PdfReader", raise_catalog_key_from_pdf_reader)
        pdf_processor = profiler.BatchProcessor(
            [filename], "pdf_encrypt", {"password": "test-only"}
        )
        pdf_logs = []
        pdf_completed = []
        pdf_processor.log_message.connect(pdf_logs.append)
        pdf_processor.file_completed.connect(
            lambda name, success, result: pdf_completed.append((name, success, result))
        )
        pdf_processor.run()
        assert pdf_completed == [(filename, False, "Kein Zielordner angegeben")]
        assert profiler._render_ui_message(pdf_logs[0]) == (
            f"✗ {filename} — Kein Zielordner angegeben"
        )

        cancelled_processor = profiler.BatchProcessor([filename], "copy", {})
        cancelled_processor.cancel()
        cancelled_logs = []
        cancelled_processor.log_message.connect(cancelled_logs.append)
        cancelled_processor.run()
        assert profiler._render_ui_message(cancelled_logs[0]) == (
            "⚠️ Processing canceled"
        )

        profiler.configure_compact_picker_button(
            button,
            tooltip="Zielordner auswählen",
            accessible_name="Zielordner auswählen",
            accessible_description="Öffnet den Dialog zur Auswahl des optionalen Zielordners.",
        )
        assert button.toolTip() == "Select destination folder"
        assert button.accessibleName() == "Select destination folder"
        assert button.accessibleDescription() == (
            "Opens a dialog to select the optional destination folder."
        )

        translator.set_language("es")
        profiler._retranslate_registered_ui(app)
        assert profiler._render_ui_message(message) == (
            "Analizando: Zielordner auswählen (2/5)"
        )
        assert profiler._render_ui_message(batch_logs[0]) == (
            f"✗ {filename} — No se indicó una carpeta de destino"
        )
        assert batch_dialog.status_label.text() == f"Procesando 1/1: {filename}"
        batch_dialog._on_log(batch_logs[0])
        assert batch_dialog.log_text.toPlainText().splitlines()[-1] == (
            f"✗ {filename} — No se indicó una carpeta de destino"
        )
        assert button.toolTip() == "Seleccionar carpeta de destino"

        translator.set_language("ja")
        profiler._retranslate_registered_ui(app)
        assert profiler._render_ui_message(batch_logs[0]) == (
            f"✗ {filename} — 保存先フォルダーが指定されていません"
        )
        assert batch_dialog.status_label.text() == f"処理中 1/1: {filename}"
        assert button.toolTip() == "保存先フォルダーを選択"
        dialog = profiler.PDFPasswordDialog(["one.pdf", "two.pdf"], mode="encrypt")
        info = next(
            label.text()
            for label in dialog.findChildren(profiler.QLabel)
            if "暗号化用のパスワード" in label.text()
        )
        assert info.startswith("2 個のファイルを選択しました")
    finally:
        if dialog is not None:
            dialog.close()
            dialog.deleteLater()
        if "batch_dialog" in locals():
            batch_dialog.close()
            batch_dialog.deleteLater()
        button.deleteLater()
        app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
        if previous_translator is None:
            if hasattr(app, "_profiler_ui_translator"):
                delattr(app, "_profiler_ui_translator")
        else:
            app._profiler_ui_translator = previous_translator
