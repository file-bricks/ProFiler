# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Hinzugefügt / Added
- `source_platform_smoke.py`: 6-Check-Smoke (stdlib, PySide6, workspace_exchange, SQLite CRUD, Umlaut-Roundtrip, headless UnifiedMainWindow offscreen) für macOS/Linux-CI.
- `.github/workflows/source-platform-smoke.yml`: CI-Job auf ubuntu-latest und macos-latest.
- ProSync kann aus dem Tools-Menü optional gestartet werden.
- `README_de.md` als separate deutsche README und `llms.txt` als maschinenlesbarer Projektkontext ergänzt.
- Redigierter Workspace-Austausch über `profiler-workspace-v1.json` mit Menüaktionen für Export und Import ergänzt.
- `pyproject.toml` zur Standardisierung der Paketmetadaten und Abhängigkeiten angelegt.

### Geändert / Changed
- `profiler_settings.json` um `prosync_path` erweitert.
- Getrackte Beispielkonfigurationen enthalten keine lokalen Benutzerpfade mehr.
- `README.md` auf English-first GitHub-SEO, klare Usecases, PySide6-Positionierung und Discovery-Keywords umgestellt.
- Workspace-Import übernimmt bewusst nur sichere Einstellungen; lokale DB-Pfade bleiben redigiert und werden nicht automatisch reaktiviert.

### Behoben / Fixed
- ProSync wird über Autodetektion, konfigurierte Pfade oder den gemeinsamen Software-Baum gefunden.

## [1.0.0] - YYYY-MM-DD

### Hinzugefügt / Added
- Erstveröffentlichung / Initial release
