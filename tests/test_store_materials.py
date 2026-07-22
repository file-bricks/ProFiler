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
    assert "https://github.com/file-bricks/ProFiler/blob/master/PRIVACY_POLICY.md" in listing
    assert "https://github.com/file-bricks/ProFiler/blob/master/SUPPORT.md" in listing
    assert "PyMuPDF" in privacy
    assert "Tesseract" in privacy
    assert "https://github.com/file-bricks/ProFiler/issues" in support
    assert "LOCALAPPDATA\\ProFilerSuite" in prep
    assert "THIRD_PARTY_LICENSES.txt" in prep


def test_existing_main_screenshot_is_present() -> None:
    assert (PROJECT_ROOT / "screenshots" / "main.png").exists()
    assert (PROJECT_ROOT / "README" / "screenshots" / "main.png").exists()


def test_readmes_reference_policy_screenshot_path() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README_de.md").read_text(encoding="utf-8")

    assert "README/screenshots/main.png" in readme
    assert "README/screenshots/main.png" in readme_de


def test_desktop_release_materials_point_to_local_build_flow() -> None:
    build_script = (PROJECT_ROOT / "build_exe.bat").read_text(encoding="utf-8")
    start_script = (PROJECT_ROOT / "START.bat").read_text(encoding="utf-8")
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert r"C:\_Local_DEV\codex_build\profiler" in build_script
    assert "build_exclude_scanner.py" in build_script
    assert "from version import APP_VERSION" in (PROJECT_ROOT / "scripts" / "write_build_provenance.py").read_text(encoding="utf-8")
    assert "BUILD-PROVENANCE.json" in build_script
    assert "Profiler_Suite_V15.py" in start_script
    assert "ProFiler.exe" in start_script
    assert "LOCK*.txt" in gitignore
    assert "LOCK.permissions.json" in gitignore
    assert "*.bak" in gitignore


def test_store_readiness_script_reports_clean_state() -> None:
    namespace: dict = {"__file__": str(PROJECT_ROOT / "scripts" / "check_store_readiness.py")}
    script = (PROJECT_ROOT / "scripts" / "check_store_readiness.py").read_text(encoding="utf-8")
    exec(script, namespace)
    assert namespace["evaluate_store_readiness"]() == []
