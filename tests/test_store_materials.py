from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_PUBLISHER = "CN=52596601-BAB4-4F3F-B182-E8F3F273B202"
EXPECTED_IDENTITY = "Geiger.ProFilerSuite"


def _read_version_from_pyproject() -> str:
    content = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None
    return match.group(1)


def test_store_package_matches_project_metadata() -> None:
    package = json.loads((PROJECT_ROOT / "store_package.json").read_text(encoding="utf-8"))

    assert package["app_name"] == "ProFiler Suite"
    assert package["identity_name"] == EXPECTED_IDENTITY
    assert package["publisher"] == EXPECTED_PUBLISHER
    assert package["executable"] == "ProFiler.exe"
    assert package["capabilities"] == "runFullTrust"
    assert package["category"] == "Productivity"
    assert package["license"] == "AGPL-3.0-only"
    assert package["version"] == f"{_read_version_from_pyproject()}.0"
    assert package["privacy_url"].endswith("/PRIVACY_POLICY.md")
    assert package["support_url"].endswith("/SUPPORT.md")
    assert "de-DE" in package["languages"]
    assert "en-US" in package["languages"]


def test_appx_manifest_structure_and_identity() -> None:
    manifest_file = PROJECT_ROOT / "store_package" / "ProFiler" / "AppxManifest.xml"
    assert manifest_file.exists()

    tree = ET.parse(manifest_file)
    root = tree.getroot()

    ns = {"def": "http://schemas.microsoft.com/appx/manifest/foundation/windows10"}
    identity = root.find("def:Identity", ns)
    if identity is None:
        identity = root.find("{http://schemas.microsoft.com/appx/manifest/foundation/windows10}Identity")

    assert identity is not None
    assert identity.get("Name") == EXPECTED_IDENTITY
    assert identity.get("Publisher") == EXPECTED_PUBLISHER
    assert identity.get("Version") == f"{_read_version_from_pyproject()}.0"
    assert identity.get("ProcessorArchitecture") == "x64"


def test_store_tile_icons_dimensions_and_validity() -> None:
    required_icons = {
        "icon_44x44.png": (44, 44),
        "icon_50x50.png": (50, 50),
        "icon_150x150.png": (150, 150),
        "icon_310x150.png": (310, 150),
        "icon_310x310.png": (310, 310),
    }

    dirs = [
        PROJECT_ROOT / "store_package" / "ProFiler" / "icons",
        PROJECT_ROOT / "store_assets",
    ]

    for d in dirs:
        assert d.exists()
        for icon_name, expected_dim in required_icons.items():
            icon_path = d / icon_name
            assert icon_path.exists(), f"Missing icon: {icon_path}"
            with Image.open(icon_path) as img:
                assert img.format == "PNG"
                assert img.size == expected_dim


def test_store_screenshots_resolution_and_format() -> None:
    required_shots = [
        "shot-1-library-overview.png",
        "shot-2-search-ocr.png",
        "shot-3-privacy-traffic-light.png",
        "shot-4-pdf-tools.png",
    ]

    shots_dir = PROJECT_ROOT / "screenshots" / "store"
    assert shots_dir.exists()

    for shot_name in required_shots:
        shot_path = shots_dir / shot_name
        assert shot_path.exists()
        with Image.open(shot_path) as img:
            assert img.format == "PNG"
            assert img.size == (1920, 1080)


def test_store_listing_keyword_policies() -> None:
    listing = (PROJECT_ROOT / "STORE_LISTING.md").read_text(encoding="utf-8")

    # DE keywords <= 7
    match_de = re.search(r"### Schlüsselwörter\s*\n([^\n#]+)", listing)
    assert match_de is not None
    keywords_de = [k.strip() for k in match_de.group(1).split(",") if k.strip()]
    assert 1 <= len(keywords_de) <= 7

    # EN keywords <= 7
    match_en = re.search(r"### Keywords\s*\n([^\n#]+)", listing)
    assert match_en is not None
    keywords_en = [k.strip() for k in match_en.group(1).split(",") if k.strip()]
    assert 1 <= len(keywords_en) <= 7


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
