# ProFiler Suite

[Deutsch](README_de.md) | [GitHub](https://github.com/file-bricks/ProFiler)

ProFiler Suite is a local-first desktop file manager for private document collections. It combines full-text file indexing, OCR, PDF tools, duplicate detection, privacy checks, and optional ProSync integration in one Windows-oriented PySide6 app.

It is built for users who manage many local documents and want search, preview, PDF processing, and privacy workflows without uploading files to a cloud service.

## Highlights

- Local SQLite file index for folders, document collections, and versioned file entries
- Full-text search across PDF, DOCX, TXT, RTF, images, spreadsheets, and code files
- OCR workflow for scanned PDFs and image documents via Tesseract
- PDF utilities for encryption, decryption, page extraction, OCR, text removal, and export
- Duplicate and version handling with SHA-256 based file fingerprints
- Privacy traffic light for finding potentially sensitive files before sharing or archiving
- Cloud-placeholder awareness for OneDrive-style local file libraries
- Optional ProSync companion launcher for folder synchronization workflows
- Desktop GUI with dark/light theme support and system tray integration
- Included helper tools for SQLite inspection and Excel import

## Screenshot

![ProFiler Suite desktop file manager with filters, file search, collections and preview panes](screenshots/main.png)

## When To Use ProFiler

ProFiler is useful when you need a private document management tool for:

- searchable local archives of PDFs, Office documents, text files, and scanned paperwork
- OCR-assisted document indexing without a hosted SaaS service
- file cleanup, duplicate detection, and version review across folders
- PDF handling for small office workflows
- privacy review before forwarding, exporting, or publishing document bundles
- a companion desktop hub next to tools such as ProSync and SQLiteViewer

## Quick Start

```bash
pip install -r requirements.txt
python Profiler_Suite_V15.py
```

On Windows you can also start the app with:

```bat
START.bat
```

## Requirements

- Python 3.8+
- PySide6
- Tesseract OCR for OCR features
- Optional PDF/OCR libraries listed in `requirements.txt`

OCR requires [Tesseract](https://github.com/tesseract-ocr/tesseract). Configure the executable path in `profiler_config.json` if the portable copy or system installation is not auto-detected.

## Configuration

| File | Purpose |
|---|---|
| `profiler_config.json` | Main paths, OCR settings, and index configuration |
| `profiler_settings.json` | UI settings, theme, and optional `prosync_path` |
| `search_config.json` | Search databases, filters, and search options |

## Included Tools

| Tool | Purpose |
|---|---|
| `Profiler_Suite_V15.py` | Main desktop application |
| `ProFiler_Datenschutzampel.py` | Standalone privacy traffic-light check |
| `SQLiteViewer.py` | SQLite database viewer for index inspection |
| `import_excel_to_profiler.py` | Excel import for existing file lists |
| `indent_gui_checker.py` | GUI indentation checker for development maintenance |

## Supported Formats

| Category | Formats |
|---|---|
| Documents | PDF, DOCX, TXT, RTF |
| Images | PNG, JPG, TIFF with OCR support |
| Spreadsheets | XLSX, XLS, CSV |
| Other files | Indexed by metadata and file category |

## ProFiler And KnowledgeDigest

Looking for full-text search with BM25 ranking, LLM summarization, or a web viewer for your documents? See [KnowledgeDigest](https://github.com/file-bricks/knowledgedigest), a portable knowledge database from the same author.

| | ProFiler | KnowledgeDigest |
|---|---|---|
| Focus | File management, PDF tools, OCR, privacy | Knowledge search, chunking, LLM summaries |
| Search | Multi-DB, type/size/date filters | FTS5 with BM25 ranking and snippets |
| PDF | Encrypt, decrypt, extract, redact, OCR | Read-only text extraction |
| Privacy | Anonymization, redaction, clipboard guard | Not the focus |
| AI | Not the focus | LLM summarization and keyword extraction |
| Interfaces | Desktop GUI, system tray | Desktop GUI, web viewer, CLI, Python API |
| License | AGPL-3.0 | MIT |

## Privacy And Redaction Notice

ProFiler supports privacy workflows, redaction, and anonymization, but it does not guarantee complete removal of sensitive information. Always review generated files manually before sharing or publishing them.

## License

ProFiler Suite is licensed under AGPL-3.0. See [LICENSE](LICENSE).

This project uses PySide6 and PyMuPDF among other dependencies; see `requirements.txt` and `THIRD_PARTY_LICENSES.txt`.

## Discoverability Keywords

`local-first file manager`, `desktop document manager`, `private document archive`, `OCR desktop app`, `PDF OCR tool`, `PDF redaction`, `document privacy checker`, `PySide6 file management`, `SQLite document index`, `Windows file organizer`.

