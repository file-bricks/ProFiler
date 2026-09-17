from __future__ import annotations

from pathlib import Path

import pytest

from ocr_runtime import resolve_ocr_runtime
from scripts.write_ocr_bundle_args import _bundle_args


def _make_runtime(root: Path) -> Path:
    runtime = root / "runtime"
    (runtime / "tesseract" / "tessdata").mkdir(parents=True)
    (runtime / "poppler").mkdir(parents=True)
    (runtime / "tesseract" / "tesseract.exe").write_bytes(b"tesseract")
    (runtime / "tesseract" / "libtesseract.dll").write_bytes(b"dll")
    (runtime / "tesseract" / "tessdata" / "deu.traineddata").write_bytes(b"lang")
    (runtime / "poppler" / "pdftoppm.exe").write_bytes(b"pdftoppm")
    (runtime / "poppler" / "pdfinfo.exe").write_bytes(b"pdfinfo")
    (runtime / "poppler" / "poppler.dll").write_bytes(b"dll")
    return runtime


def test_missing_runtime_is_not_reported_ready(tmp_path: Path) -> None:
    resolved = resolve_ocr_runtime(tmp_path)
    assert resolved.ready is False
    assert resolved.tesseract_exe is None
    assert resolved.poppler_dir is None


def test_runtime_contract_resolves_all_required_paths(tmp_path: Path) -> None:
    runtime = _make_runtime(tmp_path)
    resolved = resolve_ocr_runtime(tmp_path)
    assert resolved.ready is True
    assert resolved.tesseract_exe == runtime / "tesseract" / "tesseract.exe"
    assert resolved.tessdata_dir == runtime / "tesseract" / "tessdata"
    assert resolved.poppler_dir == runtime / "poppler"


def test_pyinstaller_args_include_binaries_and_tessdata(tmp_path: Path) -> None:
    runtime = _make_runtime(tmp_path)
    args = _bundle_args(runtime)
    assert "--add-binary" in args
    assert any("tesseract.exe;runtime\\tesseract" in arg for arg in args)
    assert any("pdftoppm.exe;runtime\\poppler" in arg for arg in args)
    assert any("libtesseract.dll;runtime\\tesseract" in arg for arg in args)
    assert any("poppler.dll;runtime\\poppler" in arg for arg in args)
    assert any("deu.traineddata;runtime\\tesseract\\tessdata" in arg for arg in args)


def test_pyinstaller_args_fail_closed_when_runtime_is_incomplete(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        _bundle_args(tmp_path / "runtime")
