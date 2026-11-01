"""Hermetic contract and regression tests for workspace_exchange.py CLI and headless utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import workspace_exchange
from workspace_exchange import (
    HeadlessConfigAdapter,
    PathRedactor,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    WorkspaceFormatError,
    export_workspace,
    load_workspace,
    main,
    summarize_workspace,
)


class MockConfig:
    """Mock config manager for testing workspace export/import."""

    def __init__(self, dbs=None, settings=None, connections=None):
        self.dbs = list(dbs or [])
        self.data = dict(settings or {
            "ui_language": "de",
            "theme": "dark",
            "delete_mode": "soft",
            "trash_retention_days": 30,
            "auto_cleanup_enabled": True,
            "ocr_enabled": True,
            "ocr_language": "deu",
        })
        self.connections = list(connections or [])

    def list_connections(self):
        return list(self.connections)

    def set(self, key, value):
        self.data[key] = value


@pytest.fixture
def sample_workspace_file(tmp_path):
    """Fixture providing a valid exported workspace snapshot file."""
    cfg = MockConfig()
    target = tmp_path / "sample_workspace.json"
    export_workspace(target, cfg, cfg, cfg)
    return target


def test_cli_help(capsys):
    exit_code = main(["--help"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "--validate" in captured.out
    assert "--info" in captured.out
    assert "--export" in captured.out
    assert "--import" in captured.out
    assert "--dry-run" in captured.out
    assert "--json" in captured.out


def test_cli_no_args(capsys):
    exit_code = main([])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "usage:" in captured.out or "usage:" in captured.err


def test_cli_validate_success(sample_workspace_file, capsys):
    exit_code = main(["--validate", str(sample_workspace_file)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "[OK]" in captured.out
    assert SCHEMA_NAME in captured.out


def test_cli_validate_json_success(sample_workspace_file, capsys):
    exit_code = main(["--validate", str(sample_workspace_file), "--json"])
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["valid"] is True
    assert data["schema"] == SCHEMA_NAME
    assert data["schema_version"] == SCHEMA_VERSION


def test_cli_validate_missing_file(tmp_path, capsys):
    nonexistent = tmp_path / "missing.json"
    exit_code = main(["--validate", str(nonexistent)])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "[FEHLER]" in captured.err


def test_cli_validate_missing_file_json(tmp_path, capsys):
    nonexistent = tmp_path / "missing.json"
    exit_code = main(["--validate", str(nonexistent), "--json"])
    assert exit_code == 2
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["valid"] is False
    assert data["error_type"] == "FileNotFoundError"


def test_cli_validate_corrupted_json(tmp_path, capsys):
    corrupted = tmp_path / "corrupted.json"
    corrupted.write_text("{not valid json", encoding="utf-8")
    exit_code = main(["--validate", str(corrupted)])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "[FEHLER]" in captured.err


def test_cli_validate_schema_mismatch(tmp_path, capsys):
    invalid = tmp_path / "invalid_schema.json"
    invalid.write_text(json.dumps({"schema": "invalid-schema", "schema_version": 1}), encoding="utf-8")
    exit_code = main(["--validate", str(invalid)])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "[FEHLER]" in captured.err


def test_cli_validate_sensitive_key_rejection(sample_workspace_file, tmp_path, capsys):
    payload = json.loads(sample_workspace_file.read_text(encoding="utf-8"))
    payload["settings"]["api_key"] = "leaked_secret_token"
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(payload), encoding="utf-8")

    exit_code = main(["--validate", str(tampered)])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "[FEHLER]" in captured.err


def test_cli_validate_absolute_path_rejection(sample_workspace_file, tmp_path, capsys):
    payload = json.loads(sample_workspace_file.read_text(encoding="utf-8"))
    payload["workspace"]["notes"] = "C:\\Users\\admin\\secret.txt"
    tampered = tmp_path / "tampered_path.json"
    tampered.write_text(json.dumps(payload), encoding="utf-8")

    exit_code = main(["--validate", str(tampered)])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "[FEHLER]" in captured.err


def test_cli_info_human_output(sample_workspace_file, capsys):
    exit_code = main(["--info", str(sample_workspace_file)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "ProFiler Workspace-Snapshot" in captured.out
    assert "Schema:" in captured.out
    assert SCHEMA_NAME in captured.out
    assert "Exportiert am:" in captured.out


def test_cli_info_json_output(sample_workspace_file, capsys):
    exit_code = main(["--info", str(sample_workspace_file), "--json"])
    assert exit_code == 0
    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    assert summary["schema"] == SCHEMA_NAME
    assert summary["schema_version"] == SCHEMA_VERSION
    assert summary["workspace_name"] == "ProFiler Workspace"
    assert "settings" in summary
    assert "indexes_count" in summary


def test_cli_export_headless(tmp_path, capsys):
    target = tmp_path / "exported_workspace.json"
    exit_code = main(["--export", str(target)])
    assert exit_code == 0
    assert target.exists()
    assert target.stat().st_size > 0

    # Validate output file
    loaded = load_workspace(target)
    assert loaded["schema"] == SCHEMA_NAME
    captured = capsys.readouterr()
    assert "[OK]" in captured.out


def test_cli_export_json_output(tmp_path, capsys):
    target = tmp_path / "exported_workspace.json"
    exit_code = main(["--export", str(target), "--json"])
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["success"] is True
    assert data["file_size"] > 0
    assert "indexes_count" in data


def test_cli_export_protected_target_rejection(tmp_path, monkeypatch, capsys):
    cfg_file = tmp_path / "profiler_settings.json"
    cfg_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(workspace_exchange, "PRIVACY_CONFIG_PATH", cfg_file)

    exit_code = main(["--export", str(cfg_file)])
    assert exit_code in (1, 2)
    captured = capsys.readouterr()
    assert "[FEHLER]" in captured.err


def test_cli_import_dry_run(sample_workspace_file, tmp_path, capsys):
    preview_file = tmp_path / "custom_preview.json"
    exit_code = main(["--import", str(sample_workspace_file), "--dry-run", "--preview-path", str(preview_file)])
    assert exit_code == 0
    assert not preview_file.exists()  # dry-run must not write preview!
    captured = capsys.readouterr()
    assert "[DRY-RUN]" in captured.out


def test_cli_import_apply(sample_workspace_file, tmp_path, monkeypatch, capsys):
    preview_file = tmp_path / "custom_preview.json"
    settings_file = tmp_path / "profiler_settings.json"
    settings_file.write_text(json.dumps({"delete_mode": "soft"}), encoding="utf-8")

    # Monkeypatch HeadlessConfigAdapter to write to tmp_path settings
    original_init = HeadlessConfigAdapter.__init__

    def patched_init(self, config_dir=None):
        original_init(self, config_dir=tmp_path)
        self.settings_path = settings_file

    monkeypatch.setattr(HeadlessConfigAdapter, "__init__", patched_init)

    exit_code = main(["--import", str(sample_workspace_file), "--preview-path", str(preview_file)])
    assert exit_code == 0
    assert preview_file.exists()
    captured = capsys.readouterr()
    assert "[OK]" in captured.out


def test_cli_utf8_streams_resilience():
    # Calling multiple times should not raise
    workspace_exchange._ensure_utf8_streams()
    workspace_exchange._ensure_utf8_streams()


def test_headless_config_adapter(tmp_path):
    adapter = HeadlessConfigAdapter(config_dir=tmp_path)
    assert isinstance(adapter.list_connections(), list)
    adapter.set("test_key", "test_value")
    assert adapter.data["test_key"] == "test_value"


def test_summarize_workspace_structure():
    mock_payload = {
        "schema": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "exported_at": "2026-11-01T12:00:00Z",
        "app": {"name": "ProFiler Suite", "version": "15.0.2"},
        "workspace": {"name": "TestWS", "notes": "Notes", "connection_count": 2, "enabled_connection_count": 1},
        "settings": {"ui_language": "de", "theme": "dark"},
        "indexes": [
            {"id": "idx-1", "file_count": 42, "formats": ["pdf", "txt"], "status": "ready"},
            {"id": "idx-2", "file_count": 10, "formats": ["docx", "pdf"], "status": "ready"},
        ],
        "privacy_summary": {"status": "rules_configured", "blacklist_terms_count": 5, "whitelist_terms_count": 2},
        "redactions": {"paths": True, "secrets": True, "raw_documents": False},
        "tool_links": {},
    }
    summary = summarize_workspace(mock_payload)
    assert summary["workspace_name"] == "TestWS"
    assert summary["indexes_count"] == 2
    assert summary["total_files"] == 52
    assert summary["formats"] == ["docx", "pdf", "txt"]
    assert summary["privacy_status"] == "rules_configured"
    assert summary["blacklist_terms_count"] == 5
