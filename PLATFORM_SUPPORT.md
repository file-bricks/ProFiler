# Plattformnachweis – ProFiler Suite

Stand: 2026-08-21 (Verifikation & Plattform-Smokes)

## Produktlinie

Windows Desktop ist die primäre Release- und Store-Produktlinie. Android, iOS
und Web/PWA sind keine Ziele der lokalen Vollanwendung.

## Belegte Basis- und Plattform-Smokes

Die Testmatrix und GitHub-Actions-Pipeline führt `source_platform_smoke.py`,
`tests/linux_platform_smoke.py` (auf Ubuntu) und `tests/macos_platform_smoke.py`
(auf macOS) aus.

### 1. Basis-Source-Smoke (6 Checks)
1. Python-Standardbibliothek (pathlib, json, sqlite3)
2. PySide6-Import & Headless-Initialisierung
3. Workspace-Schema-Import (`profiler-workspace-v1`)
4. SQLite-CRUD
5. UTF-8-Umlaut-Roundtrip (JSON UTF-8)
6. Offscreen erzeugtes `UnifiedMainWindow`

### 2. Dedizierte Linux- & macOS-Plattform-Smokes (8 Checks je Plattform)
1. POSIX/macOS/Linux App-Pfade (`app_paths.py`, XDG, Legacy-Fallback `~/.profiler_suite`)
2. Offscreen PySide6 `UnifiedMainWindow`-Erzeugung und Event-Loop-Verhalten (`QT_QPA_PLATFORM=offscreen`)
3. Plattform-spezifische Datei- und Ordneröffner-Pfade (`open` / `open -R` auf Darwin, `xdg-open` auf Linux)
4. Sibling-Launcher für Begleitmodule (.py, .sh, .command)
5. Redigierter Workspace-Export (`profiler-workspace-v1.json`) ohne Secrets und ohne UTF-8 BOM
6. SQLite-CRUD & UTF-8 / Umlaut-Roundtrip
7. Graceful Fallback bei nicht installierten OCR-/PDF-Abhängigkeiten (Tesseract/Poppler)
8. Tier-2 i18n Übersetzungssystem (de, en, es, zh, ja, ru) auf POSIX/macOS/Linux

## Verifikation 2026-08-21

- Vollständige Pytest-Suite: **141 passed**, **18 Subtests passed** (100% grün).
- Basis-Smoke `source_platform_smoke.py`: **6/6 Checks bestanden**.
- macOS-Plattform-Smoke `tests/macos_platform_smoke.py`: **8/8 Checks bestanden**.
- Linux-Plattform-Smoke `tests/linux_platform_smoke.py`: **8/8 Checks bestanden**.
- Plattform-Smoke Contract Tests in `tests/test_platform_smoke_contract.py` integriert.

## Nicht durch die Smokes belegt (Gate-Grenzen)

- Native externe Tesseract- oder Poppler-Binär-Bündelung im Release-Build
- Physische GUI-Rendering- und Native-Tray-Funktionen im Multi-Monitor-Betrieb
- PyInstaller-, macOS- (`.dmg`/`.app`) oder Linux-Paketierung (`.deb`/`.AppImage`)
- Windows-MSIX, Signatur, Store-WACK-Abnahme
- Reale Hardware-, Endgeräte- oder Multi-User-Store-Freigaben
