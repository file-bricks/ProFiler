from __future__ import annotations

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read_version_from_pyproject() -> str:
    content = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None
    return match.group(1)


def test_store_package_matches_project_metadata() -> None:
    package = json.loads((PROJECT_ROOT / "store_package.json").read_text(encoding="utf-8"))

    assert package["app_name"] == "ProFiler Suite"
    assert package["identity_name"] == "Geiger.ProFilerSuite"
    assert package["executable"] == "ProFiler.exe"
    assert package["capabilities"] == "runFullTrust"
    assert package["category"] == "Productivity"
    assert package["license"] == "AGPL-3.0-only"
    assert package["version"] == f"{_read_version_from_pyproject()}.0"
    assert package["privacy_url"].endswith("/PRIVACY_POLICY.md")
    assert package["support_url"].endswith("/SUPPORT.md")


def test_store_documents_reference_local_data_and_license_notes() -> None:
    listing = (PROJECT_ROOT / "STORE_LISTING.md").read_text(encoding="utf-8")
    privacy = (PROJECT_ROOT / "PRIVACY_POLICY.md").read_text(encoding="utf-8")
    support = (PROJECT_ROOT / "SUPPORT.md").read_text(encoding="utf-8")
    prep = (PROJECT_ROOT / "WINDOWS_STORE_PREP.md").read_text(encoding="utf-8")

    assert "LOCALAPPDATA" in listing
    assert "PyMuPDF" in listing
    assert "Tesseract" in listing
    assert "AGPL-3.0" in listing
    assert "https://github.com/file-bricks/ProFiler/blob/main/PRIVACY_POLICY.md" in listing
    assert "https://github.com/file-bricks/ProFiler/blob/main/SUPPORT.md" in listing
    assert "PyMuPDF" in privacy
    assert "Tesseract" in privacy
    assert "https://github.com/file-bricks/ProFiler/issues" in support
    assert "LOCALAPPDATA\\ProFilerSuite" in prep
    assert "THIRD_PARTY_LICENSES.txt" in prep


def test_existing_main_screenshot_is_present() -> None:
    assert (PROJECT_ROOT / "screenshots" / "main.png").exists()


def test_store_readiness_script_reports_clean_state() -> None:
    namespace: dict = {"__file__": str(PROJECT_ROOT / "scripts" / "check_store_readiness.py")}
    script = (PROJECT_ROOT / "scripts" / "check_store_readiness.py").read_text(encoding="utf-8")
    exec(script, namespace)
    assert namespace["evaluate_store_readiness"]() == []
