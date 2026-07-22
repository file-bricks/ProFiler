# Plattformnachweis – ProFiler Suite

Stand: 2026-07-22

## Produktlinie

Windows Desktop ist die einzige Release- und Store-Produktlinie. Android, iOS
und Web/PWA sind keine Ziele der lokalen Vollanwendung.

## Belegte Basis-Smokes

Die GitHub-Actions-Matrix führt `source_platform_smoke.py` auf
`ubuntu-latest` und `macos-latest` aus. Sie prüft genau sechs Verträge:

1. Python-Standardbibliothek
2. PySide6-Import
3. Workspace-Schema-Import
4. SQLite-CRUD
5. UTF-8-Umlaut-Roundtrip
6. offscreen erzeugtes `UnifiedMainWindow`

Ein grüner Lauf belegt nur diese Basis-Source-Kompatibilität.

## Nicht durch den Basis-Smoke belegt

- Tesseract- oder Poppler-Erkennung
- OCR- und PDF-Funktionen
- natives Tray- und Dateiöffner-Verhalten
- PyInstaller-, macOS- oder Linux-Paketierung
- Windows-MSIX, Signatur, Installation oder WACK
- reale Dokument-, Geräte- oder Store-Abnahme

Diese Grenzen dürfen in README, Release Notes und Store-Material nicht als
erledigte Plattformunterstützung ausgegeben werden.
