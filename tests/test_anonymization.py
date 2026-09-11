import ast
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import (
    QApplication,
    QDialogButtonBox,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTabWidget,
)

import Profiler_Suite_V15 as profiler

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class MockSettings:
    def __init__(self, initial=None):
        self.data = dict(initial or {})

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value


def test_anonymization_dialog_accessibility_and_tooltips():
    app = QApplication.instance() or QApplication([])
    settings = MockSettings({
        "anonymization_blacklist": ["Geheim", "Vertraulich"],
        "anonymization_whitelist": ["Öffentlich"],
        "anonymization_placeholder": "[ZENSIERT]",
    })

    dialog = profiler.AnonymizationSettingsDialog(settings)

    assert dialog.windowTitle() == "Anonymisierungs-Einstellungen"
    assert dialog.accessibleName() == "Anonymisierungs-Einstellungen"
    assert "Verwaltung von Blacklist" in dialog.accessibleDescription()

    tabs = dialog.findChild(QTabWidget)
    assert tabs is not None
    assert tabs.count() == 2
    assert tabs.tabText(0) == "Blacklist"
    assert tabs.tabText(1) == "Whitelist"
    assert tabs.accessibleName() == "Anonymisierungs-Kategorien"

    # Blacklist tab widgets
    assert dialog.blacklist_input.accessibleName() == "Blacklist-Begriffeingabe"
    assert "Blacklist" in dialog.blacklist_input.accessibleDescription()
    assert dialog.blacklist_input.toolTip() != ""

    assert dialog.blacklist_widget.accessibleName() == "Blacklist-Begriffsliste"
    assert dialog.blacklist_widget.count() == 2

    # Whitelist tab widgets
    assert dialog.whitelist_input.accessibleName() == "Whitelist-Begriffeingabe"
    assert "Whitelist" in dialog.whitelist_input.accessibleDescription()
    assert dialog.whitelist_input.toolTip() != ""

    assert dialog.whitelist_widget.accessibleName() == "Whitelist-Begriffsliste"
    assert dialog.whitelist_widget.count() == 1

    # Placeholder input
    assert dialog.placeholder_input.accessibleName() == "Anonymisierungs-Platzhalter"
    assert dialog.placeholder_input.text() == "[ZENSIERT]"
    assert dialog.placeholder_input.toolTip() != ""

    dialog.close()
    app.quit()


def test_anonymization_dialog_add_and_remove_blacklist():
    app = QApplication.instance() or QApplication([])
    settings = MockSettings()
    dialog = profiler.AnonymizationSettingsDialog(settings)

    assert dialog.blacklist_widget.count() == 0

    # Add word
    dialog.blacklist_input.setText("  Geheimdaten  ")
    dialog.add_to_blacklist()
    assert dialog.blacklist_widget.count() == 1
    assert dialog.blacklist_widget.item(0).text() == "Geheimdaten"
    assert dialog.blacklist == ["Geheimdaten"]

    # Duplicate should not be added
    dialog.blacklist_input.setText("Geheimdaten")
    dialog.add_to_blacklist()
    assert dialog.blacklist_widget.count() == 1

    # Empty string should not be added
    dialog.blacklist_input.setText("   ")
    dialog.add_to_blacklist()
    assert dialog.blacklist_widget.count() == 1

    # Remove selected
    dialog.blacklist_widget.item(0).setSelected(True)
    dialog.remove_from_blacklist()
    assert dialog.blacklist_widget.count() == 0
    assert dialog.blacklist == []

    dialog.close()
    app.quit()


def test_anonymization_dialog_add_and_remove_whitelist():
    app = QApplication.instance() or QApplication([])
    settings = MockSettings()
    dialog = profiler.AnonymizationSettingsDialog(settings)

    assert dialog.whitelist_widget.count() == 0

    # Add word
    dialog.whitelist_input.setText("Freigegeben")
    dialog.add_to_whitelist()
    assert dialog.whitelist_widget.count() == 1
    assert dialog.whitelist_widget.item(0).text() == "Freigegeben"
    assert dialog.whitelist == ["Freigegeben"]

    # Remove selected
    dialog.whitelist_widget.item(0).setSelected(True)
    dialog.remove_from_whitelist()
    assert dialog.whitelist_widget.count() == 0
    assert dialog.whitelist == []

    dialog.close()
    app.quit()


def test_anonymization_dialog_save_and_cancel_transactionality():
    app = QApplication.instance() or QApplication([])
    settings = MockSettings({
        "anonymization_blacklist": ["Alt1"],
        "anonymization_whitelist": ["AltW"],
        "anonymization_placeholder": "[ALT]",
    })

    # Test Cancel (reject) leaves settings intact
    dialog_cancel = profiler.AnonymizationSettingsDialog(settings)
    dialog_cancel.blacklist_input.setText("Neu1")
    dialog_cancel.add_to_blacklist()
    dialog_cancel.placeholder_input.setText("[NEU]")
    dialog_cancel.reject()

    assert settings.get("anonymization_blacklist") == ["Alt1"]
    assert settings.get("anonymization_placeholder") == "[ALT]"

    # Test Save (save_and_close) commits changes
    dialog_save = profiler.AnonymizationSettingsDialog(settings)
    dialog_save.blacklist_input.setText("NeuB")
    dialog_save.add_to_blacklist()
    dialog_save.whitelist_input.setText("NeuW")
    dialog_save.add_to_whitelist()
    dialog_save.placeholder_input.setText("[NEU_PLATZHALTER]")
    dialog_save.save_and_close()

    assert "NeuB" in settings.get("anonymization_blacklist")
    assert "NeuW" in settings.get("anonymization_whitelist")
    assert settings.get("anonymization_placeholder") == "[NEU_PLATZHALTER]"

    dialog_cancel.close()
    dialog_save.close()
    app.quit()


def test_anonymization_dialog_clear_list_with_confirmation():
    app = QApplication.instance() or QApplication([])
    settings = MockSettings({
        "anonymization_blacklist": ["Eintrag1", "Eintrag2"],
    })
    dialog = profiler.AnonymizationSettingsDialog(settings)
    assert dialog.blacklist_widget.count() == 2

    # Reject confirmation
    with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No):
        dialog.clear_list("blacklist")
    assert dialog.blacklist_widget.count() == 2

    # Accept confirmation
    with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
        dialog.clear_list("blacklist")
    assert dialog.blacklist_widget.count() == 0
    assert dialog.blacklist == []

    dialog.close()
    app.quit()


def test_anonymization_dialog_import_and_export_txt():
    app = QApplication.instance() or QApplication([])
    settings = MockSettings()
    dialog = profiler.AnonymizationSettingsDialog(settings)

    with tempfile.TemporaryDirectory() as tmpdir:
        import_path = Path(tmpdir) / "import_terms.txt"
        import_path.write_text("Alpha\nBeta\nGamma\nBeta\n", encoding="utf-8")

        # Import
        with (
            patch("PySide6.QtWidgets.QFileDialog.getOpenFileName", return_value=(str(import_path), "Text")),
            patch.object(QMessageBox, "information"),
        ):
            dialog.import_list("blacklist")

        assert sorted(dialog.blacklist) == ["Alpha", "Beta", "Gamma"]
        assert dialog.blacklist_widget.count() == 3

        # Export
        export_path = Path(tmpdir) / "exported_terms.txt"
        with (
            patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=(str(export_path), "Text")),
            patch.object(QMessageBox, "information"),
        ):
            dialog.export_list("blacklist")

        assert export_path.exists()
        assert export_path.read_text(encoding="utf-8").strip() == "Alpha\nBeta\nGamma"

    dialog.close()
    app.quit()


def test_settings_dialog_has_anonymization_button_and_handler():
    app = QApplication.instance() or QApplication([])
    settings = MockSettings()
    dialog = profiler.SettingsDialog(settings)

    assert hasattr(dialog, "btn_open_anon")
    assert dialog.btn_open_anon.accessibleName() == "Anonymisierungs-Filter konfigurieren"
    assert "Blacklist" in dialog.btn_open_anon.toolTip()
    assert hasattr(dialog, "open_anonymization_dialog")

    # Verify clicking or calling opens AnonymizationSettingsDialog
    with patch.object(profiler.AnonymizationSettingsDialog, "exec", return_value=1) as mock_exec:
        dialog.open_anonymization_dialog()
        assert mock_exec.called

    dialog.close()
    app.quit()


def test_unified_main_window_has_anonymization_action_and_handler():
    app = QApplication.instance() or QApplication([])
    settings = MockSettings()
    window = profiler.UnifiedMainWindow(settings)

    assert hasattr(window, "show_anonymization_settings")

    # Verify tools menu contains the action
    tools_actions = [action.text() for action in window.menuBar().actions() if "Tools" in action.text()]
    assert len(tools_actions) > 0

    with patch.object(profiler.AnonymizationSettingsDialog, "exec", return_value=1) as mock_exec:
        window.show_anonymization_settings()
        assert mock_exec.called

    window.close()
    app.quit()


def test_export_collection_list_ast_does_not_contain_leaked_dialog_call():
    """Regression test ensuring export_collection_list doesn't leak dialog calls."""
    source_path = PROJECT_ROOT / "Profiler_Suite_V15.py"
    source = source_path.read_text(encoding="utf-8")
    parsed = ast.parse(source)

    export_func = None
    show_anon_func = None

    for node in ast.walk(parsed):
        if isinstance(node, ast.FunctionDef):
            if node.name == "export_collection_list":
                export_func = node
            elif node.name == "show_anonymization_settings":
                # Check the one in SearchWidget (parent class or method)
                show_anon_func = node

    assert export_func is not None, "export_collection_list not found in AST"
    assert show_anon_func is not None, "show_anonymization_settings not found in AST"

    # export_collection_list should NOT call AnonymizationSettingsDialog
    for child in ast.walk(export_func):
        if isinstance(child, ast.Name) and child.id == "AnonymizationSettingsDialog":
            raise AssertionError("export_collection_list still references AnonymizationSettingsDialog!")

    # show_anonymization_settings should NOT be a bare pass/stub
    has_pass = any(isinstance(child, ast.Pass) for child in ast.walk(show_anon_func))
    assert not has_pass, "show_anonymization_settings is still a pass stub!"
