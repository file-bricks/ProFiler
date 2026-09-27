import os
from types import SimpleNamespace

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


def test_shortcuts_dialog_conformance_and_structure():
    app = QApplication.instance() or QApplication([])
    dialog = profiler.ShortcutsDialog()

    assert dialog.windowTitle() == "Tastaturkürzel & Barrierefreiheit"
    assert dialog.accessibleName() == "Tastaturkürzel & Barrierefreiheit"
    assert "BITV 2.0 / WCAG 2.1 AA" in dialog.accessibleDescription()

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
    assert win.act_shortcuts.text() == "⌨️ Tastaturkürzel & Barrierefreiheit"

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
