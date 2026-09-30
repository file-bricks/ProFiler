"""Security, licensing, dependency floor, and privacy contract tests for ProFiler Suite."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dependency_security_minimum_floors() -> None:
    """Ensure dependency version floors mitigate known CVEs/GHSAs across pyproject and requirements."""
    pyproject_path = ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml missing"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    deps = data["project"].get("dependencies", [])
    opt_deps = data["project"].get("optional-dependencies", {})
    dev_deps = opt_deps.get("dev", [])
    authors = data["project"].get("authors", [])

    # Author support email contract
    assert any(a.get("email") == "support@lukasgeiger.com" for a in authors), "Missing support email in pyproject authors"

    # Pillow must be >= 12.3.0 to mitigate 26 CVEs/GHSAs in <= 12.2.0 (GHSA-4x4j-2g7c-83w6, GHSA-45hq-cxwh-f6vc)
    assert any("Pillow>=12.3" in dep for dep in deps), f"Vulnerable Pillow floor in {deps}"
    assert any("PySide6>=6.5" in dep for dep in deps), f"PySide6 floor missing in {deps}"
    assert any("pypdf>=6.14" in dep for dep in deps), f"pypdf floor missing in {deps}"
    assert any("pikepdf>=8.0" in dep for dep in deps), f"pikepdf floor missing in {deps}"
    assert any("PyMuPDF>=1.23" in dep for dep in deps), f"PyMuPDF floor missing in {deps}"
    assert any("reportlab>=4.0" in dep for dep in deps), f"reportlab floor missing in {deps}"

    # Dev dependencies must enforce safe pytest >= 9.1.1 (guards against GHSA-6w46-j5rx-g56g / CVE-2025-7117)
    assert any("pytest>=9.1.1" in dep for dep in dev_deps), f"Vulnerable pytest floor in {dev_deps}"
    assert any("ruff>=0.9.0" in dep for dep in dev_deps), f"ruff floor missing in {dev_deps}"
    assert any("pyinstaller>=6.10.0" in dep for dep in dev_deps), f"pyinstaller floor missing in {dev_deps}"
    assert any("altgraph>=0.17.4" in dep for dep in dev_deps), f"altgraph floor missing in {dev_deps}"
    assert any("packaging>=24.0" in dep for dep in dev_deps), f"packaging floor missing in {dev_deps}"

    # requirements.txt must also enforce safe runtime floors
    req_text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "Pillow>=12.3.0" in req_text
    assert "PySide6>=6.5.0" in req_text
    assert "pypdf>=6.14.2" in req_text
    assert "pikepdf>=8.0.0" in req_text
    assert "PyMuPDF>=1.23.0" in req_text
    assert "reportlab>=4.0.0" in req_text


def test_third_party_license_inventory_completeness() -> None:
    """Ensure THIRD_PARTY_LICENSES.txt follows the standardized 5-field schema and covers all dependencies."""
    license_file = ROOT / "THIRD_PARTY_LICENSES.txt"
    assert license_file.exists(), "THIRD_PARTY_LICENSES.txt is missing"
    text = license_file.read_text(encoding="utf-8")

    assert re.search(r"Stand:\s*2026-\d{2}-\d{2}", text), "Must contain valid 2026 audit date"
    assert "Stand: 2026-09-30" in text

    # Standard 5-field schema markers
    assert "Package:" in text
    assert "License:" in text
    assert "SPDX:" in text
    assert "URL:" in text
    assert "Notice:" in text

    # All direct runtime dependencies must be explicitly cataloged
    direct_packages = [
        "PySide6",
        "shiboken6",
        "pypdf",
        "pikepdf",
        "PyMuPDF",
        "pdf2image",
        "python-docx",
        "pytesseract",
        "Pillow",
        "watchdog",
        "reportlab",
    ]
    for pkg in direct_packages:
        assert f"Package: {pkg}" in text, f"Missing direct dependency entry in THIRD_PARTY_LICENSES.txt: {pkg}"

    # Optional packages
    for pkg in ["pandas", "openpyxl"]:
        assert f"Package: {pkg}" in text, f"Missing optional dependency entry in THIRD_PARTY_LICENSES.txt: {pkg}"

    # Build, test and packaging dependencies
    toolchain_packages = [
        "pytest",
        "pluggy",
        "iniconfig",
        "ruff",
        "PyInstaller",
        "pyinstaller-hooks-contrib",
        "altgraph",
        "packaging",
    ]
    for pkg in toolchain_packages:
        assert f"Package: {pkg}" in text, f"Missing toolchain entry in THIRD_PARTY_LICENSES.txt: {pkg}"

    # SPDX identifier validations
    assert "SPDX: LGPL-3.0-only" in text
    assert "SPDX: BSD-3-Clause" in text
    assert "SPDX: MPL-2.0" in text
    assert "SPDX: AGPL-3.0-or-later" in text
    assert "SPDX: MIT" in text
    assert "SPDX: Apache-2.0" in text
    assert "SPDX: HPND" in text
    assert "SPDX: GPL-2.0-or-later WITH Bootloader-Exception" in text


def test_security_policy_bilingual_and_contacts() -> None:
    """Ensure SECURITY.md is bilingual, provides contact SLA, and defines security invariants."""
    sec_file = ROOT / "SECURITY.md"
    assert sec_file.exists(), "SECURITY.md is missing"
    text = sec_file.read_text(encoding="utf-8")

    assert "## English" in text
    assert "## Deutsch" in text
    assert "15.0.x" in text
    assert "48 hours" in text or "48 Stunden" in text
    assert "5 business days" in text or "5 Werktagen" in text
    assert "security@file-bricks.org" in text
    assert "security@open-bricks.org" in text
    assert "security@ellmos.ai" in text
    assert "support@lukasgeiger.com" in text
    assert "https://github.com/file-bricks/ProFiler/security/advisories/new" in text
    assert "Zero-Egress" in text
    assert "Local-First" in text
    assert "Non-Elevation" in text or "Unprivilegierter Betrieb" in text
    assert "§ 521 BGB" in text
    assert "Haftung des Schenkers" in text


def test_repo_hygiene_and_gitignore_rules() -> None:
    """Ensure sensitive files, sync conflicts, and locks are excluded from git tracking."""
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "LOCK*.txt" in gitignore
    assert "LOCK.permissions.json" in gitignore
    assert "*-WORKSTATION-LG*" in gitignore
    assert "*-ASUS-GEI*" in gitignore
    assert "*.conflict" in gitignore
    assert "*-conflict-*" in gitignore
    assert ".env" in gitignore
    assert "credentials.json" in gitignore
    assert "client_secret*.json" in gitignore
    assert "token.json" in gitignore
    assert "secrets.*" in gitignore
    assert "*.pem" in gitignore
    assert "*.key" in gitignore
    assert "*.pfx" in gitignore
    assert "*.p12" in gitignore
    assert "*.cer" in gitignore
    assert "*.crt" in gitignore
    assert "keyring/" in gitignore
    assert "pytest_out.txt" in gitignore
    assert "pytest*.txt" in gitignore
    assert "*.bak" in gitignore
    assert "*.tmp" in gitignore


def test_no_hardcoded_user_paths_or_plaintext_secrets() -> None:
    """Ensure no personal developer user paths or plaintext credentials exist in application code."""
    secret_regex = re.compile(r"(?i)(api[_-]?key|bearer)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]")
    user_path_regex = re.compile(r"C:[/\\]Users[/\\]lukas", re.IGNORECASE)

    mock_test_files = {"test_app_paths.py", "test_workspace_exchange.py", "check_store_readiness.py"}

    for py_path in list(ROOT.glob("*.py")) + list((ROOT / "tests").glob("*.py")) + list((ROOT / "scripts").glob("*.py")):
        content = py_path.read_text(encoding="utf-8", errors="ignore")
        assert not user_path_regex.search(content), f"Hardcoded developer path in {py_path.name}"
        if py_path.name not in mock_test_files and "test" not in py_path.name:
            assert not secret_regex.search(content), f"Secret suspect in {py_path.name}"


def test_license_parity_across_manifests() -> None:
    """Ensure AGPL-3.0 license parity across LICENSE, pyproject.toml, and documentation."""
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "GNU AFFERO GENERAL PUBLIC LICENSE" in license_text
    assert "Version 3" in license_text

    pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'text = "AGPL-3.0"' in pyproject_text
    assert "License :: OSI Approved :: GNU Affero General Public License v3" in pyproject_text


def test_local_first_and_offline_invariants() -> None:
    """Ensure zero network analytics or third-party telemetry endpoints exist in source code."""
    disallowed_patterns = [
        re.compile(r"google-analytics\.com", re.IGNORECASE),
        re.compile(r"mixpanel\.com", re.IGNORECASE),
        re.compile(r"segment\.io", re.IGNORECASE),
        re.compile(r"sentry\.io", re.IGNORECASE),
    ]

    py_files = [f for f in ROOT.glob("*.py") if f.is_file()]
    assert len(py_files) >= 5, "Expected at least 5 top-level Python files"

    for py_file in py_files:
        text = py_file.read_text(encoding="utf-8")
        for pat in disallowed_patterns:
            assert not pat.search(text), f"Disallowed telemetry pattern {pat.pattern} found in {py_file.name}"


def test_user_assets_zero_copyleft_and_linking() -> None:
    """Verify user assets zero-copyleft guarantee and PySide6 dynamic linking in inventory."""
    tp_text = (ROOT / "THIRD_PARTY_LICENSES.txt").read_text(encoding="utf-8")
    tp_md = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")

    assert "Zero-Copyleft" in tp_text or "KEINE Lizenzinfektion" in tp_text
    assert "Zero-Copyleft on User Data" in tp_md
    assert "LGPL-3.0 § 4" in tp_text
    assert "dynamisch gebunden" in tp_text.lower()
    assert "INV-LOCAL-01" in tp_text
    assert "INV-SLA-10" in tp_text
