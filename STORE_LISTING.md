# Store Listing - ProFiler Suite

## Deutsch

### Kurzbeschreibung
Lokale Dokumentverwaltung mit Suche, OCR, PDF-Werkzeugen und Datenschutzprüfung.

### Beschreibung
ProFiler Suite ist eine lokale Windows-Desktop-App für private und berufliche
Dokumentbestände. Die Anwendung kombiniert Dateisuche, OCR, PDF-Workflows,
Duplikaterkennung und Datenschutzprüfung in einer Oberfläche, ohne eigene
Cloud-Pflicht oder Upload-Zwang.

**Wichtige Funktionen**

- lokale Volltextsuche über PDFs, Office-Dateien, Bilder, Tabellen und Textdateien
- OCR für Scans und Bilder über Tesseract
- PDF-Werkzeuge für Entschlüsselung, Schwärzung, Seitenextraktion und Export
- Datenschutzampel für sensible Begriffe vor Weitergabe oder Archivierung
- redigierter Workspace-Export für sichere Reviews und Cross-Platform-Smokes
- optionaler Start benachbarter Desktop-Tools wie ProSync und SQLiteViewer

**Windows-Store-Relevanz**

- App-Daten liegen auf Windows unter `%LOCALAPPDATA%\ProFilerSuite`
- die App nutzt `runFullTrust`, weil lokale Ordner, OCR-Tools und Desktop-Workflows
  bewusst außerhalb einer reinen Sandbox laufen
- PyMuPDF und Tesseract werden offen dokumentiert; Lizenz- und Drittanbieterhinweise
  bleiben im Repository, in `THIRD_PARTY_LICENSES.txt` und in der Datenschutzdoku sichtbar
- ProFiler bleibt ein AGPL-3.0-offengelegtes Desktop-Projekt; der Store-Kanal ist
  nur ein Distributionsweg für dieselbe lokale Windows-App

### Datenschutz
https://github.com/file-bricks/ProFiler/blob/main/PRIVACY_POLICY.md

### Support
https://github.com/file-bricks/ProFiler/blob/main/SUPPORT.md

### Schlüsselwörter
Dokumentverwaltung, OCR, PDF, Datenschutz, Suche, lokal, Offline, Dateimanager, Produktivität

### Screenshot-Bedarf
- vorhandener Basisscreenshot: `screenshots/main.png`
- vor Einreichung ergänzen: Suche, PDF-Workflow, Datenschutzampel, Workspace-Export

---

## English

### Short Description
Local document manager with search, OCR, PDF tools, and privacy review.

### Description
ProFiler Suite is a local Windows desktop application for private and
professional document collections. It combines file search, OCR, PDF workflows,
duplicate detection, and privacy review in one interface without requiring a
cloud account or forced upload path.

**Key capabilities**

- local full-text search across PDFs, Office files, images, spreadsheets, and text files
- OCR for scans and image documents via Tesseract
- PDF tools for decryption, redaction, page extraction, and export
- privacy traffic light for sensitive terms before sharing or archiving
- redacted workspace export for secure reviews and cross-platform smoke runs
- optional launcher path to adjacent desktop tools such as ProSync and SQLiteViewer

**Windows Store note**

- app data lives under `%LOCALAPPDATA%\ProFilerSuite` on Windows
- the app uses `runFullTrust` because local folders, OCR tools, and desktop workflows
  intentionally operate outside a sandbox-only model
- PyMuPDF and Tesseract are disclosed in the repository, `THIRD_PARTY_LICENSES.txt`,
  and the privacy documentation
- ProFiler remains an AGPL-3.0 disclosed desktop project; the Store channel is
  only a distribution path for the same local Windows application

### Privacy Policy
https://github.com/file-bricks/ProFiler/blob/main/PRIVACY_POLICY.md

### Support
https://github.com/file-bricks/ProFiler/blob/main/SUPPORT.md
