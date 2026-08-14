from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app_paths import APP_DATA_DIRNAME, app_data_dir
from version import APP_VERSION

PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
STORE_PACKAGE_PATH = PROJECT_ROOT / "store_package.json"


def read_pyproject_version() -> str:
    content = PYPROJECT_PATH.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if match is None:
        raise ValueError("version fehlt in pyproject.toml")
    return match.group(1)


def load_store_package() -> dict:
    return json.loads(STORE_PACKAGE_PATH.read_text(encoding="utf-8"))


def evaluate_store_readiness() -> list[str]:
    findings: list[str] = []
    package = load_store_package()
    project_version = read_pyproject_version()
    if project_version != APP_VERSION:
        findings.append(f"pyproject-Version stimmt nicht mit version.py überein: {project_version} != {APP_VERSION}")
    expected_version = f"{APP_VERSION}.0"

    if package.get("version") != expected_version:
        findings.append(f"Version stimmt nicht: {package.get('version')} != {expected_version}")

    if package.get("capabilities") != "runFullTrust":
        findings.append("Store-Paket braucht runFullTrust für lokale Desktop-Workflows.")

    expected_data_dir = str(
        app_data_dir(platform="nt", env={"LOCALAPPDATA": r"C:\Users\User\AppData\Local"})
    )
    if not expected_data_dir.endswith(APP_DATA_DIRNAME):
        findings.append("AppData-Pfad endet nicht auf ProFilerSuite.")

    for required in ("STORE_LISTING.md", "PRIVACY_POLICY.md", "SUPPORT.md", "WINDOWS_STORE_PREP.md"):
        if not (PROJECT_ROOT / required).exists():
            findings.append(f"Fehlende Store-Datei: {required}")

    expected_urls = {
        "privacy_url": "https://github.com/file-bricks/ProFiler/blob/master/PRIVACY_POLICY.md",
        "support_url": "https://github.com/file-bricks/ProFiler/blob/master/SUPPORT.md",
    }
    for key, expected in expected_urls.items():
        if package.get(key) != expected:
            findings.append(f"{key} stimmt nicht: {package.get(key)!r}")

    return findings


def main() -> int:
    findings = evaluate_store_readiness()
    if findings:
        print("STORE MATERIAL BASELINE: WARN")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("STORE MATERIAL BASELINE: OK (nicht einreichungsbereit)")
    print(f"- version: {read_pyproject_version()}.0")
    sample_appdata = app_data_dir(
        platform="nt",
        env={"LOCALAPPDATA": "C:\\Users\\User\\AppData\\Local"},
    )
    print(f"- appdata: {sample_appdata}")
    print("- docs: STORE_LISTING.md, PRIVACY_POLICY.md, SUPPORT.md, WINDOWS_STORE_PREP.md")
    print("- offen: signiertes MSIX, Paket-Bundle, WACK, installierte OCR/PDF-Smokes, Partner Center")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
