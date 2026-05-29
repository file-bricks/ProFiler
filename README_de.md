# ProFiler Suite

[English](README.md) | [GitHub](https://github.com/file-bricks/ProFiler)

ProFiler Suite ist ein lokaler Desktop-Dateimanager für private Dokumentensammlungen. Die App verbindet Volltext-Indexierung, OCR, PDF-Werkzeuge, Duplikatenerkennung, Datenschutzprüfungen und eine optionale ProSync-Anbindung in einer Windows-orientierten PySide6-Oberfläche.

ProFiler richtet sich an Menschen, die viele lokale Dokumente verwalten und Suche, Vorschau, PDF-Verarbeitung und Datenschutz-Workflows nutzen möchten, ohne Dateien in einen Cloud-Dienst hochzuladen.

## Highlights

- Lokaler SQLite-Dateiindex für Ordner, Sammlungen und versionierte Dateieinträge
- Volltextsuche über PDF, DOCX, TXT, RTF, Bilder, Tabellen und Code-Dateien
- OCR-Workflow für gescannte PDFs und Bilddokumente mit Tesseract
- PDF-Werkzeuge für Verschlüsselung, Entschlüsselung, Seitenauszüge, OCR, Textextraktion und Export
- Duplikat- und Versionsverwaltung über SHA-256-Dateifingerprints
- Datenschutzampel zum Auffinden potenziell sensibler Dateien vor Weitergabe oder Archivierung
- Erkennung von Cloud-Platzhaltern für OneDrive-ähnliche lokale Bibliotheken
- Optionaler ProSync-Companion für Ordner-Synchronisationsworkflows
- Desktop-GUI mit Dark-/Light-Theme und System-Tray-Integration
- Enthaltene Hilfswerkzeuge für SQLite-Prüfung und Excel-Import

## Screenshot

![ProFiler Suite Desktop-Dateimanager mit Filtern, Dateisuche, Sammlungen und Vorschau-Bereichen](screenshots/main.png)

## Wann ProFiler passt

ProFiler ist nützlich für:

- durchsuchbare lokale Archive aus PDFs, Office-Dokumenten, Textdateien und gescannten Unterlagen
- OCR-gestützte Dokumentenindexierung ohne gehosteten SaaS-Dienst
- Dateiaufräumen, Duplikaterkennung und Versionsprüfung über mehrere Ordner
- PDF-Bearbeitung für kleinere Büro-Workflows
- Datenschutzprüfung vor Versand, Export oder Veröffentlichung von Dokumentenpaketen
- eine Desktop-Zentrale neben Werkzeugen wie ProSync und SQLiteViewer

## Schnellstart

```bash
pip install -r requirements.txt
python Profiler_Suite_V15.py
```

Unter Windows kann die App auch so gestartet werden:

```bat
START.bat
```

## Voraussetzungen

- Python 3.8+
- PySide6
- Tesseract OCR für OCR-Funktionen
- optionale PDF-/OCR-Bibliotheken aus `requirements.txt`

OCR benötigt [Tesseract](https://github.com/tesseract-ocr/tesseract). Der Pfad kann in `profiler_config.json` gesetzt werden, falls die portable Kopie oder Systeminstallation nicht automatisch erkannt wird.

## Konfiguration

| Datei | Zweck |
|---|---|
| `profiler_config.json` | Hauptpfade, OCR-Einstellungen und Index-Konfiguration |
| `profiler_settings.json` | UI-Einstellungen, Theme und optionaler `prosync_path` |
| `search_config.json` | Suchdatenbanken, Filter und Suchoptionen |

## Enthaltene Werkzeuge

| Tool | Zweck |
|---|---|
| `Profiler_Suite_V15.py` | Hauptanwendung |
| `ProFiler_Datenschutzampel.py` | Eigenständige Datenschutzampel |
| `SQLiteViewer.py` | SQLite-Datenbankviewer für Indexprüfung |
| `import_excel_to_profiler.py` | Excel-Import für bestehende Dateilisten |
| `indent_gui_checker.py` | GUI-Einrückungsprüfung für Wartung |

## Unterstützte Formate

| Kategorie | Formate |
|---|---|
| Dokumente | PDF, DOCX, TXT, RTF |
| Bilder | PNG, JPG, TIFF mit OCR-Unterstützung |
| Tabellen | XLSX, XLS, CSV |
| Weitere Dateien | Indexierung nach Metadaten und Dateikategorie |

## ProFiler und KnowledgeDigest

Wenn du Volltextsuche mit BM25-Ranking, LLM-Zusammenfassungen oder einen Web-Viewer für Dokumente suchst, siehe [KnowledgeDigest](https://github.com/file-bricks/knowledgedigest), eine portable Wissensdatenbank vom selben Autor.

| | ProFiler | KnowledgeDigest |
|---|---|---|
| Fokus | Dateiverwaltung, PDF-Werkzeuge, OCR, Datenschutz | Wissenssuche, Chunking, LLM-Zusammenfassungen |
| Suche | Multi-DB, Typ-/Größen-/Datumsfilter | FTS5 mit BM25-Ranking und Snippets |
| PDF | Verschlüsseln, entschlüsseln, extrahieren, schwärzen, OCR | Read-only-Textextraktion |
| Datenschutz | Anonymisierung, Schwärzung, Clipboard-Schutz | Nicht der Fokus |
| KI | Nicht der Fokus | LLM-Zusammenfassungen und Keyword-Extraktion |
| Oberflächen | Desktop-GUI, System-Tray | Desktop-GUI, Web-Viewer, CLI, Python-API |
| Lizenz | AGPL-3.0 | MIT |

## Datenschutz- und Schwärzungshinweis

ProFiler unterstützt Datenschutz-Workflows, Schwärzung und Anonymisierung, garantiert aber keine vollständige Entfernung sensibler Informationen. Erzeugte Dateien müssen vor Weitergabe oder Veröffentlichung immer manuell geprüft werden.

## Lizenz

ProFiler Suite steht unter AGPL-3.0. Siehe [LICENSE](LICENSE).

Dieses Projekt verwendet unter anderem PySide6 und PyMuPDF; siehe `requirements.txt` und `THIRD_PARTY_LICENSES.txt`.

