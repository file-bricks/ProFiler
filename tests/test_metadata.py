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
        "THIRD_PARTY_LICENSES.md",
        "MARKETING-LOG.txt",
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
    assert '"Parent Organization" = ' in pyproject_text
    assert '"Umbrella Ecosystem" = ' in pyproject_text
    assert "Changelog = " in pyproject_text
    assert "Security = " in pyproject_text


def test_gitignore_hygiene_patterns() -> None:
    """Verify comprehensive gitignore hygiene: sync conflicts, locks, caches, and temps."""
    gi_text = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    # Multi-host sync conflicts
    for pat in ["*-WORKSTATION-LG*", "*-ASUS-GEI*", "*-conflict-*", "*-CONFLIT-*", "*.conflict", "*.sync-conflict-*", "*.sync-temp-*"]:
        assert pat in gi_text, f"Missing sync conflict pattern in .gitignore: {pat}"
    # Multi-agent locks
    for pat in ["LOCK", "LOCK.*", "*.lock", "LOCK*.txt", "LOCK.permissions.json"]:
        assert pat in gi_text, f"Missing lock pattern in .gitignore: {pat}"
    # Test, coverage and wheelhouse caches
    for pat in [".pytest_cache/", ".ruff_cache/", ".coverage", "coverage/", "htmlcov/", "wheelhouse/", ".wheel-smoke/"]:
        assert pat in gi_text, f"Missing cache pattern in .gitignore: {pat}"
    # Temp and editor files
    for pat in ["*.tmp", "*.bak", "*.swp"]:
        assert pat in gi_text, f"Missing temp pattern in .gitignore: {pat}"


def test_pytest_configuration_and_flags() -> None:
    """Verify pytest ini_options configuration has standard flags -ra -v."""
    pyproject_text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.pytest.ini_options]" in pyproject_text
    assert 'addopts = "-ra -v"' in pyproject_text
    assert 'testpaths = ["tests", "."]' in pyproject_text


def test_security_policy_slas_and_contacts() -> None:
    """Verify bilingual SECURITY.md provides 48h response SLA, 5d triage, and official contacts."""
    sec_text = (PROJECT_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "48 hours" in sec_text and "48 Stunden" in sec_text
    assert "5 business days" in sec_text and "5 Werktagen" in sec_text
    assert "security@open-bricks.org" in sec_text
    assert "lukas@open-bricks.org" in sec_text
    assert "support@lukasgeiger.com" in sec_text
    assert "15.0.x" in sec_text


def test_ci_workflow_hardening() -> None:
    """Verify CI workflow includes Python bytecode compilation gate and verbose pytest."""
    ci_file = PROJECT_ROOT / ".github" / "workflows" / "source-platform-smoke.yml"
    assert ci_file.exists(), "CI workflow file missing"
    ci_text = ci_file.read_text(encoding="utf-8")
    assert "python -m compileall -q ." in ci_text
    assert "pytest -ra -v" in ci_text


def test_changelog_release_entry() -> None:
    """Verify CHANGELOG.md contains 15.0.1 release entry with technical hygiene notes."""
    cl_text = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [15.0.1] - 2026-09-10" in cl_text
    assert "Technische Hygiene" in cl_text or "Pfad A" in cl_text
    assert "15.0.1.0" in cl_text


def test_readme_badges_parity() -> None:
    """Verify README.md and README_de.md badges parity for version, SLA, Ruff, and tests."""
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README_de.md").read_text(encoding="utf-8")

    for doc in [readme_en, readme_de]:
        assert "version-15.0.1-blue.svg" in doc
        assert "48h%20Response%20%2F%205d%20Triage" in doc or "48h%20Antwort%20%2F%205d%20Triage" in doc
        assert "code%20style-ruff" in doc
        assert "ecosystem-open--bricks" in doc or "%C3%96kosystem-open--bricks" in doc


def test_readme_16_points_quick_navigation_parity() -> None:
    """Verify exact 16-point quick navigation parity between English and German READMEs."""
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README_de.md").read_text(encoding="utf-8")

    expected_anchors_en = [
        "(#architecture)",
        "(#workflow-lifecycle)",
        "(#core-capabilities--security-invariants)",
        "(#target-personas--use-cases)",
        "(#comparative-matrix--alternatives)",
        "(#feature-highlights)",
        "(#visual-interface--screenshot)",
        "(#when-to-use-profiler)",
        "(#quick-start--setup)",
        "(#windows-launcher--build-flow)",
        "(#configuration--local-storage)",
        "(#included-tools--utilities)",
        "(#supported-file-formats--ocr)",
        "(#sibling-ecosystem--integrations)",
        "(#third-party-licenses--compliance)",
        "(#security-policy--slas)",
    ]
    expected_anchors_de = [
        "(#architektur)",
        "(#workflow-lebenszyklus)",
        "(#kernfähigkeiten--sicherheitsinvarianten)",
        "(#zielgruppen--anwendungsfälle)",
        "(#vergleichsmatrix--alternativen)",
        "(#funktions-highlights)",
        "(#visuelle-oberfläche--screenshot)",
        "(#wann-profiler-passt)",
        "(#schnellstart--installation)",
        "(#windows-launcher--build-prozess)",
        "(#konfiguration--lokale-ablage)",
        "(#enthaltene-werkzeuge--dienstprogramme)",
        "(#unterstützte-dateiformate--ocr)",
        "(#geschwister-ökosystem--integrationen)",
        "(#drittanbieter-lizenzen--compliance)",
        "(#sicherheitsrichtlinie--slas)",
    ]

    for anchor in expected_anchors_en:
        assert anchor in readme_en, f"Missing English navigation anchor: {anchor}"

    for anchor in expected_anchors_de:
        assert anchor in readme_de, f"Missing German navigation anchor: {anchor}"


def test_governance_invariants_table_parity() -> None:
    """Verify all 10 governance invariants (INV-LOCAL-01 to INV-SLA-10) are present in both READMEs."""
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README_de.md").read_text(encoding="utf-8")

    invariant_codes = [
        "INV-LOCAL-01",
        "INV-SESSION-02",
        "INV-GATE-03",
        "INV-SCHEMA-04",
        "INV-PLACEHOLDER-05",
        "INV-UNPRIV-06",
        "INV-ATOMIC-07",
        "INV-INTEGRITY-08",
        "INV-OFFLINE-09",
        "INV-SLA-10",
    ]

    for code in invariant_codes:
        assert code in readme_en, f"Missing {code} in English README"
        assert code in readme_de, f"Missing {code} in German README"


def test_target_personas_and_use_cases_parity() -> None:
    """Verify presence of all 4 target personas in English and German READMEs."""
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README_de.md").read_text(encoding="utf-8")

    assert "Legal, Compliance & Privacy Officers" in readme_en
    assert "Academic Researchers & Archival Curators" in readme_en
    assert "Small Business Owners & Freelancers" in readme_en
    assert "Power Users & Data Sovereignty Advocates" in readme_en

    assert "Datenschutzbeauftragte, Juristen & Compliance" in readme_de
    assert "Wissenschaftler, Archive & Historiker" in readme_de
    assert "Freiberufler & Kleinunternehmen" in readme_de
    assert "Power-User & Datenschutz-Enthusiasten" in readme_de


def test_comparative_matrix_parity() -> None:
    """Verify presence of comprehensive comparative matrix against cloud and local alternatives."""
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README_de.md").read_text(encoding="utf-8")

    for doc in [readme_en, readme_de]:
        assert "KnowledgeDigest" in doc
        assert "DocuWare" in doc or "Dropbox" in doc
        assert "Alfresco" in doc or "Nextcloud" in doc
        assert "Windows Explorer" in doc


def test_third_party_licenses_markdown_audit() -> None:
    """Verify THIRD_PARTY_LICENSES.md contains SPDX identifiers, packages, and copyleft analysis."""
    lic_md = PROJECT_ROOT / "THIRD_PARTY_LICENSES.md"
    assert lic_md.exists(), "THIRD_PARTY_LICENSES.md missing"
    content = lic_md.read_text(encoding="utf-8")

    assert "AGPL-3.0-only" in content
    assert "open-bricks" in content
    assert "PySide6" in content
    assert "PyMuPDF" in content
    assert "pypdf" in content
    assert "Pillow" in content
    assert "pytesseract" in content
    assert "Tesseract OCR" in content
    assert "Poppler" in content


def test_marketing_log_parity() -> None:
    """Verify local MARKETING-LOG.txt registers Pfad B run, personas, invariants, and queries."""
    m_log = PROJECT_ROOT / "MARKETING-LOG.txt"
    assert m_log.exists(), "MARKETING-LOG.txt missing"
    content = m_log.read_text(encoding="utf-8")

    assert "file-bricks/ProFiler" in content
    assert "15.0.1" in content
    assert "2026-09-12" in content
    assert "INV-LOCAL-01" in content
    assert "INV-SLA-10" in content
    assert "Datenschutzampel" in content

