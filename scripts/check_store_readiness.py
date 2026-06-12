from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app_paths import APP_DATA_DIRNAME, app_data_dir

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


def evaluate_store_readiness() -> List[str]:
    findings: List[str] = []
    package = load_store_package()
    expected_version = f"{read_pyproject_version()}.0"

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

    return findings


def main() -> int:
    findings = evaluate_store_readiness()
    if findings:
        print("STORE READINESS: WARN")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("STORE READINESS: OK")
    print(f"- version: {read_pyproject_version()}.0")
    print(
        f"- appdata: {app_data_dir(platform='nt', env={'LOCALAPPDATA': r'C:\\Users\\User\\AppData\\Local'})}"
    )
    print("- docs: STORE_LISTING.md, PRIVACY_POLICY.md, SUPPORT.md, WINDOWS_STORE_PREP.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
