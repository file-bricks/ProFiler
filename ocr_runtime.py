"""Resolve optional bundled Poppler/Tesseract runtime files safely.

The release layout is intentionally explicit:

    runtime/tesseract/tesseract.exe
    runtime/tesseract/tessdata/
    runtime/poppler/pdftoppm.exe
    runtime/poppler/pdfinfo.exe

The binaries and language data are supplied separately with their licenses;
this module never downloads or invents them.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class OcrRuntimePaths:
    """Resolved paths for a bundled OCR/PDF runtime."""

    root: Path
    tesseract_exe: Optional[Path]
    tessdata_dir: Optional[Path]
    poppler_dir: Optional[Path]

    @property
    def ready(self) -> bool:
        """Whether all required bundled files/directories are present."""
        return all(
            (
                self.tesseract_exe and self.tesseract_exe.is_file(),
                self.tessdata_dir and self.tessdata_dir.is_dir(),
                self.poppler_dir and (self.poppler_dir / "pdftoppm.exe").is_file(),
                self.poppler_dir and (self.poppler_dir / "pdfinfo.exe").is_file(),
            )
        )


def resource_base_dir() -> Path:
    """Return the source or PyInstaller extraction directory."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass).resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resolve_ocr_runtime(base_dir: Optional[Path] = None) -> OcrRuntimePaths:
    """Resolve the explicit ``runtime`` layout below ``base_dir``."""
    base = Path(base_dir).resolve() if base_dir else resource_base_dir()
    root = base / "runtime"
    tesseract_exe = root / "tesseract" / "tesseract.exe"
    tessdata_dir = root / "tesseract" / "tessdata"
    poppler_dir = root / "poppler"
    return OcrRuntimePaths(
        root=root,
        tesseract_exe=tesseract_exe if tesseract_exe.is_file() else None,
        tessdata_dir=tessdata_dir if tessdata_dir.is_dir() else None,
        poppler_dir=poppler_dir
        if (poppler_dir / "pdftoppm.exe").is_file() and (poppler_dir / "pdfinfo.exe").is_file()
        else None,
    )


def configure_ocr_runtime() -> OcrRuntimePaths:
    """Point pytesseract at bundled files when present."""
    runtime = resolve_ocr_runtime()
    if runtime.tesseract_exe:
        try:
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = str(runtime.tesseract_exe)
        except ImportError:
            pass
    return runtime
