from __future__ import annotations

import ast
import json
import re
import shlex
import tomllib
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
    assert f"Source version: {app_version} (frozen" in llms_text


def test_required_documentation_and_manifests_exist() -> None:
    """Verify presence of core documentation and policy files."""
    required_files = [
        "README.md",
        "README_de.md",
        "NOTICE",
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
    """Verify current llms.txt sections, versioned source scope, and workflow link."""
    llms_text = (PROJECT_ROOT / "llms.txt").read_text(encoding="utf-8")
    assert "# ProFiler Suite" in llms_text
    assert "file-bricks/ProFiler" in llms_text
    assert "## Main workflows" in llms_text
    assert "## Search phrases" in llms_text
    assert "## Distribution boundary" in llms_text
    assert "## Current CI status" in llms_text
    assert "https://github.com/file-bricks/ProFiler/actions/workflows/source-platform-smoke.yml" in llms_text
    assert re.search(r"## Last checked\s+\d{4}-\d{2}-\d{2}", llms_text)


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


def test_security_policy_structure_and_contacts() -> None:
    """Verify the bilingual policy routes reports to the configured channels."""
    sec_text = (PROJECT_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "## English" in sec_text
    assert "## Deutsch" in sec_text
    assert "security@open-bricks.org" in sec_text
    assert "support@lukasgeiger.com" in sec_text
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
    """Verify parsed PEP 621 metadata and stable project URL targets."""
    config = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = config["project"]
    urls = project["urls"]
    assert project["requires-python"] == ">=3.11"
    assert "Programming Language :: Python :: 3.10" not in project["classifiers"]
    assert project["keywords"]
    assert "Programming Language :: Python :: 3.13" in project["classifiers"]
    assert "Topic :: Security" in project["classifiers"]
    assert urls["Documentation"] == "https://github.com/file-bricks/ProFiler#readme"
    assert urls["Parent Organization"] == "https://github.com/file-bricks"
    assert urls["Umbrella Ecosystem"] == "https://github.com/open-bricks"
    assert urls["Changelog"].endswith("/CHANGELOG.md")
    assert urls["Security"].endswith("/SECURITY.md")


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
    """Verify parsed pytest configuration enables concise verbose reporting."""
    config = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    pytest_config = config["tool"]["pytest"]["ini_options"]
    flags = shlex.split(pytest_config["addopts"])
    assert "-ra" in flags
    assert "-v" in flags
    assert pytest_config["testpaths"] == ["tests", "."]


def test_security_policy_slas_and_contacts() -> None:
    """Verify security report contact channels and current project version."""
    sec_text = (PROJECT_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "security@open-bricks.org" in sec_text
    assert "lukas@open-bricks.org" in sec_text
    assert "support@lukasgeiger.com" in sec_text
    assert "15.0.2" in sec_text


def test_ci_workflow_hardening() -> None:
    """Verify CI workflow includes Python bytecode compilation gate and verbose pytest."""
    ci_file = PROJECT_ROOT / ".github" / "workflows" / "source-platform-smoke.yml"
    assert ci_file.exists(), "CI workflow file missing"
    ci_text = ci_file.read_text(encoding="utf-8")
    assert "python -m compileall -q ." in ci_text
    assert "pytest -ra -v" in ci_text


def test_changelog_release_entry() -> None:
    """Verify CHANGELOG.md contains 15.0.1 and 15.0.2 release entries with technical hygiene notes."""
    cl_text = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [15.0.1] - 2026-09-10" in cl_text
    assert "## [15.0.2] - 2026-09-18" in cl_text
    assert "Technische Hygiene" in cl_text or "Pfad A" in cl_text
    assert "15.0.1.0" in cl_text
    assert "15.0.2.0" in cl_text


def test_readme_badges_parity() -> None:
    """Verify current version, lint, ecosystem, and CI badges in both READMEs."""
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README_de.md").read_text(encoding="utf-8")

    for doc in [readme_en, readme_de]:
        assert "version-15.0.2-blue.svg" in doc
        assert "code%20style-ruff" in doc
        assert "ecosystem-open--bricks" in doc or "%C3%96kosystem-open--bricks" in doc
        assert "CI:" in doc or "CI%3A" in doc


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


def test_third_party_licenses_markdown_audit() -> None:
    """Verify the dependency note keeps its project and dependency structure."""
    lic_md = PROJECT_ROOT / "THIRD_PARTY_LICENSES.md"
    assert lic_md.exists(), "THIRD_PARTY_LICENSES.md missing"
    content = lic_md.read_text(encoding="utf-8")

    assert "GNU Affero General Public License version 3" in content
    assert "[LICENSE](LICENSE)" in content
    assert "[NOTICE](NOTICE)" in content
    assert "## Direct runtime requirements" in content
    assert "## Optional and development requirements" in content
    assert "## External programs and packaging boundary" in content
    assert "PySide6" in content
    assert "PyMuPDF" in content
    assert "pypdf" in content
    assert "Pillow" in content
    assert "pytesseract" in content
    assert "Tesseract OCR" in content
    assert "Poppler" in content


def test_marketing_log_parity() -> None:
    """Keep the historical marketing record tied to the current project identity."""
    m_log = PROJECT_ROOT / "MARKETING-LOG.txt"
    assert m_log.exists(), "MARKETING-LOG.txt missing"
    content = m_log.read_text(encoding="utf-8")

    assert "file-bricks/ProFiler" in content
    assert "15.0.1" in content
    assert "15.0.2" in content
    assert "THIRD_PARTY_LICENSES.md" in content


def test_readme_18_points_quick_navigation_parity() -> None:
    """Verify exact 18-point quick navigation parity and dual HTML anchors between English and German READMEs."""
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README_de.md").read_text(encoding="utf-8")

    expected_anchors_en_18 = [
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
        "(#target-personas--high-intent-seo)",
        "(#verification--test-suite)",
    ]
    expected_anchors_de_18 = [
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
        "(#zielgruppen--high-intent-seo)",
        "(#verifikation--test-suite)",
    ]

    for anchor in expected_anchors_en_18:
        assert anchor in readme_en, f"Missing English 18-point navigation anchor: {anchor}"

    for anchor in expected_anchors_de_18:
        assert anchor in readme_de, f"Missing German 18-point navigation anchor: {anchor}"

    # Verify dual HTML anchor tags are present
    assert '<a id="1-architecture"></a>' in readme_en
    assert '<a id="18-verification--test-suite"></a>' in readme_en
    assert '<a id="1-architektur"></a>' in readme_de
    assert '<a id="18-verifikation--test-suite"></a>' in readme_de

    # Verify reciprocal dual HTML anchors sec-01 through sec-18
    for i in range(1, 19):
        sec_id = f"sec-{i:02d}"
        assert f'<a id="{sec_id}"></a>' in readme_en, f"Missing {sec_id} in English README"
        assert f'<a id="{sec_id}"></a>' in readme_de, f"Missing {sec_id} in German README"


def test_pyproject_pep621_extended_urls() -> None:
    """Verify project links resolve to the intended docs and notice files."""
    pyproj_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproj_path.exists(), "pyproject.toml missing"
    urls = tomllib.loads(pyproj_path.read_text(encoding="utf-8"))["project"]["urls"]
    assert urls["Third-Party Licenses"] == "https://github.com/file-bricks/ProFiler/blob/master/THIRD_PARTY_LICENSES.md"
    assert urls["Marketing Log"] == "https://github.com/file-bricks/ProFiler/blob/master/MARKETING-LOG.txt"
    assert urls["LLM Ready"] == "https://github.com/file-bricks/ProFiler/blob/master/llms.txt"
    assert urls["Notice"] == "https://github.com/file-bricks/ProFiler/blob/master/NOTICE"


def test_third_party_notes_preserve_the_frozen_project_version() -> None:
    """Keep the dependency note aligned with the repository's frozen version."""
    lic_md = PROJECT_ROOT / "THIRD_PARTY_LICENSES.md"
    assert lic_md.exists(), "THIRD_PARTY_LICENSES.md missing"
    content = lic_md.read_text(encoding="utf-8")

    assert "**Version:** `15.0.2` (frozen)" in content


def test_readme_extended_badges_parity() -> None:
    """Verify attribution and contributor links remain in both READMEs."""
    readme_en = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README_de.md").read_text(encoding="utf-8")

    for doc in [readme_en, readme_de]:
        assert "Attribution-NOTICE" in doc

    assert "Contributing" in readme_en
    assert "Mitwirken" in readme_de


def test_notice_file_exists_and_attribution() -> None:
    """Verify canonical root NOTICE attribution file."""
    notice_path = PROJECT_ROOT / "NOTICE"
    assert notice_path.is_file(), "Root NOTICE file missing"
    content = notice_path.read_text(encoding="utf-8")
    assert "ProFiler Suite" in content
    assert "Lukas Geiger" in content
    assert "file-bricks" in content
    assert "open-bricks" in content
    assert "THIRD_PARTY_LICENSES.md" in content


def test_pyproject_keywords_notice_url_and_license_files() -> None:
    """Verify useful PyPI keywords, the NOTICE target, and explicit license files."""
    pyproject_text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    kw_match = re.search(r'keywords\s*=\s*\[(.*?)\]', pyproject_text, re.DOTALL)
    assert kw_match is not None, "keywords array not found in pyproject.toml"
    keywords = [k.strip(' \t\n\r"\'') for k in kw_match.group(1).split(",") if k.strip(' \t\n\r"\'')]
    assert len(keywords) <= 20, f"PyPI permits at most 20 keywords, got {len(keywords)}"
    assert len(keywords) == len(set(keywords)), "PyPI keywords should be unique"
    assert {"desktop-app", "file-management", "local-first", "pdf", "pyside6", "sqlite"} <= set(keywords)

    assert 'Notice = "https://github.com/file-bricks/ProFiler/blob/master/NOTICE"' in pyproject_text
    assert 'license-files = ["LICENSE", "NOTICE", "THIRD_PARTY_LICENSES.md", "THIRD_PARTY_LICENSES.txt"]' in pyproject_text


def test_contributing_guide_present_and_bilingual_parity() -> None:
    """Verify practical bilingual contributor setup and accurate support boundaries."""
    contrib_path = PROJECT_ROOT / "CONTRIBUTING.md"
    assert contrib_path.is_file(), "CONTRIBUTING.md missing"
    content = contrib_path.read_text(encoding="utf-8")
    assert len(content) > 2000, "CONTRIBUTING.md unexpectedly brief"

    # Bilingual navigation and sections
    assert "[English](#english)" in content and "[Deutsch](#deutsch)" in content
    assert '<a id="english"></a>' in content
    assert '<a id="deutsch"></a>' in content
    assert "## English" in content
    assert "## Deutsch" in content

    # Both language sections provide runnable setup and test instructions.
    assert content.count('python -m pip install -e ".[dev]"') == 2
    assert content.count("python -m pytest -ra -v") == 2
    assert content.count("git diff --check") == 2
    assert content.count("[SECURITY.md](SECURITY.md)") == 2


def test_ci_lifecycle_workflows_and_labels_present() -> None:
    """Verify auto-assign.yml, label-sync.yml and canonical labels.yml per GOVERNANCE.md §4.2."""
    auto_assign_path = PROJECT_ROOT / ".github" / "workflows" / "auto-assign.yml"
    assert auto_assign_path.is_file(), "auto-assign.yml workflow missing"
    aa_text = auto_assign_path.read_text(encoding="utf-8")
    assert "cancel-in-progress: true" in aa_text
    assert "timeout-minutes: 5" in aa_text
    assert "actions/github-script@v7" in aa_text
    assert "pull-requests: write" in aa_text
    assert "issues: write" in aa_text

    label_sync_path = PROJECT_ROOT / ".github" / "workflows" / "label-sync.yml"
    assert label_sync_path.is_file(), "label-sync.yml workflow missing"
    ls_text = label_sync_path.read_text(encoding="utf-8")
    assert "cancel-in-progress: true" in ls_text
    assert "timeout-minutes: 5" in ls_text
    assert "EndBug/label-sync@v2" in ls_text
    assert "config-file: .github/labels.yml" in ls_text

    labels_path = PROJECT_ROOT / ".github" / "labels.yml"
    assert labels_path.is_file(), ".github/labels.yml missing"
    labels_text = labels_path.read_text(encoding="utf-8")

    expected_labels = [
        "bug",
        "enhancement",
        "good first issue",
        "help wanted",
        "documentation",
        "duplicate",
        "wontfix",
        "priority: high",
        "priority: low",
        "needs-triage",
        "stale",
    ]
    for label in expected_labels:
        assert f"name: {label}" in labels_text or f"name: '{label}'" in labels_text, f"Missing standard label: {label}"


def test_pyproject_pep621_contributing_and_license_urls() -> None:
    """Verify contributor and license URL targets from parsed project metadata."""
    pyproj_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproj_path.is_file(), "pyproject.toml missing"
    urls = tomllib.loads(pyproj_path.read_text(encoding="utf-8"))["project"]["urls"]
    assert urls["Contributing"] == "https://github.com/file-bricks/ProFiler/blob/master/CONTRIBUTING.md"
    assert urls["Plain-Text License"] == "https://github.com/file-bricks/ProFiler/blob/master/LICENSE"
    assert urls["Third-Party Licenses"] == "https://github.com/file-bricks/ProFiler/blob/master/THIRD_PARTY_LICENSES.md"
    assert urls["Third-Party Licenses (Text)"] == "https://github.com/file-bricks/ProFiler/blob/master/THIRD_PARTY_LICENSES.txt"


def test_gitignore_multihost_lock_defense() -> None:
    """Verify .gitignore contains multi-host, lock defense, and temporary cache patterns."""
    gi_path = PROJECT_ROOT / ".gitignore"
    assert gi_path.is_file(), ".gitignore missing"
    content = gi_path.read_text(encoding="utf-8")

    assert "*-IDEAPAD*" in content
    assert "*-IDEAPAD-GEI*" in content
    assert "Desktop.ini" in content
    assert "TASKPLAN_*.md" in content
    assert "*-TASKPLAN*" in content
    assert "LOCK.dev.*" in content
    assert "LOCK.antigravity.*" in content
    assert "LOCK.bugsearch.*" in content
    assert ".pytest_temp/" in content


def test_version_freeze_discipline_15_0_2() -> None:
    """Verify strict adherence to version freeze discipline per T-20260920-167562623."""
    version_src = (PROJECT_ROOT / "version.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "15.0.2"' in version_src, "version.py version bump detected"

    pyproject_text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "15.0.2"' in pyproject_text, "pyproject.toml version bump detected"

    store_pkg = json.loads((PROJECT_ROOT / "store_package.json").read_text(encoding="utf-8"))
    assert store_pkg["version"] == "15.0.2.0", "store_package.json version bump detected"

    manifest_text = (PROJECT_ROOT / "store_package" / "ProFiler" / "AppxManifest.xml").read_text(encoding="utf-8")
    assert 'Version="15.0.2.0"' in manifest_text, "AppxManifest.xml version bump detected"

    changelog_text = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## [Unreleased]" in changelog_text, "CHANGELOG.md missing Unreleased section"


def test_third_party_licenses_plain_text_companion_structure() -> None:
    """Keep plain-text and Markdown dependency notes aligned with declared packages."""
    txt_path = PROJECT_ROOT / "THIRD_PARTY_LICENSES.txt"
    md_path = PROJECT_ROOT / "THIRD_PARTY_LICENSES.md"
    assert txt_path.is_file(), "THIRD_PARTY_LICENSES.txt missing"
    assert md_path.is_file(), "THIRD_PARTY_LICENSES.md missing"
    text = txt_path.read_text(encoding="utf-8")
    md_text = md_path.read_text(encoding="utf-8")

    assert "Project version: 15.0.2 (frozen)" in text
    assert "**Version:** `15.0.2` (frozen)" in md_text
    assert "DIRECT RUNTIME REQUIREMENTS" in text
    assert "## Direct runtime requirements" in md_text
    packages = (
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
    )
    for package in packages:
        assert package in text and package in md_text
