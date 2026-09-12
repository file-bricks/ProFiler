<img src="assets/banner.svg" width="100%" alt="ProFiler Banner">

# ProFiler Suite

**[English](README.md)** | [Deutsch](README_de.md) | [GitHub](https://github.com/file-bricks/ProFiler)

[![Version: 15.0.1](https://img.shields.io/badge/version-15.0.1-blue.svg)](CHANGELOG.md)
[![Org: file-bricks](https://img.shields.io/badge/Org-file--bricks-blue)](https://github.com/file-bricks)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
[![CI: Platform Smoke](https://img.shields.io/badge/CI-Platform%20Smoke-brightgreen.svg)](https://github.com/file-bricks/ProFiler/actions)
[![Tests: 183 passed](https://img.shields.io/badge/tests-183%20passed%20%7C%20100%25-brightgreen.svg)]()
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Security SLA: 48h Response / 5d Triage](https://img.shields.io/badge/Security%20SLA-48h%20Response%20%2F%205d%20Triage-blue.svg)](SECURITY.md)
[![Python: 3.10--3.13](https://img.shields.io/badge/python-3.10--3.13-blue.svg)](https://www.python.org/)
[![GUI: PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://wiki.qt.io/Qt_for_Python)
[![Platform: Windows | Linux | macOS](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()
[![Privacy: 100% Local-First](https://img.shields.io/badge/privacy-100%25%20Local--First-success.svg)]()
[![Ecosystem: open-bricks](https://img.shields.io/badge/ecosystem-open--bricks-blueviolet)](https://github.com/open-bricks)
[![LLM Context: llms.txt](https://img.shields.io/badge/LLM%20Context-llms.txt-orange)](llms.txt)

> [!NOTE]
> AI agents and LLM tools reading this repository should refer to [`llms.txt`](llms.txt) for codebase architecture, primary features, contract boundaries, and verification commands.

> Local-first document detective — full-text indexing, OCR, PDF tools, duplicate detection & privacy checks in one PySide6 app.

ProFiler Suite is a local-first desktop file and document manager for private collections. It unifies full-text file indexing, Tesseract OCR, PDF manipulation, SHA-256 duplicate detection, privacy compliance audits (Datenschutzampel), and companion synchronization in a responsive Windows-oriented PySide6 desktop app.

It is purpose-built for users who manage private, proprietary, or regulated documents and want high-speed search, preview, PDF processing, and redaction workflows without ever transmitting data to a third-party cloud.

---

### Quick Navigation

- [Architecture](#architecture)
- [Workflow Lifecycle](#workflow-lifecycle)
- [Core Capabilities & Security Invariants](#core-capabilities--security-invariants)
- [Target Personas & Use Cases](#target-personas--use-cases)
- [Comparative Matrix & Alternatives](#comparative-matrix--alternatives)
- [Feature Highlights](#feature-highlights)
- [Visual Interface & Screenshot](#visual-interface--screenshot)
- [When To Use ProFiler](#when-to-use-profiler)
- [Quick Start & Setup](#quick-start--setup)
- [Windows Launcher & Build Flow](#windows-launcher--build-flow)
- [Configuration & Local Storage](#configuration--local-storage)
- [Included Tools & Utilities](#included-tools--utilities)
- [Supported File Formats & OCR](#supported-file-formats--ocr)
- [Sibling Ecosystem & Integrations](#sibling-ecosystem--integrations)
- [Third-Party Licenses & Compliance](#third-party-licenses--compliance)
- [Security Policy & SLAs](#security-policy--slas)

---

## Architecture

```mermaid
graph TD
    subgraph Sources["1. Document & File Sources"]
        A1["Local Directory Tree"]
        A2["Document Folders (PDF, DOCX, TXT, RTF)"]
        A3["Scanned Paperwork & Images"]
        A4["OneDrive Mounts (Cloud-Placeholder Aware)"]
    end

    subgraph CoreEngine["2. Core Ingestion & Indexing"]
        B1["Crawler & File Watchdog"]
        B2["SHA-256 Fingerprinting"]
        B3["SQLite Local Index (Versions, Metadata)"]
    end

    subgraph Processing["3. Document & PDF Processing Layer"]
        C1["Tesseract OCR Engine"]
        C2["PDF Utilities (Encrypt, Decrypt, Extract, Redact)"]
        C3["Deduplication & Version Tracker"]
    end

    subgraph PrivacyGate["4. Privacy & Workspace Security"]
        D1["Datenschutzampel (PII Pattern Detector)"]
        D2["Redacted Workspace Exchange (JSON Schema v1)"]
    end

    subgraph UI["5. Presentation & Companion Integration"]
        E1["PySide6 UnifiedMainWindow (Dark/Light Themes)"]
        E2["SQLiteViewer (Index Inspector)"]
        E3["ProSync Sibling Launcher"]
    end

    Sources --> CoreEngine
    CoreEngine --> Processing
    Processing --> PrivacyGate
    PrivacyGate --> UI
```

## Workflow Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor User as Desktop User
    participant UI as PySide6 GUI (UnifiedMainWindow)
    participant Crawler as File Watchdog & Crawler
    participant Index as SQLite Local Index
    participant OCR as Tesseract OCR / PDF Engine
    participant Gate as Datenschutzampel (PII Detector)
    participant Exchange as Redacted Workspace Exchange

    User->>UI: Select document folder or file
    UI->>Crawler: Scan path & calculate SHA-256 fingerprint
    Crawler->>Index: Store file metadata & version state
    opt Scanned Document / Image PDF
        UI->>OCR: Trigger Tesseract OCR / text extraction
        OCR->>Index: Update full-text search index (FTS)
    end
    User->>UI: Request document export / sharing
    UI->>Gate: Execute PII & sensitive pattern check
    alt Sensitive Data Detected
        Gate-->>UI: Warning / Redaction prompt (Datenschutzampel RED/YELLOW)
        User->>UI: Apply PDF redaction / anonymize workspace
    else Safe Document
        Gate-->>UI: Clear status (Datenschutzampel GREEN)
    end
    UI->>Exchange: Export redacted workspace JSON (Schema v1)
    Exchange-->>User: Validated, zero-leak handoff artifact
```

## Core Capabilities & Security Invariants

| Invariant Code | Guarantee & Boundary | Architectural Implementation | Verification & Evidence |
|---|---|---|---|
| `INV-LOCAL-01` | **100% Local-First & Zero-Egress** | All SQLite databases, indexes, and document caches remain strictly on the local machine. Zero cloud upload, zero network telemetry, and no mandatory online registration. | Verified via network-free test suite & POSIX/Windows filesystem isolation. |
| `INV-SESSION-02` | **Session-Only Secrets** | PDF passwords and temporary decryption keys are retained exclusively in volatile process memory and never written to disk, settings, or log files. | Contract-tested in `tests/test_security_hardening.py` (`test_settings_passwords_are_session_only`). |
| `INV-GATE-03` | **PII & Datenschutzampel Heuristic Gate** | Built-in pattern detection (`Datenschutzampel`) flags sensitive numbers, tax IDs, IBANs, credentials, and personal identifiable information before export or handoff. | Validated in `ProFiler_Datenschutzampel.py` and `tests/test_anonymization.py`. |
| `INV-SCHEMA-04` | **Redacted Workspace Exchange** | Workspace export and import conform strictly to JSON-Schema v1, stripping machine-specific absolute paths, system secrets, and unmanaged file pointers. | Tested in `tests/test_workspace_exchange.py` with BOM-free UTF-8 serialization. |
| `INV-PLACEHOLDER-05` | **Cloud-Placeholder Awareness** | Intelligently identifies OneDrive and cloud placeholder files, preventing unprompted hydration or excessive disk usage during bulk indexing scans. | Implemented in Crawler and verified in `tests/test_bug_regressions.py`. |
| `INV-UNPRIV-06` | **Non-Elevation & User-Space Operation** | Operates strictly as an unprivileged user process (`RunAsInvoker`). Settings and SQLite indices reside under standard `%LOCALAPPDATA%\ProFilerSuite` (or XDG standards on POSIX). | Verified in `tests/test_app_paths.py` and `tests/test_platform_smoke_contract.py`. |
| `INV-ATOMIC-07` | **Atomic SQLite Indexing** | Indexing transactions leverage WAL mode with atomic commits, ensuring crash resilience and multi-thread readability without database corruption. | Tested in `SQLiteViewer.py` and database inspection tests. |
| `INV-INTEGRITY-08` | **SHA-256 Deduplication** | Identifies exact byte-for-byte duplicate files across different directory branches using cryptographic SHA-256 hashing. | Verified across diverse file types in test suites. |
| `INV-OFFLINE-09` | **Offline Tesseract OCR & Poppler Sandbox** | Optical character recognition and PDF page rendering execute locally via unprivileged subprocesses with zero external API calls. | Tested in `tests/test_security_hardening.py`. |
| `INV-SLA-10` | **48h Security Response & 5-Day Triage SLA** | Security vulnerabilities receive an initial response within 48 hours and an actionable triage report within 5 business days. | Formalized in `SECURITY.md` and verified in `tests/test_metadata.py`. |

## Target Personas & Use Cases

| Persona | Primary Needs & Workflows | Key Pain Points Solved by ProFiler |
|---|---|---|
| **Legal, Compliance & Privacy Officers** | Auditing local document archives for GDPR/DSGVO compliance, sanitizing PDF case files, redacting sensitive client information, and preventing accidental data exposure. | **Eliminates Cloud Leakage**: Built-in Datenschutzampel detects PII and flags files with traffic-light status before export. In-memory redaction prevents accidental credential or tax ID leakage. |
| **Academic Researchers & Archival Curators** | Organizing extensive historical document corpuses, full-text searching scanned paperwork, identifying duplicate scans across deep folder trees, and reviewing metadata. | **Integrated Local OCR**: Tesseract integration extracts text from image-only PDFs directly into a searchable SQLite FTS index without uploading rare manuscripts to third-party servers. |
| **Small Business Owners & Freelancers** | Managing local invoice archives, client contracts, and vendor receipts across multiple quarters; batch protecting or extracting specific PDF pages for accounting. | **Zero Subscription Overhead**: Provides a comprehensive desktop document hub without recurring monthly SaaS fees (e.g. Adobe Acrobat / DocuWare), operating completely offline. |
| **Power Users & Data Sovereignty Advocates** | Fast, responsive file management with dark/light themes, keyboard navigation, precise control over file paths, and safe coexistence with OneDrive sync. | **Placeholder Protection**: ProFiler detects OneDrive cloud placeholders and refrains from forcing unwanted downloads, keeping disk usage under full user control. |

## Comparative Matrix & Alternatives

| Feature / Dimension | ProFiler Suite | Cloud Document SaaS (DocuWare / Dropbox) | Native OS File Manager (Windows Explorer) | Heavyweight Enterprise ECM (Alfresco / Nextcloud) | Sibling Tool (KnowledgeDigest) |
|---|---|---|---|---|---|
| **Architecture** | **100% Local-First** | Cloud-Hosted SaaS | Local OS Shell | Self-Hosted Server | Local-First Hub |
| **Network Egress** | **Zero-Egress** | Mandatory Upload | Zero (Local Only) | Server Sync Required | Zero-Egress |
| **Full-Text SQLite Search** | **Yes (FTS & Metadata)** | Cloud Index Only | Basic Windows Search | Lucene/Elasticsearch | Yes (FTS5 + BM25) |
| **Built-in OCR (Tesseract)** | **Yes (Offline)** | Proprietary Cloud OCR | None | Optional Plugin | Text-Only Extraction |
| **PDF Tools (Redact / Encrypt)** | **Yes (Integrated)** | High-Tier Paid Addon | None | Third-Party Tool | None |
| **Privacy Traffic Light (PII)** | **Yes (Datenschutzampel)** | Enterprise DLP Addon | None | Complex Rules Engine | None |
| **Cloud Placeholder Guard** | **Yes (OneDrive Aware)** | Native Sync Client | Native Sync Client | Not Applicable | Basic File Access |
| **Recurring Cost** | **Free & Open Source** | $15–$50 / user / month | Free with OS | Hardware + Admin Costs | Free & Open Source |
| **Primary Sweet Spot** | **Local Document Detective** | Corporate Collaboration | Generic File Browsing | Multi-Tenant Enterprise | LLM Digest & Chunking |

## Feature Highlights

- **Local SQLite File Index**: Rapid indexing for folders, document collections, and versioned file entries.
- **Full-Text Search Engine**: Search across PDF, DOCX, TXT, RTF, images, spreadsheets, and source code.
- **Tesseract OCR Integration**: Automatic OCR workflow for scanned PDFs and image documents.
- **Comprehensive PDF Workshop**: Encrypt, decrypt, extract pages, redact text, and export sanitized documents.
- **Cryptographic Deduplication**: Fast SHA-256 fingerprinting to identify redundant duplicate files.
- **Datenschutzampel (Privacy Traffic Light)**: Pre-flight inspection flagging sensitive numbers and PII before sharing.
- **Cloud-Placeholder Awareness**: Safe scanning of OneDrive libraries without triggering bulk file hydration.
- **ProSync Companion Integration**: Direct launcher bridge for synchronizing managed folder pairs.
- **Redacted Workspace Exchange**: Export and import portable workspaces via JSON Schema v1.
- **Ergonomic Desktop UI**: Native PySide6 interface with dark/light theme switching and system tray integration.
- **Companion Utilities**: Bundled SQLite database inspector (`SQLiteViewer.py`) and Excel file importer.

## Visual Interface & Screenshot

![ProFiler Suite desktop file manager with filters, file search, collections and preview panes](README/screenshots/main.png)

## When To Use ProFiler

ProFiler is the optimal solution when you require a private document management tool for:

- Maintaining searchable local archives of PDFs, Office documents, text files, and scanned receipts.
- Running OCR-assisted indexing across legacy document scans without third-party cloud fees.
- Detecting duplicate files and auditing version drift across deep directory structures.
- Handling PDF security operations (passwords, page extractions, redactions) in a single desktop app.
- Auditing document packages for privacy and GDPR/DSGVO compliance before sending them to external parties.
- Using a unified desktop hub alongside companion tools such as [ProSync](https://github.com/file-bricks/ProSync) and [SQLiteViewer](https://github.com/file-bricks/SQLiteViewer).

## Quick Start & Setup

### Prerequisites & Requirements

- Python 3.10+ (tested on Python 3.10, 3.11, 3.12, 3.13)
- PySide6
- Tesseract OCR (optional, required for image and scanned PDF OCR)
- Poppler utilities (optional, required for PDF rendering and page conversion)

### Installation & Launch

Install runtime dependencies from PyPI:

```bash
pip install -r requirements.txt
python Profiler_Suite_V15.py
```

On Windows, you can start the application directly via the bundled starter script:

```bat
START.bat
```

## Windows Launcher & Build Flow

For local Windows desktop deployment, you can compile a self-contained executable:

```bat
build_exe.bat
```

The build requires a clean Git checkout, runs outside OneDrive in `C:\_Local_DEV\codex_build\profiler`, uses pinned build dependencies, and generates:

- `release/ProFiler-15.0.0-win64.exe`
- `release/SHA256SUMS.txt`
- `release/BUILD-PROVENANCE.json`

The build never writes into OneDrive, GitHub Releases, or a Store package. `START.bat` launches a local EXE only when the adjacent `ProFiler.exe.sha256` matches; otherwise, a source checkout launches `Profiler_Suite_V15.py`.

## Configuration & Local Storage

| File Path | Functional Purpose |
|---|---|
| `%LOCALAPPDATA%\ProFilerSuite\profiler_config.json` | Active folder connections and database indexing settings |
| `%LOCALAPPDATA%\ProFilerSuite\profiler_settings.json` | UI preferences, theme selection, and optional tool paths |
| `%LOCALAPPDATA%\ProFilerSuite\search_config.json` | Configured search databases and indexing targets |
| `*.example.json` | Public, path-free configuration templates (never contain live data) |

PDF passwords are session-only and are deliberately excluded from persisted settings. The Excel importer is an optional administrative utility:

```bash
python -m pip install -e ".[excel]"
python import_excel_to_profiler.py --input INPUT.xlsx --database profiler.db --output imported
```

## Included Tools & Utilities

| Tool File | Functional Description |
|---|---|
| `Profiler_Suite_V15.py` | Main desktop GUI application (PySide6) |
| `ProFiler_Datenschutzampel.py` | Standalone privacy traffic-light checker for PII auditing |
| `SQLiteViewer.py` | SQLite database viewer for inspecting index tables |
| `import_excel_to_profiler.py` | Command-line utility for importing existing Excel file inventories |
| `indent_gui_checker.py` | Codebase development tool for checking GUI indentation integrity |

## Supported File Formats & OCR

| Category | File Extensions | Capabilities |
|---|---|---|
| **Documents** | `.pdf`, `.docx`, `.txt`, `.rtf` | Full-text indexing, metadata parsing, search, and preview |
| **Images** | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp` | Metadata extraction, image preview, and Tesseract OCR text recognition |
| **Spreadsheets** | `.xlsx`, `.xls`, `.csv` | Structure inspection and metadata indexing (Excel extra available) |
| **Other Formats** | Universal fallback | Indexed by filesystem attributes, file size, timestamps, and SHA-256 hash |

## Sibling Ecosystem & Integrations

ProFiler Suite is an active member of the **file-bricks** desktop utility family under the **[open-bricks](https://github.com/open-bricks)** umbrella:

| Tool | Repository | Domain / Focus | Status |
|---|---|---|---|
| **ProFiler** | [file-bricks/ProFiler](https://github.com/file-bricks/ProFiler) | Local document indexing, OCR, duplicate detection & privacy | Active Flagship |
| **KnowledgeDigest** | [file-bricks/knowledgedigest](https://github.com/file-bricks/knowledgedigest) | Portable knowledge database, FTS5 BM25 search & LLM digest | Active Flagship |
| **PDFtoPDFocr** | [doc-bricks/PDFtoPDFocr](https://github.com/doc-bricks/PDFtoPDFocr) | Batch OCR & searchable PDF generation engine | Active Sibling |
| **DokuZen** | [doc-bricks/DokuZen](https://github.com/doc-bricks/DokuZen) | Desktop PDF workshop, format converter & security unlocker | Active Sibling |
| **MediaBrain** | [doc-bricks/MediaBrain](https://github.com/doc-bricks/MediaBrain) | Multi-modal media transcription & structured indexing | Active Sibling |
| **TextBrain** | [doc-bricks/TextBrain](https://github.com/doc-bricks/TextBrain) | Document intelligence, semantic classification & summaries | Active Sibling |
| **DevCenter** | [dev-bricks/DevCenter](https://github.com/dev-bricks/DevCenter) | Developer workspace dashboard & automation launcher | Active Sibling |
| **CodeBox** | [dev-bricks/CodeBox](https://github.com/dev-bricks/CodeBox) | Offline snippet vault & code runner sandbox | Active Sibling |
| **FileCommander MCP** | [ellmos-ai/ellmos-filecommander-mcp](https://github.com/ellmos-ai/ellmos-filecommander-mcp) | Safe, sandboxed MCP file management & batch processing | Active Companion |
| **CodeCommander MCP** | [ellmos-ai/ellmos-codecommander-mcp](https://github.com/ellmos-ai/ellmos-codecommander-mcp) | MCP code intelligence, AST analysis & format repair | Active Companion |
| **SQLite Transit Sync** | [dev-bricks/sqlite-transit-sync](https://github.com/dev-bricks/sqlite-transit-sync) | Zero-loss multi-master SQLite replication & synchronization | Active Companion |

## Third-Party Licenses & Compliance

ProFiler Suite is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0-only)**. See [LICENSE](LICENSE).

Because ProFiler Suite uses `PyMuPDF`, the application is distributed under AGPL-3.0. A complete, audited third-party dependency and license inventory covering all direct packages (`PySide6`, `pypdf`, `pikepdf`, `Pillow`, `watchdog`, `reportlab`, `pytesseract`) and toolchains is documented in [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md) (and [`THIRD_PARTY_LICENSES.txt`](THIRD_PARTY_LICENSES.txt)).

Windows Store distribution preparations are governed by `store_package.json`, `STORE_LISTING.md`, `PRIVACY_POLICY.md`, `SUPPORT.md`, and `WINDOWS_STORE_PREP.md`.

## Security Policy & SLAs

ProFiler maintains a formal, bilingual security policy under [`SECURITY.md`](SECURITY.md).

- **Vulnerability Response SLA**: 48-hour initial response guarantee.
- **Triage & Remediation SLA**: 5 business days triage and resolution timeline.
- **Reporting Channels**: Contact `security@open-bricks.org` and `support@lukasgeiger.com`, or open a GitHub Security Advisory.

---

### Discoverability Keywords

`local-first file manager`, `desktop document manager`, `private document archive`, `OCR desktop app`, `PDF OCR tool`, `PDF redaction`, `document privacy checker`, `PySide6 file management`, `SQLite document index`, `Windows file organizer`, `Datenschutzampel`, `GDPR file review`.
