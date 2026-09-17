"""Emit deterministic PyInstaller arguments for the OCR runtime contract."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_FILES = (
    Path("tesseract") / "tesseract.exe",
    Path("poppler") / "pdftoppm.exe",
    Path("poppler") / "pdfinfo.exe",
)


def _bundle_args(runtime_root: Path) -> list[str]:
    runtime_root = runtime_root.resolve()
    missing = [runtime_root / relative for relative in REQUIRED_FILES if not (runtime_root / relative).is_file()]
    tessdata = runtime_root / "tesseract" / "tessdata"
    if not tessdata.is_dir():
        missing.append(tessdata)
    if missing:
        missing_text = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"OCR runtime contract incomplete: {missing_text}")

    args: list[str] = []
    for relative in REQUIRED_FILES:
        source = runtime_root / relative
        destination = "runtime\\" + str(relative.parent).replace("/", "\\")
        args.extend(("--add-binary", f'"{source};{destination}"'))

    for runtime_dir in (runtime_root / "tesseract", runtime_root / "poppler"):
        for source in sorted(runtime_dir.rglob("*.dll")):
            relative = source.relative_to(runtime_root)
            destination = "runtime\\" + str(relative.parent).replace("/", "\\")
            args.extend(("--add-binary", f'"{source};{destination}"'))

    for source in sorted(tessdata.rglob("*")):
        if source.is_file():
            relative = source.relative_to(runtime_root / "tesseract")
            destination = "runtime\\tesseract\\" + str(relative.parent).replace("/", "\\")
            args.extend(("--add-data", f'"{source};{destination}"'))
    return args


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(" ".join(_bundle_args(args.runtime_root)))
    except FileNotFoundError as exc:
        print(f"[ocr-bundle] FEHLER: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
