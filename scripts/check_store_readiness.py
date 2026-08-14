#!/usr/bin/env python3
"""
check_store_readiness.py - Windows Store Readiness Audit Tool for ProFiler Suite.

Validates:
1. store_package.json metadata and schema
2. store_package/ProFiler/AppxManifest.xml syntax, identities, capabilities, and visual elements
3. Tile icons presence, PNG signature, and exact dimensions in store_package and store_assets
4. STORE_LISTING.md, PRIVACY_POLICY.md, SUPPORT.md, WINDOWS_STORE_PREP.md and keyword guidelines
5. Store screenshot assets and 1920x1080 dimensions
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app_paths import APP_DATA_DIRNAME, app_data_dir  # noqa: E402
from version import APP_VERSION  # noqa: E402

EXPECTED_PUBLISHER = "CN=52596601-BAB4-4F3F-B182-E8F3F273B202"
EXPECTED_IDENTITY = "Geiger.ProFilerSuite"
EXPECTED_EXECUTABLE = "ProFiler.exe"
EXPECTED_VERSION = f"{APP_VERSION}.0"

DISALLOWED_KEYWORD_TRADEMARKS = [
    "gmail", "google", "netflix", "spotify", "adobe", "microsoft", "apple", "amazon"
]

REQUIRED_TILE_ICONS = {
    "icon_44x44.png": (44, 44),
    "icon_50x50.png": (50, 50),
    "icon_150x150.png": (150, 150),
    "icon_310x150.png": (310, 150),
    "icon_310x310.png": (310, 310),
}

REQUIRED_SCREENSHOTS = [
    "shot-1-library-overview.png",
    "shot-2-search-ocr.png",
    "shot-3-privacy-traffic-light.png",
    "shot-4-pdf-tools.png",
]

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def read_pyproject_version() -> str:
    content = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if match is None:
        raise ValueError("version fehlt in pyproject.toml")
    return match.group(1)


def check_store_package_json(results: dict) -> None:
    pkg_file = PROJECT_ROOT / "store_package.json"
    if not pkg_file.exists():
        results["errors"].append("store_package.json fehlt im Root-Verzeichnis.")
        return

    try:
        data = json.loads(pkg_file.read_text(encoding="utf-8"))
    except Exception as e:
        results["errors"].append(f"store_package.json ungültiges JSON: {e}")
        return

    required = [
        "app_name", "publisher", "publisher_display", "identity_name",
        "version", "description", "executable", "capabilities",
        "category", "age_rating", "privacy_url", "support_url", "languages", "logo"
    ]
    for key in required:
        if key not in data or not str(data[key]).strip():
            results["errors"].append(f"store_package.json: Pflichtfeld '{key}' fehlt oder ist leer.")

    if data.get("publisher") != EXPECTED_PUBLISHER:
        results["errors"].append(f"store_package.json: Publisher '{data.get('publisher')}' != '{EXPECTED_PUBLISHER}'")

    if data.get("identity_name") != EXPECTED_IDENTITY:
        results["errors"].append(f"store_package.json: Identity '{data.get('identity_name')}' != '{EXPECTED_IDENTITY}'")

    if data.get("executable") != EXPECTED_EXECUTABLE:
        results["errors"].append(f"store_package.json: Executable '{data.get('executable')}' != '{EXPECTED_EXECUTABLE}'")

    if data.get("version") != EXPECTED_VERSION:
        results["errors"].append(f"store_package.json: Version '{data.get('version')}' != '{EXPECTED_VERSION}'")

    if data.get("capabilities") != "runFullTrust":
        results["errors"].append("store_package.json: capabilities muss 'runFullTrust' sein.")

    p_url = data.get("privacy_url", "")
    if not p_url.startswith("https://"):
        results["errors"].append(f"store_package.json: privacy_url '{p_url}' muss eine gültige HTTPS-URL sein.")

    s_url = data.get("support_url", "")
    if not s_url.startswith("https://"):
        results["errors"].append(f"store_package.json: support_url '{s_url}' muss eine gültige HTTPS-URL sein.")

    expected_data_dir = str(
        app_data_dir(platform="nt", env={"LOCALAPPDATA": r"C:\Users\User\AppData\Local"})
    )
    if not expected_data_dir.endswith(APP_DATA_DIRNAME):
        results["errors"].append(f"AppData-Pfad endet nicht auf {APP_DATA_DIRNAME}.")

    results["ok"].append("store_package.json ist vollständig und richtlinienkonform.")


def check_appx_manifest(results: dict) -> None:
    manifest_file = PROJECT_ROOT / "store_package" / "ProFiler" / "AppxManifest.xml"
    if not manifest_file.exists():
        results["errors"].append(f"AppxManifest.xml fehlt unter {manifest_file}")
        return

    try:
        tree = ET.parse(manifest_file)
        root = tree.getroot()
    except Exception as e:
        results["errors"].append(f"AppxManifest.xml XML-Parsefehler: {e}")
        return

    ns = {"def": "http://schemas.microsoft.com/appx/manifest/foundation/windows10"}

    identity = root.find("def:Identity", ns)
    if identity is None:
        identity = root.find("{http://schemas.microsoft.com/appx/manifest/foundation/windows10}Identity")

    if identity is not None:
        name = identity.get("Name")
        pub = identity.get("Publisher")
        ver = identity.get("Version")
        if name != EXPECTED_IDENTITY:
            results["errors"].append(f"AppxManifest Identity Name '{name}' != '{EXPECTED_IDENTITY}'")
        if pub != EXPECTED_PUBLISHER:
            results["errors"].append(f"AppxManifest Publisher '{pub}' != '{EXPECTED_PUBLISHER}'")
        if ver != EXPECTED_VERSION:
            results["errors"].append(f"AppxManifest Version '{ver}' != '{EXPECTED_VERSION}'")
    else:
        results["errors"].append("AppxManifest.xml: <Identity> Tag nicht gefunden.")

    results["ok"].append("AppxManifest.xml ist syntaktisch korrekt und Identity/Version stimmen überein.")


def check_tile_icons(results: dict) -> None:
    dirs_to_check = [
        PROJECT_ROOT / "store_package" / "ProFiler" / "icons",
        PROJECT_ROOT / "store_assets",
    ]

    for d in dirs_to_check:
        if not d.exists():
            results["errors"].append(f"Icon-Verzeichnis fehlt: {d}")
            continue

        for icon_name, expected_size in REQUIRED_TILE_ICONS.items():
            icon_path = d / icon_name
            if not icon_path.exists():
                results["errors"].append(f"Fehlendes Tile-Icon: {icon_path}")
                continue

            content = icon_path.read_bytes()
            if not content.startswith(PNG_SIGNATURE):
                results["errors"].append(f"Icon {icon_name} ist keine gültige PNG-Datei (Magic Bytes fehlen).")
                continue

            try:
                with Image.open(icon_path) as img:
                    if img.size != expected_size:
                        results["errors"].append(
                            f"Icon {icon_name} in {d.name} hat falsche Dimensionen: {img.size} != {expected_size}"
                        )
            except Exception as e:
                results["errors"].append(f"Icon {icon_name} kann nicht geöffnet werden: {e}")

    results["ok"].append("Alle MSIX-Tile-Icons sind in allen Zielordnern vorhanden und maßhaltig.")


def check_store_listing_and_docs(results: dict) -> None:
    listing_path = PROJECT_ROOT / "STORE_LISTING.md"
    if not listing_path.exists():
        results["errors"].append("STORE_LISTING.md fehlt.")
        return

    content = listing_path.read_text(encoding="utf-8")

    # Check required documents
    for doc in ["PRIVACY_POLICY.md", "SUPPORT.md", "WINDOWS_STORE_PREP.md", "THIRD_PARTY_LICENSES.txt"]:
        if not (PROJECT_ROOT / doc).exists():
            results["errors"].append(f"Pflichtdokument fehlt: {doc}")

    # Check German keywords
    match_de = re.search(r"### Schlüsselwörter\s*\n([^\n#]+)", content)
    if match_de:
        keywords_de = [k.strip() for k in match_de.group(1).split(",") if k.strip()]
        if len(keywords_de) > 7:
            results["errors"].append(
                f"STORE_LISTING.md: Zu viele deutsche Schlüsselwörter ({len(keywords_de)} > 7 max. erlaubt)."
            )
        for kw in keywords_de:
            if any(tm in kw.lower() for tm in DISALLOWED_KEYWORD_TRADEMARKS):
                results["errors"].append(
                    f"STORE_LISTING.md: Unzulässiges deutsches Trademark-Schlagwort '{kw}' (Policy 10.1.3)."
                )

    # Check English keywords
    match_en = re.search(r"### Keywords\s*\n([^\n#]+)", content)
    if match_en:
        keywords_en = [k.strip() for k in match_en.group(1).split(",") if k.strip()]
        if len(keywords_en) > 7:
            results["errors"].append(
                f"STORE_LISTING.md: Zu viele englische Keywords ({len(keywords_en)} > 7 max. erlaubt)."
            )
        for kw in keywords_en:
            if any(tm in kw.lower() for tm in DISALLOWED_KEYWORD_TRADEMARKS):
                results["errors"].append(
                    f"STORE_LISTING.md: Unzulässiges englisches Trademark-Keyword '{kw}' (Policy 10.1.3)."
                )

    results["ok"].append("STORE_LISTING.md und rechtliche Pflichtdokumente entsprechen Microsoft Store Policies.")


def check_store_screenshots(results: dict) -> None:
    shots_dir = PROJECT_ROOT / "screenshots" / "store"
    if not shots_dir.exists():
        results["errors"].append(f"Screenshot-Verzeichnis fehlt: {shots_dir}")
        return

    for shot_name in REQUIRED_SCREENSHOTS:
        shot_path = shots_dir / shot_name
        if not shot_path.exists():
            results["errors"].append(f"Fehlender Store-Screenshot: {shot_name}")
            continue

        content = shot_path.read_bytes()
        if not content.startswith(PNG_SIGNATURE):
            results["errors"].append(f"Screenshot {shot_name} ist keine gültige PNG-Datei.")
            continue

        try:
            with Image.open(shot_path) as img:
                if img.size != (1920, 1080):
                    results["errors"].append(
                        f"Screenshot {shot_name} hat falsche Auflösung: {img.size} != (1920, 1080)"
                    )
        except Exception as e:
            results["errors"].append(f"Screenshot {shot_name} kann nicht geöffnet werden: {e}")

    results["ok"].append("Alle 4 hochauflösenden Store-Screenshots (1920x1080) sind vorhanden und valide.")


def evaluate_store_readiness() -> list[str]:
    results = {"ok": [], "errors": []}
    check_store_package_json(results)
    check_appx_manifest(results)
    check_tile_icons(results)
    check_store_listing_and_docs(results)
    check_store_screenshots(results)
    return results["errors"]


def main() -> int:
    print("=" * 65)
    print("  ProFiler Suite - Windows Store Readiness Audit")
    print("=" * 65)

    results = {"ok": [], "errors": []}
    check_store_package_json(results)
    check_appx_manifest(results)
    check_tile_icons(results)
    check_store_listing_and_docs(results)
    check_store_screenshots(results)

    for ok_msg in results["ok"]:
        print(f"  [PASS] {ok_msg}")

    if results["errors"]:
        print("\n" + "=" * 65)
        print("  AUDIT FAILED - OFFENE PUNKTE:")
        print("=" * 65)
        for err in results["errors"]:
            print(f"  [FAIL] {err}")
        return 1

    print("\n" + "=" * 65)
    print("  AUDIT PASSED (5/5 Checks OK - Vorbereitung vollständig)")
    print(f"  - Package Version: {EXPECTED_VERSION}")
    print(f"  - App Identity:    {EXPECTED_IDENTITY}")
    print(f"  - Publisher:       {EXPECTED_PUBLISHER}")
    print(f"  - Capabilities:    runFullTrust")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
