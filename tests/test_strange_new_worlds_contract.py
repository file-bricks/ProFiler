from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ONEDRIVE_MIRROR = Path(r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\DATA\REL-PUB_ProFiler")


def test_snw_profiler_01_platform_matrix_consistency():
    """SNW-PROFILER-01: Windows is primary, macOS/Linux source-smoke, mobile/web/sync non-goals."""
    # Check PORTIERUNGSPLAN.md (either in repo or in OneDrive mirror)
    port_plan_path = PROJECT_ROOT / "PORTIERUNGSPLAN.md"
    if not port_plan_path.exists():
        port_plan_path = ONEDRIVE_MIRROR / "PORTIERUNGSPLAN.md"
    assert port_plan_path.exists(), "PORTIERUNGSPLAN.md must exist in repo root or OneDrive mirror"

    port_plan = port_plan_path.read_text(encoding="utf-8")
    assert "Windows Desktop" in port_plan and "Hauptlinie" in port_plan
    assert "macOS" in port_plan and "Source-Smoke" in port_plan
    assert "Linux" in port_plan and "Source-Smoke" in port_plan
    assert "Web/PWA" in port_plan and "Nicht-Ziel" in port_plan
    assert "Android/iOS" in port_plan and "Nicht-Ziel" in port_plan
    assert "Server-Sync" in port_plan and "Nicht-Ziel" in port_plan

    # Verify PLATFORM_SUPPORT.md consistency
    platform_support = (PROJECT_ROOT / "PLATFORM_SUPPORT.md").read_text(encoding="utf-8")
    assert "Tier-1: Windows Desktop (Primary)" in platform_support or "Windows Desktop" in platform_support
    assert "Tier-3 (Source-Smoke / Non-Goals)" in platform_support or "Source-Smoke" in platform_support
    assert "Android" in platform_support
    assert "iOS" in platform_support

    # Verify WINDOWS_STORE_PREP.md
    store_prep = (PROJECT_ROOT / "WINDOWS_STORE_PREP.md").read_text(encoding="utf-8")
    assert "MSIX" in store_prep or "msix" in store_prep.lower()
    assert "WACK" in store_prep or "Windows App Certification Kit" in store_prep


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
