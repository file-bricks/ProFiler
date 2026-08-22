# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Beholfen / Fixed (2026-08-23)
- **Bugsweep — Companion Module Path Normalization (`module_registry.py`)**: `ModuleRegistry._detect_one` verwendet nun die kanonische Pfadnormalisierung `normalize_configured_tool_path` (inkl. Windows `%VAR%`-Umgebungsvariablen- und `~`-Tilde-Expansion sowie Whitespace-Bereinigung), sodass konfigurierte Begleitwerkzeugpfade in den Einstellungen und im Modul-Statusdialog fehlerfrei aufgelöst werden. 3 neue Regressionstests in `tests/test_module_registry.py` hinzugefügt (144/144 Tests 100% grün).

### Hinzugefügt / Added (2026-08-21)
- **Cross-Platform macOS & Linux Platform Smokes:** Dedizierte Plattform-Smoke-Testsuiten (`tests/macos_platform_smoke.py` und `tests/linux_platform_smoke.py`) mit je 8 reproduzierbaren Plattform-Checks implementiert (POSIX/XDG App-Pfade, Legacy-Fallback, Offscreen PySide6 UnifiedMainWindow, plattform-spezifische Dateimanager-Öffner via `open`/`open -R` und `xdg-open`, Sibling-Launcher-Skriptaufrufe, BOM-freier Workspace-Export ohne Secrets, SQLite Unicode-Roundtrip, Graceful OCR-Fallback, Tier-2 I18N).
- **Sibling-Launcher POSIX-Unterstützung:** `sibling_launcher.py` um Unterstützung für `.sh` und `.command` Shellskripte sowie POSIX-Subprozess-Starts erweitert.
- **Plattform-Smoke CI Workflow:** `.github/workflows/source-platform-smoke.yml` für `ubuntu-latest` und `macos-latest` um Ausführung der dedizierten Plattform-Smokes und der gesamten Testsuite erweitert.
- **Plattform-Smoke Contract Tests:** `tests/test_platform_smoke_contract.py` integriert; Pytest Testsuite auf 141 Tests (100% grün) ausgebaut.

### Hinzugefügt / Added (2026-08-20)
- **Tier-2 Multi-Language Expansion (I18N):** Vollständige mehrsprachige Lokalisierung (`locales/translations.json`) mit 109 übersetzten UI-Strings über alle 6 Zielsprachen (Deutsch `de`, English `en`, Español `es`, 简体中文 `zh`, 日本語 `ja`, Русский `ru`) mit 100% Abdeckung (0 fehlende Übersetzungen).
- **Settings UI Language Selector:** `SettingsDialog` in `Profiler_Suite_V15.py` um neuen Tab „Allgemein“ mit nativer Oberflächensprachauswahl (`de`, `en`, `es`, `zh`, `ja`, `ru`) und persistenter Konfigurationsspeicherung erweitert.
- **Store-Manifest Parität:** `store_package.json` und `store_package/ProFiler/AppxManifest.xml` um alle 6 Sprachressourcen (`de-DE`, `en-US`, `es-ES`, `zh-CN`, `ja-JP`, `ru-RU`) erweitert.
- **I18N Testsuite:** `tests/test_i18n.py` erweitert um vollständige 6-Sprachen-Paritätsprüfungen, Fallback-Ketten, Namenszuordnungen und Store-Manifest-Validierung (139/139 Tests bestanden).

### Geändert / Changed (2026-08-16)
- **Discoverability & Badges:** Test-Badges in `README.md` und `README_de.md` auf 135 bestandene Tests aktualisiert; Ökosystem- und Geschwisterwerkzeuge-Matrix (`file-bricks`, `doc-bricks`, `dev-bricks`, `open-bricks`) mit Direktverlinkungen integriert.
- **Automatisierte Metadaten- & Manifest-Testsuite:** `tests/test_metadata.py` implementiert zur automatisierten Prüfung von Versionsparität (`version.py`, `pyproject.toml`, `store_package.json`, `AppxManifest.xml`), Dokumentenintegrität, UTF-8-Encoding und LLM-Metadaten (5/5 Tests bestanden).
- **Ruff Linting & Code-Hygiene:** Harmlosen f-String-Präfix in `scripts/check_store_readiness.py` bereinigt, `[tool.ruff.lint]` angepasst (`ruff check` 100% sauber).
- **LLM Context Discovery:** `llms.txt` Last-checked Datum auf `2026-08-16` und Teststand auf 135/135 synchronisiert.

## [15.0.0] - 2026-08-14

### Hinzugefügt / Added
- **Accessibility:** Die zentralen Arbeitsbereiche Dateisuche, Suchergebnisse und Dateivorschau haben nun sprechende Accessible Names, Descriptions und Tooltips. Die kompakte Drei-Spalten-Oberfläche bleibt unverändert.
- **Windows Store Packaging Staging:** `store_package/ProFiler/AppxManifest.xml` mit Identity `Geiger.ProFilerSuite`, Publisher `CN=52596601-BAB4-4F3F-B182-E8F3F273B202`, Version `15.0.0.0`, Capability `runFullTrust` und mehrsprachigen Ressourcen (`de-de`, `en-us`) angelegt.
- **MSIX-Tile- & Icon-Assets:** Vollständiges Multi-Resolution Tile- und Logo-Paket (`icon_44x44.png`, `icon_50x50.png`, `icon_150x150.png`, `icon_310x150.png`, `icon_310x310.png`) unter `store_package/ProFiler/icons/`, `store_assets/` und `assets/icons/` generiert.
- **Store-Screenshots (1920x1080):** Vier hochauflösende Promo-Screenshots unter `screenshots/store/` und `README/screenshots/store/` hinterlegt (`shot-1-library-overview.png`, `shot-2-search-ocr.png`, `shot-3-privacy-traffic-light.png`, `shot-4-pdf-tools.png`).
- **Store Readiness Audit Tool:** `scripts/check_store_readiness.py` als 5-stufiges automatisiertes Audit-Tool ausgebaut (Manifest-Syntax, Tile-Maßhaltigkeit, Keyword-Policies, HTTPS-URLs, Screenshot-Auflösungen; 5/5 Checks PASS).
- **Asset- & Store-Regressionstests:** `tests/test_app_assets.py` neu angelegt und `tests/test_store_materials.py` um Manifest-, Tile-Icon- und Screenshot-Prüfungen erweitert (119/119 Tests 100% grün).

### Geändert / Changed
- `store_package.json`: Sprachen (`de-DE`, `en-US`), Publisher Display, Logo-Pfad und Berechtigungsangaben aktualisiert.
- `STORE_LISTING.md`: Schlagwörter auf maximal 7 Keywords pro Sprache harmonisiert (Policy 10.1.3), bilinguale Texte und Screenshot-Referenzen synchronisiert.
- `WINDOWS_STORE_PREP.md`: Dokumentation um Packaging-Staging, Audit-Ergebnisse und verbleibende externe Partner-Center-Gates aktualisiert.
- `llms.txt`: Last-checked Datum auf 2026-08-14 und Teststand auf 119/119 synchronisiert.

## [Unreleased]

### Geändert / Changed (2026-08-14)
- **I18N foundation:** `TranslationSystem v2.0.0` and the translation scanner support the planned DE/EN/ES/ZH/JA/RU schema with deterministic English-then-German fallbacks. New regression tests protect the language registry, direct Tier-2 values, fallback behavior, new-entry schema, and existing DE/EN translation integrity; reviewed Tier-2 translations remain a separate task.
- **Code-Hygiene & Linting**: Typ-Annotationen, Import-Sortierung und Exceptions in Modulen (`workspace_exchange.py`, `ProFiler_Datenschutzampel.py`, `scripts/build_exclude_scanner.py`, `tests/test_store_materials.py`) via `ruff` bereinigt.
- **Pytest & Packaging-Konfiguration**: `pyproject.toml` um `[tool.pytest.ini_options]` und `[tool.ruff]` erweitert, `scripts/__init__.py` initialisiert. Vollständige Testsuite 114/114 bestanden (100% grün).
- **Dokumentation & Discoverability**: `README.md` & `README_de.md` um Mermaid-Architekturdiagramm (5 Stufen) und Badges (Org, PySide6, Tests, Ecosystem, LLM-Context) erweitert; `llms.txt` auf Stand 2026-08-14 synchronisiert.

### Verifikation / Gate-Status (2026-08-13)
- **TASKPLAN 1381:** Der 6-Check-Source-Smoke und die 112 Tests plus 18 Subtests sind lokal grün; Remote-Run `31529140177` bestätigt Ubuntu/macOS.
- **TASKPLAN 1380:** Poppler-/Tesseract-Bündelung bleibt offen. Die benötigten Runtime-Verzeichnisse fehlen und `build_exe.bat` enthält keinen Bundle-Schritt; Paket-/Installations-OCR-Smoke und MSIX bleiben ausdrücklich ungeprüft.

### Beholfen / Fixed (2026-08-11)
- **Bugsweep Iteration 1 (DATA/REL-PUB_ProFiler)**: Robustere UTF-8-BOM-Dekodierung in `workspace_exchange.py` (`load_workspace`, `_load_json_file`) via `utf-8-sig` sowie Absicherung der Pfad-Resolvierung und Existenzprüfungen in `_build_index_payload` & `_summarize_database` gegen `OSError`/`RuntimeError`. 2 neue Unit-Tests in `test_workspace_exchange.py` hinzugefügt (114/114 Tests grün).

### Sicherheit / Security (2026-08-06)
- `pypdf` auf **6.14.2** angehoben (Pin und untere Schranke). Der erste Wurf pinnte
  6.13.2 — die Version, die zufällig lokal installiert war — und handelte sich damit
  zehn offene Warnungen ein (Endlosschleifen bei nicht terminierten Inline-Bildern,
  Speicherverbrauch bei falschen Bildmaßen, ignorierte Stream-Längen; gepatcht in
  6.13.3, 6.14.0, 6.14.1, 6.14.2). Auch `>=3.9.0` als untere Schranke war zu tief.
  Lehre: bei einem Bibliothekswechsel die aktuell sichere Version nachschlagen,
  nicht die gerade greifbare übernehmen.

### Sicherheit / Security (2026-08-05)
- Wechsel von `PyPDF2` auf den gepflegten Nachfolger `pypdf`. PyPDF2 ist
  eingestellt: die offene Warnung GHSA-4vvm-4w3v-6mr8
  (Endlosschleife bei einem Kommentar ohne folgendes Zeichen, betrifft
  2.2.0–3.0.1) hat dort **keine** korrigierte Version, ein Versionssprung
  innerhalb von PyPDF2 war also nicht möglich. Die genutzte API
  (`PdfReader`/`PdfWriter`) ist in beiden Bibliotheken identisch; angepasst
  wurden Import, Abhängigkeiten, Nutzerhinweise und `THIRD_PARTY_LICENSES.txt`.
  112/112 Tests grün — der PDF-OCR-Test lief erstmals wirklich durch, statt am
  fehlenden Import zu scheitern.

### Geändert / Changed (2026-07-27)
- `llms.txt` Last-checked Datum auf 2026-07-27 aktualisiert (112/112 Unit-Tests verifiziert 100% grün).
- Technische Hygiene & Maintenance Check durchgeführt (Pfad A automation gemini/antigravity).

### Geändert / Changed (2026-07-25)
- `llms.txt` aktualisiert (Stand 2026-07-25, 112/112 bestandene Unit-Tests vermerkt).
- KI/LLM-Integrationshinweis (`> [!NOTE]`) in `README.md` und `README_de.md` eingebunden.

### Hinzugefügt / Added
- `build_exe.bat`: Fail-closed PyInstaller-Build aus einem sauberen Git-Checkout mit gepinnten Abhängigkeiten, repository-lokalem Exclude-Scanner, Windows-VersionInfo, SHA-256 und `BUILD-PROVENANCE.json`; Ausgabe ausschließlich unter `C:\_Local_DEV\codex_build\profiler`.
- `version.py`: kanonischer Versionsvertrag `15.0.0` für Laufzeit, Workspace, Build und Store-Material.
- `PLATFORM_SUPPORT.md`: enge Evidenzgrenze des Ubuntu-/macOS-Basis-Smokes.
- `sibling_launcher.py`: Modulares Modul zum Auffinden und Starten von ProFiler-Geschwister-Anwendungen. Kapselt `normalize_configured_tool_path`, `resolve_prosync_launch_path`, `launch_tool_process`, `launch_prosync` und das generische `launch_sibling`. Keine PySide6-Abhängigkeit; ProFiler läuft vollständig weiter wenn ProSync nicht vorhanden ist. Ergebnis-API über `LaunchOutcome`/`LaunchResult`.
- `tests/test_sibling_launcher.py`: 26 Unit-Tests für alle öffentlichen Funktionen von `sibling_launcher.py` (Mock-basiert, kein echter Subprozess, kein PySide6-Import nötig).
- `github_installer.py`: Fail-closed GitHub-Modulinstaller mit HTTPS-/Hostbindung, verpflichtendem SHA-256, Download-/Archivgrenzen, Traversal-/Sonderdatei-/Kollisionsschutz, Staging und Überschreibungsverbot.
- `tests/test_github_installer.py`: 19 Unit-Tests (Mock-basiert, netzwerkfrei): `fetch_latest_release` Success/404/500/Auth-Header, `find_zip_asset` explicit-ZIP/zipball-Fallback, `extract_zip_to_sibling` mit/ohne GitHub-Präfix + Verzeichnisanlage, `install_module` Error-Handling, Strukturtests GITHUB_REPOS vs. `_KNOWN`.
- `module_registry.py`: `ModuleRegistry` erkennt fünf Begleitmodule nur über explizite Konfiguration, das gleiche Verzeichnis oder den fest benannten Geschwisterordner; beliebige Geschwister werden nicht ausgeführt.
- `MODULE_STRATEGY.md`: Dokumentiert Erkennungsprinzip, Installations-/Aktualisierungswege (manuell, Sibling-Konvention, GitHub-Installer-Roadmap) und Erweiterungs-Anleitung für neue Module.
- Einstellungen → Externe Tools: neue „Modul-Status"-Gruppe zeigt Ampelindikator (✓/✗) für jedes Begleitmodul mit Pfadangabe oder Hilfehinweis.
- `tests/test_module_registry.py`: 12 Tests für `ModuleInfo`, `ModuleRegistry` und `get_by_filename()`.
- `source_platform_smoke.py`: 6-Check-Smoke (stdlib, PySide6, workspace_exchange, SQLite CRUD, Umlaut-Roundtrip, headless UnifiedMainWindow offscreen) für macOS/Linux-CI.
- `.github/workflows/source-platform-smoke.yml`: CI-Job auf ubuntu-latest und macos-latest.
- ProSync kann aus dem Tools-Menü optional gestartet werden.
- `README_de.md` als separate deutsche README und `llms.txt` als maschinenlesbarer Projektkontext ergänzt.
- Redigierter Workspace-Austausch über `profiler-workspace-v1.json` mit Menüaktionen für Export und Import ergänzt.
- `pyproject.toml` zur Standardisierung der Paketmetadaten und Abhängigkeiten angelegt.
- Windows-Store-Basismaterialien ergänzt: `store_package.json`, `STORE_LISTING.md`, `PRIVACY_POLICY.md`, `SUPPORT.md`, `WINDOWS_STORE_PREP.md` und `scripts/check_store_readiness.py`.
- Neue Tests `tests/test_app_paths.py` und `tests/test_store_materials.py` für App-Datenpfade und Store-Materialien.
