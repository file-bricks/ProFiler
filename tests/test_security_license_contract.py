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
    """Check dependency declarations are grouped by runtime and development role."""
    license_file = ROOT / "THIRD_PARTY_LICENSES.txt"
    assert license_file.exists(), "THIRD_PARTY_LICENSES.txt is missing"
    text = license_file.read_text(encoding="utf-8")

    direct_section, optional_section = text.split("OPTIONAL AND DEVELOPMENT REQUIREMENTS", 1)
    assert "GNU Affero General Public License version 3" in text
    assert "DIRECT RUNTIME REQUIREMENTS" in direct_section

    # Declared direct runtime dependencies are named in the bounded notes.
    direct_packages = [
        "PySide6",
        "pypdf",
        "pikepdf",
        "PyMuPDF",
        "pdf2image",
        "python-docx",
        "pytesseract",
        "Pillow",
        "watchdog",
        "ReportLab",
    ]
    for pkg in direct_packages:
        assert pkg in direct_section, f"Missing direct dependency entry in THIRD_PARTY_LICENSES.txt: {pkg}"

    # Optional and development tools are distinguished from runtime packages.
    for pkg in ["pandas", "openpyxl"]:
        assert pkg in optional_section, f"Missing optional dependency entry in THIRD_PARTY_LICENSES.txt: {pkg}"

    toolchain_packages = [
        "pytest",
        "ruff",
        "PyInstaller",
        "altgraph",
        "packaging",
    ]
    for pkg in toolchain_packages:
        assert pkg in optional_section, f"Missing development/build tool in THIRD_PARTY_LICENSES.txt: {pkg}"


def test_security_policy_bilingual_and_contacts() -> None:
    """Ensure SECURITY.md keeps bilingual reporting channels and contact routes."""
    sec_file = ROOT / "SECURITY.md"
    assert sec_file.exists(), "SECURITY.md is missing"
    text = sec_file.read_text(encoding="utf-8")

    assert "## English" in text
    assert "## Deutsch" in text
    assert "15.0.2" in text
    assert "security@file-bricks.org" in text
    assert "security@open-bricks.org" in text
    assert "security@ellmos.ai" in text
    assert "support@lukasgeiger.com" in text
    assert "https://github.com/file-bricks/ProFiler/security/advisories/new" in text


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
    """Ensure the AGPL-3-only grant matches SPDX metadata and packaged license files."""
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "GNU AFFERO GENERAL PUBLIC LICENSE" in license_text
    assert "Version 3" in license_text

    pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'license = "AGPL-3.0-only"' in pyproject_text
    assert 'license-files = ["LICENSE", "NOTICE", "THIRD_PARTY_LICENSES.md", "THIRD_PARTY_LICENSES.txt"]' in pyproject_text
    for path in ("LICENSE", "NOTICE", "THIRD_PARTY_LICENSES.md", "THIRD_PARTY_LICENSES.txt"):
        assert (ROOT / path).is_file(), f"Declared license file is missing: {path}"


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


def test_native_bundle_requirements_are_recorded() -> None:
    """Keep external OCR/PDF bundle paths explicit in dependency notes."""
    text = (ROOT / "THIRD_PARTY_LICENSES.txt").read_text(encoding="utf-8")
    for required_path in (
        "runtime/tesseract/tesseract.exe",
        "runtime/tesseract/tessdata/",
        "runtime/poppler/pdftoppm.exe",
        "runtime/poppler/pdfinfo.exe",
    ):
        assert required_path in text
