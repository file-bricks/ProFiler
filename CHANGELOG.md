# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Geändert / Changed (2026-08-14)
- **Code-Hygiene & Linting**: Typ-Annotationen, Import-Sortierung und Exceptions in Modulen (`workspace_exchange.py`, `ProFiler_Datenschutzampel.py`, `scripts/build_exclude_scanner.py`, `tests/test_store_materials.py`) via `ruff` bereinigt.
- **Pytest & Packaging-Konfiguration**: `pyproject.toml` um `[tool.pytest.ini_options]` und `[tool.ruff]` erweitert, `scripts/__init__.py` initialisiert. Vollständige Testsuite 114/114 bestanden (100% grün).
- **Dokumentation & Discoverability**: `README.md` & `README_de.md` um Mermaid-Architekturdiagramm (5 Stufen) und Badges (Org, PySide6, Tests, Ecosystem, LLM-Context) erweitert; `llms.txt` auf Stand 2026-08-14 synchronisiert.

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

### Geändert / Changed
- `START.bat` startet `ProFiler.exe` nur bei passender benachbarter SHA-256-Datei und verwendet im Quellcheckout sonst `Profiler_Suite_V15.py`.
- `README.md` und `README_de.md` referenzieren den Haupt-Screenshot jetzt policy-konform unter `README/screenshots/main.png` und dokumentieren den lokalen Windows-EXE-Build.
- `find_tool_path()`: Delegiert für bekannte Dateinamen an `ModuleRegistry` statt einfacher same-dir/parent-dir-Prüfung; Fallback bleibt für unbekannte Tool-Namen erhalten.
- `Profiler_Suite_V15.py`: `normalize_configured_tool_path` und `resolve_prosync_launch_path` aus dem Hauptfile nach `sibling_launcher.py` verlagert (kanonische Implementierung dort). GUI-Methode `launch_prosync()` delegiert an `sibling_launcher.launch_prosync()` und wertet `LaunchOutcome` aus. `WINDOWS_ENV_VAR_PATTERN`-Konstante entfernt (in `sibling_launcher` intern).
- Laufzeit-Konfigurationen liegen nur unter AppData; getrackte Dateien heißen eindeutig `*.example.json` und enthalten keine lokalen Benutzerpfade oder Passwortfelder.
- `README.md` auf English-first GitHub-SEO, klare Usecases, PySide6-Positionierung und Discovery-Keywords umgestellt.
- Workspace-Import übernimmt bewusst nur sichere Einstellungen; lokale DB-Pfade bleiben redigiert und werden nicht automatisch reaktiviert.
- Windows-Konfigurationsdateien und Datenschutzampel nutzen für neue Installationen `%LOCALAPPDATA%\ProFilerSuite`; bestehende `~/.profiler_suite`-Dateien bleiben lesbar.
- `THIRD_PARTY_LICENSES.txt` ist jetzt aus direkten Manifesten abgeleitet; die konkrete Build-Umgebung wird artefaktbezogen in der Provenienz erfasst.

### Behoben / Fixed
- `.gitignore` ignoriert jetzt `LOCK*.txt`, `LOCK.permissions.json`, `*.bak` und interne `docs/superpowers/`-Planungsartefakte, damit Privacy- und Wartungsdateien nicht versehentlich ins Repo geraten.
- `Profiler_Suite_V15.py` (Anonymisierungs-Worker): Ausgabedateinamen `_geschwrzt` → `_geschwärzt` korrigiert (3 Stellen); Log-Meldung ergänzt um fehlendes ✅-Emoji und korrekten Umlaut.
- `Profiler_Suite_V15.py` (SearchWidgetHybrid): Hardcodierte Linux-Fallbackpfade `/mnt/project/MethodenAnalyser3.py`, `/mnt/project/Kompilator.py`, `/mnt/project/SQLiteViewer.py` und `/mnt/project/PythonBox.py` entfernt; Tool-nicht-gefunden-Dialog ist jetzt der einzige Fehlerpfad.
- ProSync wird über Autodetektion, konfigurierte Pfade oder den gemeinsamen Software-Baum gefunden.
- PDF-OCR erzeugt nun tatsächlich ein mehrseitiges PDF mit Tesseract-Textebene, statt das Original unverändert als Erfolg zu kopieren.
- PDF-Passwörter bleiben sitzungsbezogen; ältere Klartextschlüssel werden beim Laden aus der JSON-Datei entfernt.
- Excel-Cleanup verlangt einen passenden Eigentumsmarker, arbeitet transaktional und erhält gemeinsam genutzte Datei-/Tag-Datensätze.
- Workspace-Import validiert Größe, Schema-Version, Typen, Settings, Pfad- und Secret-Redaktion vor jeder Mutation.
- Store-Pflichtlinks verwenden den realen Default-Branch `master`; die Materialprüfung grenzt MSIX/WACK/Signing ausdrücklich aus.

## [1.0.0] - Datum nicht dokumentiert

### Hinzugefügt / Added
- Erstveröffentlichung / Initial release
