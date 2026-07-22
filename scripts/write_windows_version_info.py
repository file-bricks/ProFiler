"""Generate the PyInstaller Windows version resource from the canonical version."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from version import APP_VERSION  # noqa: E402


def write_version_info(output: Path) -> None:
    parts = tuple(int(part) for part in APP_VERSION.split("."))
    if len(parts) != 3:
        raise ValueError("APP_VERSION muss drei numerische Teile besitzen")
    file_version = (*parts, 0)
    dotted = f"{APP_VERSION}.0"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={file_version}, prodvers={file_version}, mask=0x3f,
    flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)
  ),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'file-bricks'),
      StringStruct('FileDescription', 'ProFiler Suite'),
      StringStruct('FileVersion', '{dotted}'),
      StringStruct('InternalName', 'ProFiler'),
      StringStruct('LegalCopyright', 'Copyright file-bricks contributors'),
      StringStruct('OriginalFilename', 'ProFiler.exe'),
      StringStruct('ProductName', 'ProFiler Suite'),
      StringStruct('ProductVersion', '{dotted}')
    ])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    write_version_info(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
