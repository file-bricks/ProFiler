from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dependency_versions_no_vulnerable_floors() -> None:
    """Ensure dependency version floors mitigate known CVEs/GHSAs."""
    pyproject_path = ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml missing"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    deps = data["project"].get("dependencies", [])

    # Pillow must be >= 12.3.0 to mitigate 26 CVEs/GHSAs in <= 12.2.0 (GHSA-4x4j-2g7c-83w6, GHSA-45hq-cxwh-f6vc)
    assert any("Pillow>=12.3" in dep for dep in deps), f"Vulnerable Pillow floor in {deps}"
    assert any("PySide6>=6.5" in dep for dep in deps), f"PySide6 floor missing in {deps}"

    # Dev dependencies must enforce safe pytest >= 9.1.1 (guards against GHSA-6w46-j5rx-g56g / CVE-2025-7117)
    opt_deps = data["project"].get("optional-dependencies", {})
    dev_deps = opt_deps.get("dev", [])
    assert any("pytest>=9.1" in dep for dep in dev_deps), f"Vulnerable pytest floor in {dev_deps}"

    # requirements.txt must also enforce safe Pillow >= 12.3.0
    req_text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "Pillow>=12.3" in req_text, "requirements.txt missing safe Pillow>=12.3 floor"


def test_third_party_license_inventory_metadata() -> None:
    """Ensure THIRD_PARTY_LICENSES.txt is current and covers all direct and toolchain packages."""
    license_file = ROOT / "THIRD_PARTY_LICENSES.txt"
    assert license_file.exists(), "THIRD_PARTY_LICENSES.txt is missing"
    text = license_file.read_text(encoding="utf-8")

    assert "Last reviewed: 2026-09-07" in text
    assert "AGPL-3.0-only" in text
    assert "pypdf" in text and "6.15.0" in text

    # All direct runtime dependencies must be explicitly cataloged
    for pkg in [
        "pyside6",
        "pypdf",
        "pikepdf",
        "pymupdf",
        "pdf2image",
        "python-docx",
        "pytesseract",
        "pillow",
        "watchdog",
        "reportlab",
    ]:
        assert pkg in text.lower(), f"Missing direct dependency entry in THIRD_PARTY_LICENSES.txt: {pkg}"

    # Build and test dependencies
    for pkg in ["pyinstaller", "altgraph", "packaging", "pluggy", "iniconfig", "pytest"]:
        assert pkg in text.lower(), f"Missing toolchain entry in THIRD_PARTY_LICENSES.txt: {pkg}"


def test_security_policy_bilingual_and_contacts() -> None:
    """Ensure SECURITY.md is bilingual, provides contact SLA, and defines security invariants."""
    sec_file = ROOT / "SECURITY.md"
    assert sec_file.exists(), "SECURITY.md is missing"
    text = sec_file.read_text(encoding="utf-8")

    assert "## English" in text
    assert "## Deutsch" in text
    assert "15.0.x" in text
    assert "48 hours" in text or "48 Stunden" in text
    assert "security@open-bricks.org" in text
    assert "support@lukasgeiger.com" in text
    assert "Zero-Egress" in text
    assert "Local-First" in text
    assert "Non-Elevation" in text or "Unprivilegierter Betrieb" in text


def test_repo_hygiene_and_gitignore_rules() -> None:
    """Ensure sensitive files, sync conflicts, and locks are excluded from git tracking."""
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "LOCK*.txt" in gitignore
    assert "LOCK.permissions.json" in gitignore
    assert "*-WORKSTATION-LG*" in gitignore
    assert "*-ASUS-GEI*" in gitignore
    assert "*.conflict" in gitignore
    assert "*.sync-conflict-*" in gitignore
    assert ".env" in gitignore
    assert "credentials.json" in gitignore
    assert "token.json" in gitignore


def test_no_hardcoded_user_paths_or_plaintext_secrets() -> None:
    """Ensure no personal developer user paths or plaintext credentials exist in application code."""
    secret_regex = re.compile(r"(?i)(api[_-]?key|secret|password|bearer)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]")
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
