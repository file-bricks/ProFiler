# Third-Party Licenses & Dependency Inventory

**Project:** ProFiler Suite (`file-bricks/ProFiler`)<br>
**Canonical Project License:** GNU Affero General Public License v3.0 (`AGPL-3.0-only`)<br>
**Canonical Attribution:** [NOTICE](NOTICE)<br>
**Audit Date:** 2026-09-26 (Pfad B Discoverability & Design; Previous Pfad A: 2026-09-18; Previous Pfad B: 2026-09-16)<br>
**Auditor:** Antigravity / Gemini (via GithubBot)<br>
**Version:** `15.0.2`<br>
**Umbrella Ecosystem:** `open-bricks`<br>

---

## 1. Overview & Compliance Architecture

ProFiler Suite is an open-source, local-first desktop document management application. Because ProFiler Suite incorporates `PyMuPDF` (under `AGPL-3.0-or-later`), the overarching application codebase is licensed under **AGPL-3.0-only**. All direct runtime libraries, transitive packages, and development toolchains have been cataloged and audited for license compatibility, non-infringement, zero-copyleft contagion on user files, and vulnerability floors.

This inventory is derived directly from `pyproject.toml`, `requirements.txt`, `requirements-lock.txt`, and `requirements-build.txt`.

---

## 2. Direct Runtime Dependencies

| Package | Locked Version | Declared SPDX License | Upstream Project / Repository | Compatibility Analysis |
|---|---|---|---|---|
| **PySide6** | `6.11.1` | `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only` | [The Qt Company](https://doc.qt.io/qtforpython-6/) | **Permissive/Copyleft**: LGPL-3.0 permits dynamic linking with AGPL-3.0 host applications without license contagion. Users retain the freedom to relink with custom Qt builds under LGPL-3.0 § 4. |
| **pypdf** | `6.16.1` | `BSD-3-Clause` | [pypdf](https://pypdf.readthedocs.io/) | **Permissive**: Fully compatible with AGPL-3.0. |
| **pikepdf** | `10.9.1` | `MPL-2.0` | [pikepdf](https://pikepdf.readthedocs.io/) | **Weak Copyleft**: File-level copyleft; fully compatible with AGPL-3.0 applications. |
| **PyMuPDF** | `1.27.2.3` | `AGPL-3.0-or-later OR Commercial Artifex` | [Artifex Software / PyMuPDF](https://pymupdf.readthedocs.io/) | **Strong Copyleft**: Dictates AGPL-3.0-only distribution for ProFiler. Commercial license required if proprietary closed-source distribution is ever chosen. |
| **pdf2image** | `1.17.0` | `MIT` | [pdf2image](https://github.com/Belval/pdf2image) | **Permissive**: Fully compatible with AGPL-3.0. |
| **python-docx** | `1.2.0` | `MIT` | [python-docx](https://python-docx.readthedocs.io/) | **Permissive**: Fully compatible with AGPL-3.0. |
| **pytesseract** | `0.3.13` | `Apache-2.0` | [pytesseract](https://github.com/madmaze/pytesseract) | **Permissive**: Apache-2.0 is compatible with AGPL-3.0. |
| **Pillow** | `12.3.0` | `HPND` (PIL Software License) | [Pillow](https://python-pillow.org/) | **Permissive**: Enforces safe `>=12.3.0` floor mitigating 26 CVEs/GHSAs (including GHSA-4x4j-2g7c-83w6, GHSA-45hq-cxwh-f6vc). |
| **watchdog** | `6.0.0` | `Apache-2.0` | [watchdog](https://github.com/gorakhargosh/watchdog) | **Permissive**: Fully compatible with AGPL-3.0. |
| **reportlab** | `5.0.0` | `BSD-3-Clause` | [ReportLab](https://www.reportlab.com/) | **Permissive**: Fully compatible with AGPL-3.0. |

---

## 3. Optional & Data Management Dependencies

| Package | Minimum Version | SPDX License | Purpose | Status |
|---|---|---|---|---|
| **pandas** | `>=2.2.0` | `BSD-3-Clause` | Optional Excel batch import (`import_excel_to_profiler.py`) | Permissive / Optional extra `[excel]` |
| **openpyxl** | `>=3.1.0` | `MIT` | XLSX workbook reading and parsing | Permissive / Optional extra `[excel]` |

---

## 4. Build, Packaging & Test Toolchain

| Package | Locked Version | SPDX License | Purpose | Invariant Guarantee |
|---|---|---|---|---|
| **PyInstaller** | `6.21.0` | `GPL-2.0-or-later WITH Bootloader-Exception` | Local binary packaging (`build_exe.bat`) | Bootloader exception prevents runtime license pollution. |
| **altgraph** | `0.17.4` | `MIT` | PyInstaller graph dependency | Permissive build tool. |
| **pyinstaller-hooks-contrib** | `2025.1` | `Apache-2.0` | PyInstaller community hook bundle | Permissive build tool. |
| **packaging** | `24.2` | `Apache-2.0 OR BSD-2-Clause` | Version parsing & PEP 440 verification | Permissive core metadata. |
| **pluggy** | `1.6.0` | `MIT` | Pytest plugin manager | Permissive test tool. |
| **iniconfig** | `2.1.0` | `MIT` | Configuration parser | Permissive test tool. |
| **pytest** | `9.1.1` | `MIT` | Test framework | Enforces `>=9.1.1` floor mitigating GHSA-6w46-j5rx-g56g / CVE-2025-7117. |
| **ruff** | `>=0.9.0` | `MIT OR Apache-2.0` | Fast Python linter & bytecode formatter | Development tool. |

---

## 5. External Native Binaries (Host Prerequisites)

| Tool | License | Distribution Note | Bundling Boundary |
|---|---|---|---|
| **Tesseract OCR** | `Apache-2.0` | Optical character recognition engine | **Not bundled in source checkout**. Must be installed on host system (`tesseract.exe`). |
| **Poppler Utilities** | `GPL-2.0-or-later` | PDF rendering and image extraction (`pdftoppm`) | **Not bundled in source checkout**. Must be installed or available in PATH. |

> [!IMPORTANT]
> Neither Tesseract nor Poppler is bundled by the canonical `build_exe.bat`. Windows Store package distribution requires verified bundling, notarized redistributables, and an automated end-to-end WACK (Windows App Certification Kit) verification run before Store release claims can be satisfied.

---

## 6. Governance & Runtime Invariants Assurance

All direct dependencies, optional modules, and toolchains strictly honor ProFiler's 10 Core Governance & Runtime Invariants:

| Invariant Code | Name | Legal & Architectural Assurance |
|---|---|---|
| `INV-LOCAL-01` | **100% Local-First & Zero-Egress** | No library introduces network telemetry, cloud calls, or mandatory online registration. |
| `INV-SESSION-02` | **Session-Only Secrets** | PDF passwords remain exclusively in volatile process memory; zero disk or settings persistence. |
| `INV-GATE-03` | **PII & Datenschutzampel Heuristic Gate** | Built-in heuristics warn before export; no data is transmitted externally. |
| `INV-SCHEMA-04` | **Redacted Workspace Exchange** | JSON Schema v1 export strips host secrets and path pointers. |
| `INV-PLACEHOLDER-05` | **Cloud-Placeholder Awareness** | OneDrive hydration protection prevents unwanted bulk file downloads. |
| `INV-UNPRIV-06` | **Non-Elevation (`RunAsInvoker`)** | Executes entirely in unprivileged user space; zero administrative UAC prompt. |
| `INV-ATOMIC-07` | **Atomic SQLite Indexing** | SQLite WAL mode ensures transactional integrity, atomic commits, and crash recovery. |
| `INV-INTEGRITY-08` | **SHA-256 Deduplication** | Standard cryptographic hashing without proprietary hashing dependencies. |
| `INV-OFFLINE-09` | **Offline OCR & Sandbox** | Tesseract & Poppler execute locally as unprivileged subprocesses. |
| `INV-SLA-10` | **48h Security Response & 5-Day Triage SLA** | Formal vulnerability remediation commitment under `SECURITY.md`. |

---

## 7. User Document Assets & Zero-Copyleft Affirmation

ProFiler Suite operates on user-provided document collections, scanned receipts, contracts, PDFs, images, and SQLite databases. Under AGPL-3.0 and all third-party license terms:

- **Zero-Copyleft on User Data:** Processing, indexing, searching, OCR-annotating, or redacting files using ProFiler Suite does **NOT** subject the user's files, documents, outputs, or databases to AGPL-3.0 or any open-source licensing obligation.
- **User Ownership:** All processed artifacts, index databases (`*.db`), redacted PDFs, and exported workspace JSON archives remain 100% the private, proprietary property of the user or their organization.

---

## 8. Release Checklist & Supply Chain Governance

1. **Commit Hygiene:** Builds must originate exclusively from a clean Git tree on `master` with zero unstaged changes.
2. **Provenance Preservation:** Every production build generates `release/BUILD-PROVENANCE.json` and `release/SHA256SUMS.txt`.
3. **No Unsigned Store Claims:** Local unsigned EXEs remain strictly local developer binaries; Store packages must adhere to Microsoft Store submission requirements (`store_package.json`).
4. **Vulnerability Mitigation:** Dependency floors are pinned to reject all vulnerable historical versions (e.g. Pillow `< 12.3.0`, pytest `< 9.1.1`).
