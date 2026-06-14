# ProFiler Suite — Modulstrategie

## Überblick

ProFiler Suite besteht aus einer Kernanwendung (`Profiler_Suite_V15.py`) und mehreren
optionalen Begleit-Modulen, die separat bereitgestellt werden:

| Modul | Schlüssel | Hauptdatei |
|---|---|---|
| ProSync | `prosync` | `ProSyncStart_V3.1.py` |
| SQLiteViewer | `sqliteviewer` | `SQLiteViewer.py` |
| Datenschutzampel | `datenschutzampel` | `ProFiler_Datenschutzampel.py` |
| FormConstructor | `formconstructor` | `FormConstructor_V1_5.py` |
| PythonBox | `pythonbox` | `PythonBox.py` |

## Erkennungsstrategie (`module_registry.py`)

Die Klasse `ModuleRegistry` erkennt jedes Modul nach folgendem Prioritätsprinzip:

1. **Konfigurierter Pfad** — vom Benutzer in den Einstellungen eingetragen (höchste Priorität)
2. **Gleiches Verzeichnis** — Modul liegt neben `Profiler_Suite_V15.py`
3. **Geschwister-Verzeichnis** — `../REL-PUB_<Modul>/`
4. **Alle Geschwister** — Breit-Scan aller Ordner neben dem ProFiler-Verzeichnis

```python
from module_registry import ModuleRegistry
from pathlib import Path

registry = ModuleRegistry(
    base_dir=Path(__file__).parent,
    configured_paths={
        "prosync": settings.get("prosync_path", ""),
        "sqliteviewer": settings.get("sqlite_viewer_path", ""),
        "formconstructor": settings.get("formconstructor_path", ""),
        "pythonbox": settings.get("pythonbox_path", ""),
    },
)
if registry.get("prosync").available:
    path = registry.get("prosync").resolved_path
```

## Installations- und Aktualisierungswege

Module können auf drei Wegen bereitgestellt werden:

### A) Manuell (empfohlen für Einzelinstallation)

1. GitHub-Release der gewünschten Komponente herunterladen
2. In ein beliebiges Verzeichnis entpacken
3. ProFiler starten → Einstellungen → Externe Tools → Pfad eintragen
   (oder einfach neben den ProFiler-Ordner legen — wird automatisch erkannt)

### B) Sibling-Konvention (empfohlen für Entwicklungsumgebungen)

Alle Module in Geschwister-Ordner mit Namensschema `REL-PUB_<Modul>` ablegen:

```
.SOFTWARE/DATA/
├── REL-PUB_ProFiler/          ← Kernanwendung
├── REL-PUB_ProSync/
├── REL-PUB_SQLiteViewer/
├── REL-PUB_Datenschutzampel/
└── REL-PUB_FormConstructor/
```

Bei dieser Anordnung erkennt `ModuleRegistry` alle Module ohne manuelle Pfadkonfiguration.

### C) GitHub-Release (zukünftiger Installer)

Geplant: Ein einfacher Launcher/Installer, der fehlende Module direkt aus
`github.com/file-bricks/<Repo>` herunterlädt und in die Sibling-Struktur entpackt.
Voraussetzung: Releases als ZIP/Installer auf GitHub bereitgestellt.

## Modul-Status in der GUI

Im Einstellungsdialog (Einstellungen → Externe Tools → Modul-Status) zeigt ProFiler
für jedes Modul einen Ampelindikator:

- **Grün** (`✓`): Modul gefunden, Pfad verfügbar
- **Rot** (`✗`): Modul nicht gefunden; Hinweis auf manuelle Pfadeingabe oder Download

## Erweiterung um neue Module

`module_registry.py` → `_KNOWN`-Liste um einen Eintrag erweitern:

```python
(
    "neuesmodul",           # key (Kleinbuchstaben, kein Leerzeichen)
    "Neues Modul",          # display_name
    "NeuesModul.py",        # filename (Hauptdatei)
    "REL-PUB_NeuesModul",   # sibling_dir_hint
    [],                     # extra_candidates (z.B. .exe, .bat)
),
```
