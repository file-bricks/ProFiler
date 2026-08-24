from __future__ import annotations

import ast
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_metadata_version_parity() -> None:
    """Verify version parity across version.py, pyproject.toml, store_package.json, and AppxManifest."""
    version_src = (PROJECT_ROOT / "version.py").read_text(encoding="utf-8")
    version_match = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', version_src)
    assert version_match is not None, "APP_VERSION not found in version.py"
    app_version = version_match.group(1)

    # pyproject.toml
    pyproject_text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    pyproject_match = re.search(r'version\s*=\s*"([^"]+)"', pyproject_text)
    assert pyproject_match is not None, "version not found in pyproject.toml"
    assert pyproject_match.group(1) == app_version, f"pyproject.toml version ({pyproject_match.group(1)}) does not match version.py ({app_version})"

    # store_package.json
    store_package = json.loads((PROJECT_ROOT / "store_package.json").read_text(encoding="utf-8"))
    assert store_package["version"] == f"{app_version}.0", f"store_package.json version ({store_package['version']}) mismatch"

    # AppxManifest.xml
    manifest_text = (PROJECT_ROOT / "store_package" / "ProFiler" / "AppxManifest.xml").read_text(encoding="utf-8")
    assert f'Version="{app_version}.0"' in manifest_text, f"AppxManifest.xml version does not match {app_version}.0"

    # CHANGELOG.md
    changelog_text = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"[{app_version}]" in changelog_text, f"CHANGELOG.md missing release section for [{app_version}]"

    # llms.txt
    llms_text = (PROJECT_ROOT / "llms.txt").read_text(encoding="utf-8")
    assert f"version.py` — canonical public version contract (`{app_version}`)" in llms_text


def test_required_documentation_and_manifests_exist() -> None:
    """Verify presence of core documentation and policy files."""
    required_files = [
        "README.md",
        "README_de.md",
        "LICENSE",
        "SECURITY.md",
        "CHANGELOG.md",
        "llms.txt",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "PRIVACY_POLICY.md",
        "SUPPORT.md",
        "STORE_LISTING.md",
        "WINDOWS_STORE_PREP.md",
        "store_package.json",
        "pyproject.toml",
    ]
    for filename in required_files:
        path = PROJECT_ROOT / filename
        assert path.is_file(), f"Required file '{filename}' is missing"
        assert path.stat().st_size > 50, f"Required file '{filename}' is unexpectedly small or empty"


def test_readme_and_readme_de_parity() -> None:
    """Verify bilingual parity, ecosystem badges, and mermaid architecture diagrams in READMEs."""
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README_de.md").read_text(encoding="utf-8")

    # Badges
    assert "file-bricks" in readme_en and "file-bricks" in readme_de
    assert "open-bricks" in readme_en and "open-bricks" in readme_de
    assert "llms.txt" in readme_en and "llms.txt" in readme_de
    assert "AGPL" in readme_en and "AGPL" in readme_de

    # Mermaid architecture diagram
    assert "```mermaid" in readme_en and "```mermaid" in readme_de
    assert "graph TD" in readme_en and "graph TD" in readme_de

    # LLM Note
    assert "llms.txt" in readme_en and "llms.txt" in readme_de


def test_llms_txt_structure() -> None:
    """Verify llms.txt structure, search keywords, and recent timestamp."""
    llms_text = (PROJECT_ROOT / "llms.txt").read_text(encoding="utf-8")
    assert "# ProFiler Suite" in llms_text
    assert "file-bricks/ProFiler" in llms_text
    assert "## Architecture" in llms_text or "## Primary Use" in llms_text
    assert "## Search Phrases" in llms_text
    assert "## Contract Boundaries" in llms_text
    assert "## Last-checked: 2026-" in llms_text


def test_utf8_python_files_integrity() -> None:
    """Verify all Python source files parse cleanly and are valid UTF-8."""
    py_files = list(PROJECT_ROOT.glob("*.py")) + list((PROJECT_ROOT / "tests").glob("*.py")) + list((PROJECT_ROOT / "scripts").glob("*.py"))
    assert len(py_files) > 10, "Expected at least 10 Python files in repository"
    for py_path in py_files:
        content = py_path.read_text(encoding="utf-8")
        ast.parse(content, filename=str(py_path))


def test_readme_quick_navigation_and_sequence_diagram_parity() -> None:
    """Verify quick navigation, sequence diagram, and security invariants table parity."""
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README_de.md").read_text(encoding="utf-8")

    # Quick navigation
    assert "### Quick Navigation" in readme_en
    assert "### Schnellnavigation" in readme_de

    # Sequence diagram
    assert "## Workflow Lifecycle" in readme_en
    assert "## Workflow-Lebenszyklus" in readme_de
    assert "sequenceDiagram" in readme_en and "sequenceDiagram" in readme_de
    assert "Datenschutzampel" in readme_en and "Datenschutzampel" in readme_de

    # Core capabilities & security invariants
    assert "## Core Capabilities & Security Invariants" in readme_en
    assert "## Kernfähigkeiten & Sicherheitsinvarianten" in readme_de
    assert "Zero-Egress" in readme_en and "Zero-Egress" in readme_de


def test_security_policy_structure_and_contacts() -> None:
    """Verify bilingual SECURITY.md structure, SLA, invariants, and contacts."""
    sec_text = (PROJECT_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "## English" in sec_text
    assert "## Deutsch" in sec_text
    assert "48 hours" in sec_text or "48 Stunden" in sec_text
    assert "security@open-bricks.org" in sec_text
    assert "support@lukasgeiger.com" in sec_text
    assert "Zero-Egress" in sec_text
    assert "security/advisories" in sec_text


def test_ci_workflow_concurrency_and_matrix() -> None:
    """Verify CI workflow has concurrency cancel-in-progress and multi-OS matrix."""
    ci_file = PROJECT_ROOT / ".github" / "workflows" / "source-platform-smoke.yml"
    assert ci_file.exists(), "CI workflow file missing"
    ci_text = ci_file.read_text(encoding="utf-8")
    assert "concurrency:" in ci_text
    assert "cancel-in-progress: true" in ci_text
    assert "ubuntu-latest" in ci_text
    assert "macos-latest" in ci_text


def test_pyproject_pep621_metadata_and_urls() -> None:
    """Verify PEP 621 metadata, keywords, classifiers, and project URLs."""
    pyproject_text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "keywords = [" in pyproject_text
    assert "Programming Language :: Python :: 3.13" in pyproject_text
    assert "Topic :: Security" in pyproject_text
    assert "Documentation = " in pyproject_text
