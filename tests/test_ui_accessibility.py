import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

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
