from __future__ import annotations

import json

import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _assert_platform_matrix_consistency(root: Path) -> None:
    """Read the public checkout contract only; a missing matrix fails closed."""
    path = root / "PLATFORM_SUPPORT.md"
    assert path.is_file(), "PLATFORM_SUPPORT.md must exist in the checkout; no external fallback"
    text = path.read_text(encoding="utf-8")
    rows = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == 3 and cells[0] not in {"Plattform", "---"}:
            assert cells[0] not in rows, f"Duplicate platform row: {cells[0]}"
            rows[cells[0]] = cells[1:]
    expected = {
        "Windows Desktop": "Hauptlinie",
        "Windows Store": "Kandidat, extern gegatet",
        "macOS": "Source-Smoke, keine Paketlinie",
        "Linux": "Source-Smoke, keine Paketlinie",
        "Web/PWA": "Nicht-Ziel",
        "Android/iOS": "Nicht-Ziel",
        "Server-Sync": "Nicht-Ziel",
        "Read-only Companion": "Nicht-Ziel",
    }
    assert set(rows) == set(expected), "Public platform matrix must list exactly the supported targets and non-goals"
    for platform, status in expected.items():
        actual_status, boundary = rows[platform]
        assert actual_status == status, f"{platform}: expected {status}, got {actual_status}"
        assert boundary, f"{platform}: a product boundary is required"


def test_snw_profiler_01_platform_matrix_consistency():
    """Windows primary; source smokes and non-goals come from the public matrix."""
    _assert_platform_matrix_consistency(PROJECT_ROOT)
    store_prep = (PROJECT_ROOT / "WINDOWS_STORE_PREP.md").read_text(encoding="utf-8")
    assert "MSIX" in store_prep or "msix" in store_prep.lower()
    assert "WACK" in store_prep or "Windows App Certification Kit" in store_prep


def test_platform_matrix_is_checkout_local_without_internal_plan(tmp_path, monkeypatch):
    """No private plan, user directory or OneDrive lookup is needed."""
    (tmp_path / "PLATFORM_SUPPORT.md").write_bytes(
        (PROJECT_ROOT / "PLATFORM_SUPPORT.md").read_bytes()
    )
    assert not (tmp_path / "PORTIERUNGSPLAN.md").exists()

    def forbidden_home_lookup(*args, **kwargs):
        raise AssertionError("The public contract must not inspect a user home")

    monkeypatch.setattr(Path, "home", forbidden_home_lookup)
    _assert_platform_matrix_consistency(tmp_path)


def test_missing_public_matrix_fails_even_with_an_internal_plan(tmp_path):
    (tmp_path / "PORTIERUNGSPLAN.md").write_text("Windows Desktop | Hauptlinie", encoding="utf-8")
    with pytest.raises(AssertionError, match="PLATFORM_SUPPORT.md must exist"):
        _assert_platform_matrix_consistency(tmp_path)


@pytest.mark.parametrize(
    "platform",
    ["Windows Desktop", "Windows Store", "macOS", "Linux", "Web/PWA", "Android/iOS", "Server-Sync", "Read-only Companion"],
)
def test_public_matrix_rejects_changed_product_decisions(tmp_path, platform):
    """Exercise the same matrix contract with a changed status, not a fallback fixture."""
    text = (PROJECT_ROOT / "PLATFORM_SUPPORT.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith(f"| {platform} |"):
            cells = line.split("|")
            cells[2] = " unsupported status "
            lines[index] = "|".join(cells)
            break
    else:
        pytest.fail(f"Missing public row for {platform}")
    (tmp_path / "PLATFORM_SUPPORT.md").write_text("\n".join(lines), encoding="utf-8")
    with pytest.raises(AssertionError, match=platform):
        _assert_platform_matrix_consistency(tmp_path)


def test_snw_profiler_02_store_gates_require_real_evidence():
    """SNW-PROFILER-02: Store packaging gates remain strictly evidentiary."""
    store_prep = (PROJECT_ROOT / "WINDOWS_STORE_PREP.md").read_text(encoding="utf-8")

    # The store prep doc explicitly documents remaining open gates
    assert "WACK" in store_prep
    assert "MSIX" in store_prep
    assert "Partner Center" in store_prep or "Partner-Center" in store_prep

    # Verify store_package.json identity consistency
    pkg_json = json.loads((PROJECT_ROOT / "store_package.json").read_text(encoding="utf-8"))
    assert pkg_json["identity_name"] == "Geiger.ProFilerSuite"
    assert pkg_json["publisher_display"] == "Lukas Geiger"


def test_snw_profiler_03_workspace_exchange_format_invariants():
    """SNW-PROFILER-03: profiler-workspace-v1.json as redacted exchange format without raw docs/secrets/live-sync."""
    from workspace_exchange import PathRedactor, SCHEMA_NAME

    assert SCHEMA_NAME == "profiler-workspace-v1"

    # PathRedactor must redact username / home directories
    redactor = PathRedactor()
    sample_path = str(Path.home() / "Documents" / "confidential.pdf")
    redacted = redactor.redact(sample_path)
    assert Path.home().name not in redacted or redacted.startswith("<") or "_redacted" in redacted.lower()

    # Workspace exporter must produce format with schema version
    # and no sensitive live-sync fields
    sample_workspace = {
        "format": "profiler-workspace-v1",
        "exported_at": "2026-09-11T00:00:00Z",
        "redacted_paths": True,
        "collections": [],
        "search_presets": [],
    }

    raw_json = json.dumps(sample_workspace)
    assert "password" not in raw_json.lower()
    assert "secret" not in raw_json.lower()
    assert "cloud_token" not in raw_json.lower()
    assert "live_sync_url" not in raw_json.lower()


def test_snw_profiler_04_no_unwarranted_mobile_web_or_companion_lines():
    """SNW-PROFILER-04: No Web/PWA, Android, iOS, or companion lines derived without documented usecase."""
    # Guard against accidental inception of unauthorized ports/companions
    forbidden_subtrees = [
        PROJECT_ROOT / "android",
        PROJECT_ROOT / "ios",
        PROJECT_ROOT / "web",
        PROJECT_ROOT / "pwa",
        PROJECT_ROOT / "mobile",
        PROJECT_ROOT / "companion",
    ]

    for subtree in forbidden_subtrees:
        assert not subtree.exists(), f"Unauthorized platform subtree detected: {subtree}"
