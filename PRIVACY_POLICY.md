# Privacy Policy - ProFiler Suite

Stand: 2026-06-12

## Deutsch

ProFiler Suite arbeitet lokal auf dem Gerät des Nutzers. Die Anwendung lädt
Dateien, Dokumentinhalte, OCR-Ergebnisse, SQLite-Indizes oder Workspace-Exporte
nicht an einen eigenen ProFiler-Server hoch.

### Lokal verarbeitete Daten

- lokale Ordner, Dateinamen, Metadaten und Vorschaudaten
- SQLite-Indizes für Suche, Versionen und Duplikaterkennung
- OCR-Ergebnisse über Tesseract
- PDF-Arbeitsstände und Redaktionsläufe, optional mit PyMuPDF
- UI- und Tool-Einstellungen unter `%LOCALAPPDATA%\ProFilerSuite`
- redigierte Workspace-Exporte wie `profiler-workspace-v1.json`

### Keine Standard-Telemetrie

- keine Pflicht-Cloud
- keine Werbe-IDs
- keine eingebaute Nutzerverfolgung
- kein automatischer Upload privater Dokumente

### Externe Komponenten

ProFiler kann lokale Drittkomponenten wie PyMuPDF, Tesseract, pdf2image,
watchdog oder ReportLab verwenden. Diese Bibliotheken laufen im lokalen Prozess
des Nutzers. Lizenzdetails stehen in `THIRD_PARTY_LICENSES.txt`.

### Support

Support-Kanäle und Hinweise zum anonymisierten Fehlerbericht stehen in
`SUPPORT.md`.

---

## English

ProFiler Suite processes user data locally on the user's device. The
application does not upload files, document contents, OCR results, SQLite
indexes, or workspace exports to a dedicated ProFiler service.

### Data processed locally

- local folders, filenames, metadata, and preview data
- SQLite indexes for search, versions, and duplicate detection
- OCR results through Tesseract
- PDF workflows and redaction runs, optionally with PyMuPDF
- UI and tool settings under `%LOCALAPPDATA%\ProFilerSuite`
- redacted workspace exports such as `profiler-workspace-v1.json`

### No default telemetry

- no mandatory cloud
- no advertising identifiers
- no built-in user tracking
- no automatic upload of private documents

### External components

ProFiler may use local third-party components such as PyMuPDF, Tesseract,
pdf2image, watchdog, and ReportLab. These libraries run locally on the user's
machine. License details are documented in `THIRD_PARTY_LICENSES.txt`.
