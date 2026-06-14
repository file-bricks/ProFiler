# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Hinzugefügt / Added
- `module_registry.py`: `ModuleRegistry`-Klasse erkennt alle 5 ProFiler-Suite-Begleitmodule (ProSync, SQLiteViewer, Datenschutzampel, FormConstructor, PythonBox) über konfigurierte Pfade, gleiches Verzeichnis, Geschwisterordner und Breit-Scan. `get_by_filename()` ermöglicht Dateiname-Lookup.
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
- `find_tool_path()`: Delegiert für bekannte Dateinamen an `ModuleRegistry` statt einfacher same-dir/parent-dir-Prüfung; Fallback bleibt für unbekannte Tool-Namen erhalten.
- `profiler_settings.json` um `prosync_path` erweitert.
- Getrackte Beispielkonfigurationen enthalten keine lokalen Benutzerpfade mehr.
- `README.md` auf English-first GitHub-SEO, klare Usecases, PySide6-Positionierung und Discovery-Keywords umgestellt.
- Workspace-Import übernimmt bewusst nur sichere Einstellungen; lokale DB-Pfade bleiben redigiert und werden nicht automatisch reaktiviert.
- Windows-Konfigurationsdateien und Datenschutzampel nutzen für neue Installationen `%LOCALAPPDATA%\ProFilerSuite`; bestehende `~/.profiler_suite`-Dateien bleiben lesbar.

### Behoben / Fixed
- `Profiler_Suite_V15.py` (Anonymisierungs-Worker): Ausgabedateinamen `_geschwrzt` → `_geschwärzt` korrigiert (3 Stellen); Log-Meldung ergänzt um fehlendes ✅-Emoji und korrekten Umlaut.
- `Profiler_Suite_V15.py` (SearchWidgetHybrid): Hardcodierte Linux-Fallbackpfade `/mnt/project/MethodenAnalyser3.py`, `/mnt/project/Kompilator.py`, `/mnt/project/SQLiteViewer.py` und `/mnt/project/PythonBox.py` entfernt; Tool-nicht-gefunden-Dialog ist jetzt der einzige Fehlerpfad.
- ProSync wird über Autodetektion, konfigurierte Pfade oder den gemeinsamen Software-Baum gefunden.

## [1.0.0] - YYYY-MM-DD

### Hinzugefügt / Added
- Erstveröffentlichung / Initial release
