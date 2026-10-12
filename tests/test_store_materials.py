from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_PUBLISHER = "CN=52596601-BAB4-4F3F-B182-E8F3F273B202"
EXPECTED_IDENTITY = "Geiger.ProFilerSuite"


def _load_script_module(module_name: str, script_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


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
    assert package["logo"] == "store_assets/StoreLogo.png"
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

    props = root.find("def:Properties", ns)
    if props is None:
        props = root.find("{http://schemas.microsoft.com/appx/manifest/foundation/windows10}Properties")
    assert props is not None
    logo = props.find("def:Logo", ns)
    if logo is None:
        logo = props.find("{http://schemas.microsoft.com/appx/manifest/foundation/windows10}Logo")
    assert logo is not None
    assert logo.text == r"icons\StoreLogo.png"


def test_store_tile_icons_dimensions_and_validity() -> None:
    required_icons = {
        "icon_44x44.png": (44, 44),
        "icon_50x50.png": (50, 50),
        "icon_150x150.png": (150, 150),
        "icon_310x150.png": (310, 150),
        "icon_310x310.png": (310, 310),
        "StoreLogo.png": (50, 50),
    }

    dirs = [
        PROJECT_ROOT / "store_package" / "ProFiler" / "icons",
        PROJECT_ROOT / "store_assets",
        PROJECT_ROOT / "releases" / "windowsstore",
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

    assert "Tesseract" in listing
    assert "THIRD_PARTY_LICENSES.md" in listing
    assert "PRIVACY_POLICY.md" in listing
    assert "SUPPORT.md" in listing
    assert "https://github.com/file-bricks/ProFiler/issues" in support
    assert "build_exe.bat" in prep
    assert "AppxManifest.xml" in prep
    assert "wack_preflight_20261001.xml" in prep


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


def test_windowsstore_release_staging_complete() -> None:
    rel_store = PROJECT_ROOT / "releases" / "windowsstore"
    assert rel_store.exists()

    required_files = [
        "BUILD.md",
        "WACK_PROTOCOL.md",
        "store_settings.json",
        "store_listing_de.md",
        "store_listing_en.md",
        "StoreLogo.png",
    ]
    for rf in required_files:
        p = rel_store / rf
        assert p.exists() and p.stat().st_size > 0

    shots_dir = rel_store / "screenshots"
    assert shots_dir.exists()
    assert len(list(shots_dir.glob("*.png"))) >= 4

    test_reports = rel_store / "test_reports"
    assert test_reports.exists()
    assert list(test_reports.glob("wack_preflight_*.xml"))
    assert list(test_reports.glob("wack_preflight_*.json"))
    history_note = test_reports / "wack_preflight_20261001.NOT-WACK.md"
    assert history_note.exists()
    assert "synthetic" in history_note.read_text(encoding="utf-8").casefold()


def test_preflight_is_not_a_wack_report_and_does_not_claim_pass(capsys) -> None:
    wack_script = PROJECT_ROOT / "scripts" / "run_windows_wack.py"
    assert wack_script.exists()

    module = _load_script_module("wack_runner_test", wack_script)
    with tempfile.TemporaryDirectory(prefix="profiler-preflight-") as temp_dir:
        report_dir = Path(temp_dir)
        preflight_path = module.generate_preflight_status(PROJECT_ROOT, report_dir)
        payload = json.loads(preflight_path.read_text(encoding="utf-8"))

        assert preflight_path.name.startswith("store_preflight_")
        assert preflight_path.suffix == ".json"
        assert not list(report_dir.glob("*.xml"))
        assert payload["schema"] == "profiler.windows-store-preflight.v1"
        assert payload["report_type"] == "static_preflight"
        assert payload["status"] == "NOT_RUN"
        assert payload["wack_executed"] is False
        assert "overall_result" not in payload
        assert "requirements" not in payload

        exit_code = module.main(
            ["--project-root", str(PROJECT_ROOT), "--report-dir", str(report_dir), "--preflight"]
        )
        assert exit_code == 0
        output = capsys.readouterr().out
        assert "NOT_RUN" in output
        assert "kein Zertifizierungsbericht" in output


def test_wack_parser_separates_historical_preflight_from_report_xml(tmp_path: Path, capsys) -> None:
    wack_script = PROJECT_ROOT / "scripts" / "run_windows_wack.py"
    module = _load_script_module("wack_parser_test", wack_script)

    historical_xml = PROJECT_ROOT / "releases" / "windowsstore" / "test_reports" / "wack_preflight_20261001.xml"
    with pytest.raises(ValueError, match="Herkunft ist damit nicht verifiziert"):
        module.parse_wack_report(historical_xml)
    copied_historical_xml = tmp_path / "wack_preflight_legacy.xml"
    copied_historical_xml.write_text(historical_xml.read_text(encoding="utf-8"), encoding="utf-8")
    assert module.main(["--parse-report", str(copied_historical_xml)]) == 2
    assert not copied_historical_xml.with_suffix(".json").exists()
    assert "nicht verifiziert" in capsys.readouterr().err

    renamed_synthetic = tmp_path / "renamed.xml"
    renamed_synthetic.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!-- SYNTHETIC NOT WACK: test fixture only -->\n'
        '<REPORT OVERALL_RESULT="PASS"><REQUIREMENT RESULT="PASS" /></REPORT>\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="synthetisch und nicht als WACK markiert"):
        module.parse_wack_report(renamed_synthetic)

    representative_report = tmp_path / "representative-appcert-report.xml"
    representative_report.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<REPORT OVERALL_RESULT="WARNING">'
        '<REQUIREMENT Id="1" RESULT="PASS" />'
        '<REQUIREMENT Id="2" RESULT="WARNING" />'
        '</REPORT>\n',
        encoding="utf-8",
    )
    summary = module.parse_wack_report(representative_report)
    assert summary.overall_result == "WARNING"
    assert summary.requirement_count == 2
    assert summary.pass_count == 1
    assert summary.warning_count == 1
    actual_run_path = module.resolve_report_path(PROJECT_ROOT, tmp_path, None)
    assert actual_run_path.name.startswith("wack_report_")
    next_run_path = module.resolve_report_path(PROJECT_ROOT, tmp_path, None)
    assert next_run_path != actual_run_path
    summary_path = tmp_path / "parsed-summary.json"
    module.write_summary(
        summary,
        summary_path,
        appcert_invoked_by_this_run=False,
    )
    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary_payload["report_type"] == "wack_xml_summary"
    assert summary_payload["appcert_invoked_by_this_run"] is False


def _prepare_fake_wack_run(tmp_path: Path, report_path: Path) -> tuple[Path, Path, list[str]]:
    project_root = tmp_path / "project"
    project_root.mkdir()
    msix_path = tmp_path / "fixture.msix"
    msix_path.write_bytes(b"test package")
    appcert_path = tmp_path / "appcert.exe"
    appcert_path.write_bytes(b"fake executable placeholder")
    args = [
        "--project-root",
        str(project_root),
        "--msix",
        str(msix_path),
        "--appcert",
        str(appcert_path),
        "--report-path",
        str(report_path),
        "--allow-non-admin",
    ]
    return project_root, appcert_path, args


def _install_fake_appcert(
    module,
    monkeypatch,
    *,
    test_exit: int = 0,
    reset_exit: int = 0,
    finalize_exit: int = 0,
    create_report: bool = True,
) -> list[str]:
    calls: list[str] = []
    pass_report = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<REPORT OVERALL_RESULT="PASS"><REQUIREMENT Id="fixture" RESULT="PASS" /></REPORT>\n'
    )

    def fake_subprocess_run(command, **kwargs):
        operation = command[1]
        calls.append(operation)
        if operation == "reset":
            exit_code = reset_exit
        elif operation == "test":
            exit_code = test_exit
            if create_report:
                report_path = Path(command[command.index("-reportoutputpath") + 1])
                report_path.write_text(pass_report, encoding="utf-8")
        elif operation == "finalizereport":
            exit_code = finalize_exit
        else:
            raise AssertionError(f"Unexpected appcert command: {operation}")
        return module.subprocess.CompletedProcess(command, exit_code, stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_subprocess_run)
    return calls


def test_wack_run_refuses_existing_pass_report_without_overwriting(tmp_path: Path, monkeypatch, capsys) -> None:
    module = _load_script_module(
        "wack_existing_report_test",
        PROJECT_ROOT / "scripts" / "run_windows_wack.py",
    )
    report_path = tmp_path / "existing-pass.xml"
    original = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<REPORT OVERALL_RESULT="PASS"><REQUIREMENT RESULT="PASS" /></REPORT>\n'
    ).encode("utf-8")
    report_path.write_bytes(original)
    _, _, args = _prepare_fake_wack_run(tmp_path, report_path)
    calls = _install_fake_appcert(module, monkeypatch, test_exit=1)

    assert module.main(args) == 2
    assert calls == []
    assert report_path.read_bytes() == original
    assert not report_path.with_suffix(".log").exists()
    assert "Ausgabe existiert bereits" in capsys.readouterr().err


def test_wack_test_failure_cannot_be_masked_by_pass_report(tmp_path: Path, monkeypatch, capsys) -> None:
    module = _load_script_module(
        "wack_failed_test_report_test",
        PROJECT_ROOT / "scripts" / "run_windows_wack.py",
    )
    report_path = tmp_path / "failed-run.xml"
    _, _, args = _prepare_fake_wack_run(tmp_path, report_path)
    args.append("--skip-reset")
    calls = _install_fake_appcert(module, monkeypatch, test_exit=1, create_report=True)

    assert module.main(args) == 1
    assert calls == ["test"]
    assert report_path.exists()
    assert not report_path.with_suffix(".json").exists()
    assert "appcert test ist mit Exitcode 1 fehlgeschlagen" in capsys.readouterr().err


def test_wack_success_without_new_report_is_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    module = _load_script_module(
        "wack_missing_report_test",
        PROJECT_ROOT / "scripts" / "run_windows_wack.py",
    )
    report_path = tmp_path / "missing-report.xml"
    _, _, args = _prepare_fake_wack_run(tmp_path, report_path)
    args.append("--skip-reset")
    calls = _install_fake_appcert(module, monkeypatch, create_report=False)

    assert module.main(args) == 1
    assert calls == ["test"]
    assert not report_path.exists()
    assert not report_path.with_suffix(".json").exists()
    assert "keinen neuen, nichtleeren XML-Report" in capsys.readouterr().err


def test_wack_reset_failure_stops_before_test_and_preserves_exit_code(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    module = _load_script_module(
        "wack_reset_failure_test",
        PROJECT_ROOT / "scripts" / "run_windows_wack.py",
    )
    report_path = tmp_path / "reset-failure.xml"
    _, _, args = _prepare_fake_wack_run(tmp_path, report_path)
    calls = _install_fake_appcert(module, monkeypatch, reset_exit=740)

    assert module.main(args) == 740
    assert calls == ["reset"]
    assert not report_path.exists()
    assert "appcert reset ist mit Exitcode 740 fehlgeschlagen" in capsys.readouterr().err


def test_wack_finalize_failure_cannot_produce_summary(tmp_path: Path, monkeypatch, capsys) -> None:
    module = _load_script_module(
        "wack_finalize_failure_test",
        PROJECT_ROOT / "scripts" / "run_windows_wack.py",
    )
    report_path = tmp_path / "finalize-failure.xml"
    _, _, args = _prepare_fake_wack_run(tmp_path, report_path)
    args.append("--skip-reset")
    calls = _install_fake_appcert(module, monkeypatch, finalize_exit=9)

    assert module.main(args) == 9
    assert calls == ["test", "finalizereport"]
    assert report_path.exists()
    assert not report_path.with_suffix(".json").exists()
    assert "appcert finalizereport ist mit Exitcode 9 fehlgeschlagen" in capsys.readouterr().err


def test_wack_new_report_with_successful_commands_is_summarized(tmp_path: Path, monkeypatch, capsys) -> None:
    module = _load_script_module(
        "wack_successful_new_report_test",
        PROJECT_ROOT / "scripts" / "run_windows_wack.py",
    )
    report_path = tmp_path / "successful-run.xml"
    _, _, args = _prepare_fake_wack_run(tmp_path, report_path)
    args.append("--skip-reset")
    calls = _install_fake_appcert(module, monkeypatch)

    assert module.main(args) == 0
    assert calls == ["test", "finalizereport"]
    summary_payload = json.loads(report_path.with_suffix(".json").read_text(encoding="utf-8"))
    assert summary_payload["overall_result"] == "PASS"
    assert summary_payload["appcert_invoked_by_this_run"] is True
    assert summary_payload["exit_code"] == 0
    assert "WACK-Ergebnis: PASS" in capsys.readouterr().out


def test_store_staging_consistency_is_not_a_readiness_or_wack_claim(capsys) -> None:
    checker = _load_script_module(
        "store_staging_check_test",
        PROJECT_ROOT / "scripts" / "check_store_readiness.py",
    )
    assert checker.evaluate_staging_consistency() == []
    assert checker.main() == 0
    output = capsys.readouterr().out
    assert "Staging Consistency Check" in output
    assert "STAGING CONSISTENCY CHECK PASSED" in output
    assert "keinen Build" in output
    assert "keinen WACK-Lauf" in output
    assert "Readiness Audit" not in output
    assert "AUDIT PASSED" not in output
    assert "[PASS]" not in output


def test_staging_check_error_output_does_not_print_success_labels(capsys, monkeypatch) -> None:
    checker = _load_script_module(
        "store_staging_check_failure_test",
        PROJECT_ROOT / "scripts" / "check_store_readiness.py",
    )
    monkeypatch.setattr(
        checker,
        "check_store_package_json",
        lambda results: results["errors"].append("missing package metadata"),
    )
    monkeypatch.setattr(checker, "check_appx_manifest", lambda results: None)
    monkeypatch.setattr(checker, "check_tile_icons", lambda results: None)
    monkeypatch.setattr(checker, "check_store_listing_and_docs", lambda results: None)
    monkeypatch.setattr(checker, "check_store_screenshots", lambda results: None)
    monkeypatch.setattr(checker, "check_windowsstore_release_staging", lambda results: None)

    assert checker.main() == 1
    output = capsys.readouterr().out
    assert "STAGING CONSISTENCY CHECK FAILED" in output
    assert "[CHECK OK]" not in output


def test_staging_file_check_does_not_require_a_fake_preflight_report(tmp_path: Path) -> None:
    checker = _load_script_module(
        "store_staging_check_minimal_test",
        PROJECT_ROOT / "scripts" / "check_store_readiness.py",
    )
    checker.PROJECT_ROOT = tmp_path
    rel_store = tmp_path / "releases" / "windowsstore"
    rel_store.mkdir(parents=True)
    for name in (
        "BUILD.md",
        "WACK_PROTOCOL.md",
        "store_settings.json",
        "store_listing_de.md",
        "store_listing_en.md",
        "StoreLogo.png",
    ):
        (rel_store / name).write_text("staging fixture\n", encoding="utf-8")
    screenshots_dir = rel_store / "screenshots"
    screenshots_dir.mkdir()
    for index in range(4):
        (screenshots_dir / f"shot-{index}.png").write_bytes(b"")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "run_windows_wack.py").write_text("# tool presence only\n", encoding="utf-8")

    assert not (rel_store / "test_reports").exists()
    results = {"ok": [], "errors": []}
    checker.check_windowsstore_release_staging(results)
    assert results["errors"] == []
    assert "keine Build-, Signatur-, WACK- oder Store-Prüfung" in results["ok"][0]
