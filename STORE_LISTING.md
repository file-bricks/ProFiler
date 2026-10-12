# Store Listing Draft - ProFiler Suite

**Status:** draft only; no Store submission or publication is claimed. The source version remains frozen at `15.0.2`.

## Deutsch

### Kurzbeschreibung

Lokale Dokumentverwaltung mit Suche, OCR, PDF-Werkzeugen und einer regelbasierten Prüfung möglicher sensibler Begriffe.

### Beschreibung

ProFiler Suite ist eine Windows-orientierte Desktopanwendung für lokale Datei- und Dokumentabläufe. Sie kombiniert Dateisuche, OCR, PDF-Werkzeuge, Duplikaterkennung und Hinweise auf möglicherweise sensible Begriffe.

**Funktionen**

- Suche in ausgewählten lokalen Ordnern und Dokumenten
- OCR über Tesseract, sofern das Programm auf dem Host verfügbar ist
- PDF-Werkzeuge für Extraktion, Verschlüsselung, Entschlüsselung und Schwärzung
- Regelbasierte Hinweise auf ausgewählte sensible Begriffe
- Schema-gefilterter Workspace-Austausch; Exporte vor einer Weitergabe prüfen
- Optionale Startmöglichkeiten für separate Desktop-Werkzeuge

**Hinweis zum Store-Kanal**

- Die vorhandenen Store-Dateien sind Entwürfe und Staging-Material.
- Das Manifest deklariert derzeit `runFullTrust`; daraus folgt keine Store-Freigabe.
- Ein signiertes MSIX, ein aktueller WACK-Lauf auf diesem Paket und eine Partner-Center-Einreichung sind nicht belegt.
- Der in `build_exe.bat` verlangte Tesseract-/Poppler-Bundle fehlt im geprüften Quellstand; der native Paketbuild ist blockiert.
- Abhängigkeitshinweise stehen in `THIRD_PARTY_LICENSES.md` und `THIRD_PARTY_LICENSES.txt`; sie sind keine vollständige Lizenz- oder Kompatibilitätsprüfung.

### Datenschutz

Siehe [PRIVACY_POLICY.md](PRIVACY_POLICY.md).

### Support

Siehe [SUPPORT.md](SUPPORT.md).

### Schlüsselwörter

Dokumentverwaltung, OCR, PDF-Werkzeuge, Datenschutzprüfung, Volltextsuche, Offline, Dateimanager

### Screenshot-Referenzen

- `screenshots/store/shot-1-library-overview.png`: Dateibaum und Dokumentübersicht
- `screenshots/store/shot-2-search-ocr.png`: Suche und OCR
- `screenshots/store/shot-3-privacy-traffic-light.png`: Hinweise der regelbasierten Datenschutzampel
- `screenshots/store/shot-4-pdf-tools.png`: PDF-Werkzeuge und Schwärzung

---

## English

### Short description

Local document management with search, OCR, PDF tools, and rule-based sensitive-term review.

### Description

ProFiler Suite is a Windows-oriented desktop application for local file and document workflows. It combines file search, OCR, PDF utilities, duplicate detection, and indicators for selected potentially sensitive terms.

**Features**

- Search selected local folders and documents
- OCR through Tesseract when available on the host
- PDF utilities for extraction, encryption, decryption, and redaction
- Rule-based indicators for selected sensitive terms
- Schema-filtered workspace exchange; inspect exports before sharing
- Optional launchers for separate desktop tools

**Store channel note**

- Existing Store files are drafts and staging material.
- The current manifest declares `runFullTrust`; this does not establish Store approval.
- A signed MSIX, a current WACK run on that package, and a Partner Center submission are not evidenced.
- The Tesseract/Poppler bundle required by `build_exe.bat` is absent from the reviewed source checkout, so the native package build is blocked.
- Dependency notes are in `THIRD_PARTY_LICENSES.md` and `THIRD_PARTY_LICENSES.txt`; they are not a complete license or compatibility review.

### Privacy

See [PRIVACY_POLICY.md](PRIVACY_POLICY.md).

### Support

See [SUPPORT.md](SUPPORT.md).

### Keywords

Document Manager, OCR, PDF Tools, Privacy Review, Full Text Search, Offline, File Organizer

### Screenshot references

- `screenshots/store/shot-1-library-overview.png`: directory tree and document overview
- `screenshots/store/shot-2-search-ocr.png`: search and OCR
- `screenshots/store/shot-3-privacy-traffic-light.png`: rule-based privacy review indicators
- `screenshots/store/shot-4-pdf-tools.png`: PDF utilities and redaction
