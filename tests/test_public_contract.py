from __future__ import annotations

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_runtime_and_store_use_one_version_contract() -> None:
    version_src = (PROJECT_ROOT / "version.py").read_text(encoding="utf-8")
    match = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', version_src)
    assert match is not None
    version = match.group(1)
    main_src = (PROJECT_ROOT / "Profiler_Suite_V15.py").read_text(encoding="utf-8")
    workspace_src = (PROJECT_ROOT / "workspace_exchange.py").read_text(encoding="utf-8")
    package = json.loads((PROJECT_ROOT / "store_package.json").read_text(encoding="utf-8"))

    assert version == "15.0.0"
    assert "from version import APP_VERSION" in main_src
    assert "from version import APP_VERSION" in workspace_src
    assert "ProFiler Suite V14.3" not in main_src
    assert "ProFiler Suite V13.3" not in main_src
    assert "ProFiler Suite V9" not in main_src
    assert package["version"] == f"{version}.0"


def test_public_docs_require_python_310_and_valid_master_links() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (PROJECT_ROOT / "README_de.md").read_text(encoding="utf-8")
    listing = (PROJECT_ROOT / "STORE_LISTING.md").read_text(encoding="utf-8")
    package = json.loads((PROJECT_ROOT / "store_package.json").read_text(encoding="utf-8"))

    assert "Python 3.8+" not in readme
    assert "Python 3.8+" not in readme_de
    assert "Python 3.10+" in readme
    assert "Python 3.10+" in readme_de
    assert "/blob/main/" not in listing
    assert "/blob/master/PRIVACY_POLICY.md" in listing
    assert "/blob/master/SUPPORT.md" in listing
    assert "/blob/main/" not in package["privacy_url"]
    assert "/blob/main/" not in package["support_url"]


def test_runtime_config_files_are_examples_not_tracked_live_names() -> None:
    for name in ("profiler_config", "profiler_settings", "search_config"):
        assert not (PROJECT_ROOT / f"{name}.json").exists()
        assert (PROJECT_ROOT / f"{name}.example.json").exists()

    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "profiler_config.json" in gitignore
    assert "profiler_settings.json" in gitignore
    assert "search_config.json" in gitignore


def test_build_contract_is_repo_local_and_output_stays_outside_checkout() -> None:
    build = (PROJECT_ROOT / "build_exe.bat").read_text(encoding="utf-8")
    assert "%PROJECT_ROOT%\\scripts\\build_exclude_scanner.py" in build
    assert "..\\..\\_tools" not in build
    assert "copy /Y" not in build
    assert "git status --porcelain" in build
    assert "BUILD-PROVENANCE.json" in build
    assert "requirements-build.txt" in build


def test_public_tree_has_one_canonical_application_source() -> None:
    assert (PROJECT_ROOT / "Profiler_Suite_V15.py").exists()
    forbidden = [*PROJECT_ROOT.glob("Profiler_Suite_V1[0-4]*.py"), PROJECT_ROOT / "Profiler.txt"]
    assert not [path for path in forbidden if path.exists()]


def test_contributing_points_to_real_repo_and_entrypoint() -> None:
    contributing = (PROJECT_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "file-bricks/ProFiler" in contributing
    assert "python Profiler_Suite_V15.py" in contributing
    assert "github.com/yourusername/profiler-suite" not in contributing
    assert "python main.py" not in contributing
