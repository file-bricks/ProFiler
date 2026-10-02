# Contributing to ProFiler Suite / Mitwirken an ProFiler Suite

[English](#english) | [Deutsch](#deutsch)

---

<a id="english"></a>
## English

Thank you for your interest in contributing to **ProFiler Suite** (`file-bricks/ProFiler`), a local-first desktop file and document manager with full-text indexing, Tesseract OCR, batch PDF tools, SHA-256 deduplication, and privacy compliance audits (Datenschutzampel) built with PySide6 and SQLite.

### 1. Architectural Principles & 10 Governance Invariants

All contributions must strictly adhere to our core architectural invariants:

1. **Local-First & Zero Egress (`INV-LOCAL-01`)**: 100% offline-ready operation. No remote telemetry, analytics, cloud tracking, or mandatory online registration. All data remains exclusively on-device in local SQLite databases.
2. **Session-Only Secrets (`INV-SESSION-02`)**: PDF encryption passwords and temporary decryption credentials remain strictly in volatile process memory; zero persistence to disk, settings, or log files.
3. **PII & Datenschutzampel Heuristic Gate (`INV-GATE-03`)**: Built-in regex and heuristic patterns identify sensitive personal data (IBANs, tax IDs, credentials) locally and warn before exports without network transmission.
4. **Redacted Workspace Exchange (`INV-SCHEMA-04`)**: Exported workspace exchange archives adhere to JSON Schema v1, stripping host-specific absolute paths and machine identities.
5. **Cloud-Placeholder Awareness (`INV-PLACEHOLDER-05`)**: File crawlers inspect Windows OneDrive reparse points and offline file attributes to prevent unintended bulk cloud hydration and disk saturation.
6. **Unprivileged User Mode (`INV-UNPRIV-06`)**: Pure `RunAsInvoker` execution. The application and all CLI scripts run entirely in standard user space without requiring administrative elevation, root access, or UAC prompts.
7. **Atomic SQLite Indexing (`INV-ATOMIC-07`)**: Database operations use SQLite Write-Ahead Logging (WAL) mode, ensuring crash-safe atomic transactions and reader-writer concurrency.
8. **SHA-256 Deduplication (`INV-INTEGRITY-08`)**: Deterministic cryptographic chunked hashing identifies duplicate files without proprietary hashing schemes.
9. **Offline OCR & Subprocess Sandbox (`INV-OFFLINE-09`)**: Tesseract OCR and Poppler utilities execute locally as sandboxed unprivileged subprocesses with explicit timeout limits.
10. **Security Response SLA (`INV-SLA-10`)**: Binding 48-hour acknowledgment and 5-business-day triage commitment for reported vulnerabilities via `security@file-bricks.org`, `security@open-bricks.org`, and `security@ellmos.ai`.

### 2. Plan D Local Development Workflow

In accordance with our cross-system architecture (Plan D), the local git repository at `C:\_Local_DEV\repos\ProFiler` serves as the authoritative **Source of Truth**. Development, testing, and commits must take place exclusively in the canonical local clone. Cloud mirrors (e.g. OneDrive) serve solely as gitless read projections.

```bash
# Clone the canonical repository
git clone https://github.com/file-bricks/ProFiler.git C:\_Local_DEV\repos\ProFiler
cd C:\_Local_DEV\repos\ProFiler

# Install runtime dependencies
python -m pip install -r requirements.txt

# Run full test suite with isolated basetemp
pytest

# Launch application
python Profiler_Suite_V15.py
```

### 3. Version Freeze Discipline (`T-20260920-167562623`)

ProFiler Suite operates under strict version-freeze discipline. The version identifier (`15.0.2` in `version.py`, `pyproject.toml`, and manifests) must not be arbitrarily incremented. All improvements, bug fixes, and hygiene adjustments are documented under `## [Unreleased]` in `CHANGELOG.md`.

### 4. Quality Gates

Before submitting a pull request, verify all local quality gates:
1. `pytest`: 100% green test execution across all contract, security, accessibility, and functional suites.
2. `ruff check .`: Zero lint errors.
3. `python -m compileall -q .`: Zero bytecode compilation errors.
4. `git diff --check`: Zero whitespace or line-ending anomalies.
5. `git diff -G"version = "`: Zero unauthorized version modifications.

### 5. Statutory Notice (§ 521 BGB) & Zero-Copyleft on User Data

This software is provided free of charge under the GNU Affero General Public License v3.0 (AGPL-3.0-only). In accordance with German statutory law (**§ 521 BGB** — *Haftung des Schenkers*), liability for defects in quality and title is strictly limited to intentional misconduct (*Vorsatz*) and gross negligence (*grobe Fahrlässigkeit*).

**Zero-Copyleft Guarantee:** Processing, indexing, OCR-annotating, or redacting files using ProFiler Suite does **not** subject user documents, databases, or exported archives to AGPL-3.0 or any open-source licensing obligation. All user data remains 100% private and proprietary.

---

<a id="deutsch"></a>
## Deutsch

Vielen Dank für dein Interesse an einer Mitwirkung bei der **ProFiler Suite** (`file-bricks/ProFiler`), einem lokalen Desktop-Dateimanager mit Volltext-Indexierung, Tesseract-OCR, Batch-PDF-Werkzeugen, SHA-256-Duplikaterkennung und DSGVO-Datenschutzprüfung (Datenschutzampel), entwickelt mit PySide6 und SQLite.

### 1. Architektur-Prinzipien & 10 Governance-Invarianten

Alle Beiträge müssen unsere verbindlichen Kern-Invarianten strikt einhalten:

1. **Local-First & Zero Egress (`INV-LOCAL-01`)**: 100% Offline-Betrieb. Keine Netzwerk-Telemetrie, kein Cloud-Upload, keine Analyse-Tracker und kein Zwangskonto. Alle Daten verbleiben ausnahmslos lokal in SQLite-Datenbanken.
2. **Flüchtige Passwörter (`INV-SESSION-02`)**: PDF-Passwörter und temporäre Entschlüsselungsschlüssel verbleiben ausschließlich im flüchtigen Prozessspeicher; keine Speicherung auf Festplatte, in Einstellungen oder Logdateien.
3. **Datenschutzampel & PII-Heuristik (`INV-GATE-03`)**: Integrierte Regex-Muster erkennen sensible personenbezogene Daten (IBAN, Steuer-IDs, Zugangsdaten) lokal und warnen vor dem Export ohne Netzwerkkommunikation.
4. **Redigierter Datenaustausch (`INV-SCHEMA-04`)**: Exportierte Workspace-Archive folgen dem JSON-Schema v1 und entfernen systemspezifische absolute Pfade und Host-Identitäten.
5. **Cloud-Platzhalter-Schutz (`INV-PLACEHOLDER-05`)**: Der Datei-Crawler erkennt OneDrive-Reparse-Points und verhindert das unbeabsichtigte Herunterladen riesiger Cloud-Bestände auf die lokale Festplatte.
6. **Rechtefreier Benutzermodus (`INV-UNPRIV-06`)**: Reiner `RunAsInvoker`-Betrieb. Die Anwendung und alle Skripte laufen vollständig mit Standard-Benutzerrechten ohne Administratorrechte oder UAC-Aufforderungen.
7. **Atomare SQLite-Indexierung (`INV-ATOMIC-07`)**: Transaktionale Datenhaltung im SQLite Write-Ahead-Logging (WAL) Modus mit atomaren Commits und zuverlässiger Absturzsicherheit.
8. **SHA-256 Duplikaterkennung (`INV-INTEGRITY-08`)**: Deterministische kryptografische Chunk-Hashes identifizieren Datei-Duplikate ohne proprietäre Hashing-Verfahren.
9. **Offline-OCR & Prozess-Sandbox (`INV-OFFLINE-09`)**: Tesseract OCR und Poppler laufen lokal als unprivilegierte Subprozesse mit strikten Timeout-Grenzen.
10. **Sicherheits-Response SLA (`INV-SLA-10`)**: Verbindliche 48-Stunden-Erstantwortgarantie und 5-Werktage-Triage-Zusage für gemeldete Schwachstellen über `security@file-bricks.org`, `security@open-bricks.org` und `security@ellmos.ai`.

### 2. Plan D Lokaler Entwicklungsworkflow

Gemäß unserer systemweiten Architektur (Plan D) bildet das lokale Repository unter `C:\_Local_DEV\repos\ProFiler` die alleinige maßgebliche **Source of Truth**. Entwicklung, Tests und Commits finden ausschließlich im kanonischen lokalen Klon statt. Cloud-Spiegel (z. B. OneDrive) dienen rein als gitlose Leseprojektionen.

```bash
# Kanonischen Klon verwenden
git clone https://github.com/file-bricks/ProFiler.git C:\_Local_DEV\repos\ProFiler
cd C:\_Local_DEV\repos\ProFiler

# Abhängigkeiten installieren
python -m pip install -r requirements.txt

# Testsuite mit isoliertem basetemp ausführen
pytest

# Anwendung starten
python Profiler_Suite_V15.py
```

### 3. Version Freeze Discipline (`T-20260920-167562623`)

Die ProFiler Suite unterliegt strikter Version-Freeze-Disziplin. Die Versionskennung (`15.0.2` in `version.py`, `pyproject.toml` und Manifesten) darf nicht beliebig erhöht werden. Alle Verbesserungen, Fehlerbehebungen und Hygiene-Maßnahmen werden unter `## [Unreleased]` in `CHANGELOG.md` erfasst.

### 4. Qualitäts-Tore

Vor dem Einreichen eines Pull Requests sind alle lokalen Prüfungen zu bestätigen:
1. `pytest`: 100% bestandene Tests über alle Vertrags-, Sicherheits-, Barrierefreiheits- und Funktionssuiten.
2. `ruff check .`: 0 Flotten-Linterfehler.
3. `python -m compileall -q .`: 0 Bytecode-Kompilierungsfehler.
4. `git diff --check`: 0 Whitespace- oder Zeilenumbruchfehler.
5. `git diff -G"version = "`: 0 unautorisierte Versionsmodifikationen.

### 5. Gesetzlicher Hinweis (§ 521 BGB) & Nutzerdaten-Schutz

Diese Software wird unentgeltlich unter der GNU Affero General Public License v3.0 (AGPL-3.0-only) bereitgestellt. Gemäß **§ 521 BGB** (*Haftung des Schenkers*) ist die Haftung für Sach- und Rechtsmängel auf Vorsatz und grobe Fahrlässigkeit beschränkt.

**Zero-Copyleft auf Nutzerdaten:** Die Verarbeitung, Indexierung, OCR-Verarbeitung oder Schwärzung von Dokumenten mit der ProFiler Suite unterwirft verarbeitete Nutzerdateien, Datenbanken oder exportierte Archive **nicht** den Bestimmungen der AGPL-3.0. Alle Nutzerdaten verbleiben zu 100% privates, geschütztes Eigentum des Anwenders.
