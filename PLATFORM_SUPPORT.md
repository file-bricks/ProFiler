# Plattformnachweis – ProFiler Suite

Stand: 2026-08-13 (Verifikation)

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

## Verifikation 2026-08-13

- Lokaler Checkout `003988e`: `python -m pytest -q` meldet **112 passed** und
  **18 Subtests passed**; `python source_platform_smoke.py` besteht mit **6/6**.
  Vorhandene fremde Änderungen an `llms.txt` und die ungetrackte
  `BEFUNDE.md` wurden dabei nicht verändert.
- Remote-`master` steht inzwischen auf `7d3ee66`; der
  [GitHub-Actions-Run 31529140177](https://github.com/file-bricks/ProFiler/actions/runs/31529140177)
  ist für `ubuntu-latest` und `macos-latest` erfolgreich. Beide Matrix-Jobs
  installieren PySide6 und führen den 6-Check-Smoke aus; die Linux-
  Systemabhängigkeiten werden nur auf Ubuntu installiert.
- Diese Verifikation bestätigt ausschließlich den Basis-Source-Smoke. Die
  Poppler-/Tesseract-Bündelung, OCR/PDF-Installations-Smokes und native
  PyInstaller-/MSIX-Paketierung bleiben ein separates, offenes Gate.

## Nicht durch den Basis-Smoke belegt

- Tesseract- oder Poppler-Erkennung
- OCR- und PDF-Funktionen
- natives Tray- und Dateiöffner-Verhalten
- PyInstaller-, macOS- oder Linux-Paketierung
- Windows-MSIX, Signatur, Installation oder WACK
- reale Dokument-, Geräte- oder Store-Abnahme

Diese Grenzen dürfen in README, Release Notes und Store-Material nicht als
erledigte Plattformunterstützung ausgegeben werden.
