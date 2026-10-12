#!/usr/bin/env python3
"""
ProFiler Datenschutzampel - System-Tray Tool
Parallel zu ProFiler Suite laufend
Überwacht Zwischenablage auf sensible Daten
Shared Config für Blacklist/Whitelist
"""

import json
import re
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSystemTrayIcon,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app_paths import config_path, resolve_read_path
from translator import install_translator_from_settings


def _ui_text(key: str, **values) -> str:
    app = QApplication.instance()
    translator = getattr(app, "_profiler_ui_translator", None) if app else None
    if translator:
        return translator.translate_ui(key, **values)
    if not values:
        return key
    try:
        return key.format_map(values)
    except (KeyError, ValueError):
        return key


def _ui_message_box(kind: str, parent, title: str, message: str, *args):
    """Show translated standard button labels without reprocessing rendered text."""
    icon = {
        "information": QMessageBox.Icon.Information,
        "warning": QMessageBox.Icon.Warning,
        "critical": QMessageBox.Icon.Critical,
        "question": QMessageBox.Icon.Question,
    }[kind]
    buttons_default = (
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        if kind == "question"
        else QMessageBox.StandardButton.Ok
    )
    buttons = args[0] if args else buttons_default
    default_button = args[1] if len(args) > 1 else QMessageBox.StandardButton.NoButton
    box = QMessageBox(icon, title, message, buttons, parent)
    labels = {
        QMessageBox.StandardButton.Ok: "OK",
        QMessageBox.StandardButton.Yes: "Ja",
        QMessageBox.StandardButton.No: "Nein",
        QMessageBox.StandardButton.Cancel: "Abbrechen",
        QMessageBox.StandardButton.Close: "Schließen",
        QMessageBox.StandardButton.Save: "Speichern",
        QMessageBox.StandardButton.Open: "Öffnen",
        QMessageBox.StandardButton.Discard: "Verwerfen",
        QMessageBox.StandardButton.Retry: "Wiederholen",
        QMessageBox.StandardButton.Ignore: "Ignorieren",
        QMessageBox.StandardButton.Help: "Hilfe",
    }
    for standard_button, key in labels.items():
        if buttons & standard_button:
            button = box.button(standard_button)
            if button is not None:
                button.setText(_ui_text(key))
    if default_button != QMessageBox.StandardButton.NoButton:
        box.setDefaultButton(default_button)
    return QMessageBox.StandardButton(box.exec())

# ============================================================================
# KONFIGURATION
# ============================================================================

CONFIG_PATH = config_path("datenschutzampel.json")
HISTORY_LIMIT = 15

STYLESHEET = """
QMainWindow { background-color: #f0f2f5; }
QTabWidget::pane { border: 1px solid #dcdcdc; background: white; border-radius: 4px; }
QTabBar::tab { 
    background: #e1e4e8; 
    padding: 8px 20px; 
    margin-right: 2px; 
    border-top-left-radius: 4px; 
    border-top-right-radius: 4px; 
    color: #333; 
}
QTabBar::tab:selected { 
    background: white; 
    font-weight: bold; 
    border-bottom: 2px solid #007bff; 
}
QLabel { color: #333; font-size: 14px; }
QLabel#Header { font-size: 18px; font-weight: bold; color: #2c3e50; }
QPushButton { 
    background-color: #ffffff; 
    border: 1px solid #ced4da; 
    border-radius: 4px; 
    padding: 6px 12px; 
    font-size: 13px; 
    color: #495057; 
}
QPushButton:hover { background-color: #e9ecef; border-color: #adb5bd; }
QPushButton#Danger { color: #dc3545; border-color: #dc3545; }
QPushButton#Danger:hover { background-color: #dc3545; color: white; }
QPushButton#Success { color: #28a745; border-color: #28a745; }
QPushButton#Success:hover { background-color: #28a745; color: white; }
QLineEdit, QListWidget, QTextEdit { 
    border: 1px solid #ced4da; 
    border-radius: 4px; 
    padding: 4px; 
    background-color: white; 
    selection-background-color: #007bff; 
}
"""

# ============================================================================
# MAIN APPLICATION
# ============================================================================

class DatenschutzAmpel(QMainWindow):
    """Datenschutz-Ampel für ProFiler Suite"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle(_ui_text("🚦 ProFiler Datenschutzampel"))
        self.resize(900, 650)
        self.setMinimumSize(800, 500)

        # State
        self.sensitive: list[str] = []
        self.whitelist: list[str] = []
        self.clip_history: list[str] = []
        self.patterns: list[re.Pattern] = []

        self.ampel_status = "grün"  # grün, gelb, rot
        self.case_sensitive = False
        self.whole_words = False
        self.clipboard_lock = False

        # UI
        self.init_ui()
        self.setup_tray()

        # Clipboard
        self.clipboard = QApplication.clipboard()

        # Config laden
        self.load_config()
        self.compile_patterns()

        # Clipboard Monitoring
        self.clipboard.dataChanged.connect(self.on_clipboard_change)

        # Styling
        self.setStyleSheet(STYLESHEET)
        self.statusBar().showMessage(_ui_text("Bereit - Ampel: 🟢"))

    def init_ui(self):
        """Initialisiert UI"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        tabs = QTabWidget()

        # Tab 1: Listen
        tab_lists = QWidget()
        self.setup_tab_lists(tab_lists)
        tabs.addTab(tab_lists, _ui_text("📋 Listen (Blacklist/Whitelist)"))

        # Tab 2: Ampel
        tab_ampel = QWidget()
        self.setup_tab_ampel(tab_ampel)
        tabs.addTab(tab_ampel, _ui_text("🚦 Ampel-Steuerung"))

        # Tab 3: Verlauf
        tab_history = QWidget()
        self.setup_tab_history(tab_history)
        tabs.addTab(tab_history, _ui_text("🕘 Verlauf"))

        main_layout.addWidget(tabs)

    def setup_tab_lists(self, tab):
        """Blacklist/Whitelist Verwaltung"""
        layout = QVBoxLayout(tab)

        # Header
        header = QLabel(_ui_text("Listen-Verwaltung"))
        header.setObjectName("Header")
        layout.addWidget(header)

        # Blacklist
        layout.addWidget(QLabel(_ui_text("🚫 Blacklist (Sensible Begriffe):")))

        self.blacklist_widget = QListWidget()
        layout.addWidget(self.blacklist_widget)

        bl_controls = QHBoxLayout()
        self.blacklist_input = QLineEdit()
        self.blacklist_input.setPlaceholderText(_ui_text("Begriff hinzufügen..."))
        btn_add_bl = QPushButton(_ui_text("+ Hinzufügen"))
        btn_add_bl.clicked.connect(self.add_to_blacklist)
        btn_remove_bl = QPushButton(_ui_text("- Entfernen"))
        btn_remove_bl.clicked.connect(self.remove_from_blacklist)

        bl_controls.addWidget(self.blacklist_input)
        bl_controls.addWidget(btn_add_bl)
        bl_controls.addWidget(btn_remove_bl)
        layout.addLayout(bl_controls)

        # Whitelist
        layout.addWidget(QLabel(_ui_text("✅ Whitelist (Ausnahmen):")))

        self.whitelist_widget = QListWidget()
        layout.addWidget(self.whitelist_widget)

        wl_controls = QHBoxLayout()
        self.whitelist_input = QLineEdit()
        self.whitelist_input.setPlaceholderText(_ui_text("Ausnahme hinzufügen..."))
        btn_add_wl = QPushButton(_ui_text("+ Hinzufügen"))
        btn_add_wl.clicked.connect(self.add_to_whitelist)
        btn_remove_wl = QPushButton(_ui_text("- Entfernen"))
        btn_remove_wl.clicked.connect(self.remove_from_whitelist)

        wl_controls.addWidget(self.whitelist_input)
        wl_controls.addWidget(btn_add_wl)
        wl_controls.addWidget(btn_remove_wl)
        layout.addLayout(wl_controls)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_clear_bl = QPushButton(_ui_text("🗑️ Blacklist leeren"))
        btn_clear_bl.setObjectName("Danger")
        btn_clear_bl.clicked.connect(self.clear_blacklist)

        btn_save = QPushButton(_ui_text("💾 Listen speichern"))
        btn_save.setObjectName("Success")
        btn_save.clicked.connect(self.save_config)

        btn_layout.addWidget(btn_clear_bl)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def setup_tab_ampel(self, tab):
        """Ampel-Steuerung"""
        layout = QVBoxLayout(tab)

        # Ampel-Anzeige
        self.ampel_label = QLabel(_ui_text("🟢"))
        self.ampel_label.setStyleSheet("font-size: 72px;")
        self.ampel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.ampel_label)

        self.ampel_text = QLabel(_ui_text("Status: Grün - Alles sicher"))
        self.ampel_text.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.ampel_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.ampel_text)

        layout.addWidget(QLabel(_ui_text("")))

        # Optionen
        self.cb_case_sensitive = QCheckBox(_ui_text("Groß-/Kleinschreibung beachten"))
        self.cb_case_sensitive.stateChanged.connect(self.on_options_changed)
        layout.addWidget(self.cb_case_sensitive)

        self.cb_whole_words = QCheckBox(_ui_text("Nur ganze Wörter"))
        self.cb_whole_words.stateChanged.connect(self.on_options_changed)
        layout.addWidget(self.cb_whole_words)

        self.cb_clipboard_lock = QCheckBox(_ui_text("🔒 Zwischenablage sperren bei Rot"))
        self.cb_clipboard_lock.stateChanged.connect(self.on_options_changed)
        layout.addWidget(self.cb_clipboard_lock)

        layout.addStretch()

        # Manual Override
        manual_layout = QHBoxLayout()
        btn_green = QPushButton(_ui_text("🟢 Auf Grün setzen"))
        btn_green.setObjectName("Success")
        btn_green.clicked.connect(lambda: self.set_ampel_manual("grün"))

        btn_red = QPushButton(_ui_text("🔴 Auf Rot setzen"))
        btn_red.setObjectName("Danger")
        btn_red.clicked.connect(lambda: self.set_ampel_manual("rot"))

        manual_layout.addWidget(btn_green)
        manual_layout.addWidget(btn_red)
        layout.addLayout(manual_layout)

    def setup_tab_history(self, tab):
        """Zwischenablage-Verlauf"""
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel(_ui_text("📋 Letzte Zwischenablage-Einträge:")))

        self.history_widget = QTextEdit()
        self.history_widget.setReadOnly(True)
        layout.addWidget(self.history_widget)

        btn_clear_history = QPushButton(_ui_text("🗑️ Verlauf löschen"))
        btn_clear_history.clicked.connect(self.clear_history)
        layout.addWidget(btn_clear_history)

    def setup_tray(self):
        """System-Tray Icon"""
        self.tray_icon = QSystemTrayIcon(self)
        self.update_tray_icon()

        tray_menu = QMenu(self)
        action_show = tray_menu.addAction(_ui_text("📂 Öffnen"))
        action_show.triggered.connect(self.show)

        tray_menu.addSeparator()
        action_quit = tray_menu.addAction(_ui_text("❌ Beenden"))
        action_quit.triggered.connect(self.force_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_click)
        self.tray_icon.show()

    def update_tray_icon(self):
        """Aktualisiert Tray-Icon basierend auf Ampel-Status"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)

        if self.ampel_status == "rot":
            color = QColor(220, 53, 69)  # Rot
        elif self.ampel_status == "gelb":
            color = QColor(255, 193, 7)  # Gelb
        else:
            color = QColor(40, 167, 69)  # Grün

        painter.setBrush(QBrush(color))
        painter.drawEllipse(4, 4, 56, 56)
        painter.end()

        # FIX: QPixmap zu QIcon konvertieren!
        self.tray_icon.setIcon(QIcon(pixmap))
        self.tray_icon.setToolTip(
            _ui_text(
                "Ampelstatus: {value0}",
                value0=_ui_text(self.ampel_status),
            )
        )

    def on_tray_click(self, reason):
        """Tray-Icon Klick"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def force_quit(self):
        """Wirklich beenden"""
        QApplication.quit()

    def closeEvent(self, event):
        """Minimiert zu Tray"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            _ui_text("Datenschutzampel"),
            _ui_text("Läuft im Hintergrund weiter."),
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    # ========================================================================
    # LISTE-VERWALTUNG
    # ========================================================================

    def add_to_blacklist(self):
        word = self.blacklist_input.text().strip()
        if word and word not in self.sensitive:
            self.sensitive.append(word)
            self.update_blacklist_display()
            self.blacklist_input.clear()
            self.compile_patterns()

    def add_to_whitelist(self):
        word = self.whitelist_input.text().strip()
        if word and word not in self.whitelist:
            self.whitelist.append(word)
            self.update_whitelist_display()
            self.whitelist_input.clear()

    def remove_from_blacklist(self):
        for item in self.blacklist_widget.selectedItems():
            self.sensitive.remove(item.text())
        self.update_blacklist_display()
        self.compile_patterns()

    def remove_from_whitelist(self):
        for item in self.whitelist_widget.selectedItems():
            self.whitelist.remove(item.text())
        self.update_whitelist_display()

    def clear_blacklist(self):
        reply = _ui_message_box(
            "question",
            self,
            _ui_text("Blacklist leeren"),
            _ui_text("Wirklich alle Einträge löschen?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.sensitive.clear()
            self.update_blacklist_display()
            self.compile_patterns()

    def update_blacklist_display(self):
        self.blacklist_widget.clear()
        for word in sorted(self.sensitive):
            self.blacklist_widget.addItem(word)

    def update_whitelist_display(self):
        self.whitelist_widget.clear()
        for word in sorted(self.whitelist):
            self.whitelist_widget.addItem(word)

    def clear_history(self):
        self.clip_history.clear()
        self.history_widget.clear()

    # ========================================================================
    # AMPEL-LOGIK
    # ========================================================================

    def compile_patterns(self):
        """Kompiliert Regex-Patterns aus Blacklist"""
        self.patterns = []
        flags = 0 if self.case_sensitive else re.IGNORECASE

        for word in self.sensitive:
            if self.whole_words:
                pattern = rf"\b{re.escape(word)}\b"
            else:
                pattern = re.escape(word)
            try:
                self.patterns.append(re.compile(pattern, flags))
            except re.error:
                pass

    def on_options_changed(self):
        """Optionen geändert"""
        self.case_sensitive = self.cb_case_sensitive.isChecked()
        self.whole_words = self.cb_whole_words.isChecked()
        self.clipboard_lock = self.cb_clipboard_lock.isChecked()
        self.compile_patterns()

    def on_clipboard_change(self):
        """Zwischenablage hat sich geändert"""
        try:
            text = self.clipboard.text()
            if not text:
                return

            # Zu Verlauf hinzufügen
            self.clip_history.insert(0, text)
            if len(self.clip_history) > HISTORY_LIMIT:
                self.clip_history.pop()
            self.update_history_display()

            # Prüfen
            found_sensitive = []

            for pattern in self.patterns:
                matches = pattern.findall(text)
                if matches:
                    found_sensitive.extend(matches)

            # Whitelist-Check
            found_sensitive = [
                word for word in found_sensitive
                if word.lower() not in [w.lower() for w in self.whitelist]
            ]

            if found_sensitive:
                sensitive_text = ", ".join(set(found_sensitive))
                self.set_ampel(
                    "rot",
                    _ui_text("Sensible Begriffe: {value0}", value0=sensitive_text),
                )

                if self.clipboard_lock:
                    self.clipboard.clear()
                    _ui_message_box(
                        "warning",
                        self,
                        _ui_text("Zwischenablage gesperrt"),
                        _ui_text(
                            "⚠️ Sensible Begriffe erkannt!\n\nZwischenablage wurde geleert:\n{value0}",
                            value0=sensitive_text,
                        ),
                    )
            else:
                self.set_ampel("grün", _ui_text("Keine sensiblen Daten erkannt"))

        except Exception:
            pass

    def set_ampel(self, status, message=""):
        """Setzt Ampel-Status"""
        self.ampel_status = status

        if status == "rot":
            self.ampel_label.setText(_ui_text("🔴"))
            self.ampel_text.setText(_ui_text("Status: ROT - {value0}", value0=message))
            self.statusBar().showMessage(_ui_text("⚠️ ROT: {value0}", value0=message))
        elif status == "gelb":
            self.ampel_label.setText(_ui_text("🟡"))
            self.ampel_text.setText(_ui_text("Status: GELB - {value0}", value0=message))
            self.statusBar().showMessage(_ui_text("⚠️ GELB: {value0}", value0=message))
        else:
            self.ampel_label.setText(_ui_text("🟢"))
            self.ampel_text.setText(_ui_text("Status: GRÜN - {value0}", value0=message))
            self.statusBar().showMessage(_ui_text("✅ GRÜN: {value0}", value0=message))

        self.update_tray_icon()

    def set_ampel_manual(self, status):
        """Manuelles Setzen der Ampel"""
        self.set_ampel(status, _ui_text("Manuell gesetzt"))

    def update_history_display(self):
        """Aktualisiert Verlaufs-Anzeige"""
        text = "\n\n".join([
            f"[{i+1}] {entry[:200]}{'...' if len(entry) > 200 else ''}"
            for i, entry in enumerate(self.clip_history)
        ])
        self.history_widget.setPlainText(text)

    # ========================================================================
    # CONFIG
    # ========================================================================

    def load_config(self):
        """Lädt Konfiguration"""
        read_path = resolve_read_path(CONFIG_PATH.name)
        if read_path.exists():
            try:
                with open(read_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.sensitive = data.get('blacklist', [])
                self.whitelist = data.get('whitelist', [])
                self.case_sensitive = data.get('case_sensitive', False)
                self.whole_words = data.get('whole_words', False)
                self.clipboard_lock = data.get('clipboard_lock', False)

                self.update_blacklist_display()
                self.update_whitelist_display()

                self.cb_case_sensitive.setChecked(self.case_sensitive)
                self.cb_whole_words.setChecked(self.whole_words)
                self.cb_clipboard_lock.setChecked(self.clipboard_lock)
            except (OSError, json.JSONDecodeError):
                pass

    def save_config(self):
        """Speichert Konfiguration"""
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'blacklist': self.sensitive,
            'whitelist': self.whitelist,
            'case_sensitive': self.case_sensitive,
            'whole_words': self.whole_words,
            'clipboard_lock': self.clipboard_lock
        }

        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        _ui_message_box(
            "information",
            self,
            _ui_text("Gespeichert"),
            _ui_text("✅ Konfiguration gespeichert:\n{value0}", value0=CONFIG_PATH),
        )


# ============================================================================
# MAIN
# ============================================================================

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Wichtig für Tray!
    install_translator_from_settings(app, app_dir=Path(__file__).resolve().parent)

    window = DatenschutzAmpel()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
