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

