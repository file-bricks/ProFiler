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
