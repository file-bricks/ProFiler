# Third-Party Dependency Notes

**Project:** ProFiler Suite (`file-bricks/ProFiler`)
**Project license:** GNU Affero General Public License version 3; see [LICENSE](LICENSE) and [NOTICE](NOTICE).
**Reviewed:** 2026-10-12 against the repository dependency declarations
**Version:** `15.0.2` (frozen)

This page identifies declared dependencies and points to their upstream projects. It is not a complete software bill of materials, a review of every transitive package, a vulnerability assessment, or a legal opinion about license compatibility. A future binary package may contain a different set of components; inspect the exact artifact and its included notices before distribution.

## Direct runtime requirements

The constraints below are from `pyproject.toml` and `requirements.txt`. The requirements files and platform-specific package resolution may add or select transitive components.

| Package | Declared requirement | Use in this project | Upstream project and terms |
|---|---|---|---|
| PySide6 | `>=6.5.0` | Desktop UI | [Qt for Python](https://doc.qt.io/qtforpython-6/) |
| pypdf | `>=6.14.2` | PDF reading and writing | [pypdf](https://github.com/py-pdf/pypdf) |
| pikepdf | `>=8.0.0` | PDF structure and encryption workflows | [pikepdf](https://github.com/pikepdf/pikepdf) |
| PyMuPDF | `>=1.23.0` | Optional PDF extraction and redaction paths | [PyMuPDF licensing and project](https://github.com/pymupdf/PyMuPDF) |
| pdf2image | `>=1.16.0` | PDF page rendering through host tools | [pdf2image](https://github.com/Belval/pdf2image) |
| python-docx | `>=1.0.0` | DOCX reading | [python-docx](https://github.com/python-openxml/python-docx) |
| pytesseract | `>=0.3.10` | Tesseract OCR interface | [pytesseract](https://github.com/madmaze/pytesseract) |
| Pillow | `>=12.3.0` | Image loading and conversion | [Pillow](https://github.com/python-pillow/Pillow) |
| watchdog | `>=3.0.0` | File-change monitoring | [watchdog](https://github.com/gorakhargosh/watchdog) |
| ReportLab | `>=4.0.0` | PDF generation | [ReportLab](https://www.reportlab.com/) |

## Optional and development requirements

| Group | Package | Declared requirement | Use | Upstream project and terms |
|---|---|---|---|---|
| `excel` | pandas | `>=2.2.0` | Optional spreadsheet import | [pandas](https://github.com/pandas-dev/pandas) |
| `excel` | openpyxl | `>=3.1.0` | XLSX parsing | [openpyxl](https://foss.heptapod.net/openpyxl/openpyxl) |
| `dev` | pytest | `>=9.1.1` | Tests | [pytest](https://github.com/pytest-dev/pytest) |
| `dev` | Ruff | `>=0.9.0` | Linting | [Ruff](https://github.com/astral-sh/ruff) |
| `dev` | PyInstaller | `>=6.10.0` | Local executable packaging | [PyInstaller](https://github.com/pyinstaller/pyinstaller) |
| `dev` | altgraph | `>=0.17.4` | PyInstaller support | [altgraph](https://github.com/ronaldoussoren/altgraph) |
| `dev` | packaging | `>=24.0` | Version and package metadata utilities | [packaging](https://github.com/pypa/packaging) |
| build system | setuptools | `>=77.0.0` | Build backend | [setuptools](https://github.com/pypa/setuptools) |
| build system | wheel | unspecified | Wheel build support | [wheel](https://github.com/pypa/wheel) |

The checked-in `requirements-lock.txt` pins selected packages for the existing build workflow. It is not a full transitive lockfile and should not be treated as an artifact inventory.

## External programs and packaging boundary

The source checkout does not contain Tesseract or Poppler binaries. `build_exe.bat` requires these files before packaging:

- `runtime/tesseract/tesseract.exe` and `runtime/tesseract/tessdata/`
- `runtime/poppler/pdftoppm.exe` and `runtime/poppler/pdfinfo.exe`

Those required paths are absent from the reviewed checkout, so the native executable build is currently blocked. The source project can call host-installed OCR/PDF tools in workflows that need them. No Store package or bundled-runtime license review is established by this inventory.

## Review boundary

Use the linked upstream project and license texts for the terms applicable to the exact package version and distribution. This page does not conclude that dependencies are compatible with one another or that any component's obligations are satisfied. For binary redistribution, review the built package contents, license texts, notices, and linking or bundling choices as a separate release task.
