"""Redacted workspace export/import helpers for ProFiler."""

from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

APP_NAME = "ProFiler Suite"
SCHEMA_NAME = "profiler-workspace-v1"
SCHEMA_VERSION = 1
APP_VERSION = "15"
CONFIG_DIR = Path.home() / ".profiler_suite"
PRIVACY_CONFIG_PATH = CONFIG_DIR / "datenschutzampel.json"
IMPORTED_WORKSPACE_PATH = CONFIG_DIR / "imported_workspace_preview.json"
WINDOWS_ABS_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")
PATH_HINT_PATTERN = re.compile(r"[\\/]|^[A-Za-z]:")
SAFE_EXPORT_SETTINGS = (
    "ui_language",
    "theme",
    "delete_mode",
    "trash_retention_days",
    "auto_cleanup_enabled",
    "ocr_enabled",
    "ocr_language",
    "default_spawn_format",
    "rename_in_filesystem",
)
SAFE_IMPORT_SETTINGS = SAFE_EXPORT_SETTINGS


class WorkspaceFormatError(ValueError):
    """Raised when a workspace file does not match the expected schema."""


class PathRedactor:
    """Replace absolute local paths with stable references."""

    def __init__(self) -> None:
        self._refs: Dict[str, str] = {}
        self._counters: Counter[str] = Counter()

    def redact(self, value: Any, preferred_prefix: str = "path") -> Any:
        if not isinstance(value, str) or not value:
            return value

        normalized = value.replace("\\", "/")
        if not self._looks_like_path(normalized):
            return value
        if not self._is_absolute_path(normalized):
            return value

        ref = self._register(value, preferred_prefix)
        leaf = Path(value).name
        if leaf:
            return f"[{ref}]/{leaf}"
        return f"[{ref}]"

    def _register(self, original: str, preferred_prefix: str) -> str:
        if original in self._refs:
            return self._refs[original]
        self._counters[preferred_prefix] += 1
        ref = f"{preferred_prefix}-{self._counters[preferred_prefix]}"
        self._refs[original] = ref
        return ref

    @staticmethod
    def _looks_like_path(value: str) -> bool:
        return bool(PATH_HINT_PATTERN.search(value))

    @staticmethod
    def _is_absolute_path(value: str) -> bool:
        return value.startswith("//") or value.startswith("/") or bool(WINDOWS_ABS_PATTERN.match(value))


def export_workspace(
    output_path: str,
    search_manager: Any,
    settings_manager: Any,
    connection_manager: Any,
    exported_at: Optional[datetime] = None,
    privacy_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Write the redacted workspace export and return the payload."""
    payload = build_workspace_export(
        search_manager,
        settings_manager,
        connection_manager,
        exported_at=exported_at,
        privacy_config=privacy_config,
    )
    Path(output_path).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return payload


def build_workspace_export(
    search_manager: Any,
    settings_manager: Any,
    connection_manager: Any,
    exported_at: Optional[datetime] = None,
    privacy_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the workspace export payload."""
    exported_at = exported_at or datetime.now(timezone.utc)
    settings_data = dict(getattr(settings_manager, "data", {}) or {})
    connections = list(_list_connections(connection_manager))
    redactor = PathRedactor()
    privacy_data = privacy_config if privacy_config is not None else _load_json_file(PRIVACY_CONFIG_PATH)

    return {
        "schema": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "exported_at": exported_at.isoformat().replace("+00:00", "Z"),
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION,
        },
        "workspace": _build_workspace_metadata(connections),
        "settings": _build_settings_payload(settings_data),
        "indexes": _build_index_payload(getattr(search_manager, "dbs", []), connections, redactor),
        "privacy_summary": _build_privacy_summary(privacy_data),
        "tool_links": _build_tool_links(settings_data),
        "redactions": {
            "paths": True,
            "secrets": True,
            "raw_documents": False,
        },
    }


def import_workspace(
    input_path: str,
    settings_manager: Any,
    preview_path: Optional[str] = None,
    imported_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Load a workspace export, apply safe settings, and persist a local preview."""
    payload = load_workspace(input_path)
    applied_settings = _apply_imported_settings(settings_manager, payload.get("settings", {}))

    imported_at = imported_at or datetime.now(timezone.utc)
    target_path = Path(preview_path) if preview_path else IMPORTED_WORKSPACE_PATH
    preview_record = {
        "imported_at": imported_at.isoformat().replace("+00:00", "Z"),
        "source_filename": Path(input_path).name,
        "workspace": payload,
    }
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(preview_record, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    workspace = payload.get("workspace", {})
    return {
        "payload": payload,
        "workspace_name": workspace.get("name", APP_NAME),
        "indexes_count": len(payload.get("indexes", [])),
        "applied_settings": applied_settings,
        "preview_path": str(target_path),
        "privacy_status": payload.get("privacy_summary", {}).get("status", "unknown"),
    }


def load_workspace(input_path: str) -> Dict[str, Any]:
    """Load and validate a workspace export."""
    try:
        payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkspaceFormatError(f"Workspace-Datei konnte nicht gelesen werden: {exc}") from exc

    if payload.get("schema") != SCHEMA_NAME:
        raise WorkspaceFormatError(
            f"Falsches Schema: erwartet '{SCHEMA_NAME}', erhalten '{payload.get('schema', '')}'"
        )
    return payload


def _build_workspace_metadata(connections: List[Dict[str, Any]]) -> Dict[str, Any]:
    enabled = [conn for conn in connections if conn.get("enabled", True)]
    if len(enabled) == 1:
        name = enabled[0].get("name") or "ProFiler Workspace"
    elif enabled:
        name = f"ProFiler Workspace ({len(enabled)} Verbindungen)"
    else:
        name = "ProFiler Workspace"

    return {
        "name": name,
        "notes": "Redigierter Export ohne Rohdokumente und ohne lokale Benutzerpfade.",
        "connection_count": len(connections),
        "enabled_connection_count": len(enabled),
    }


def _build_settings_payload(settings_data: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for key in SAFE_EXPORT_SETTINGS:
        if key in settings_data:
            payload[key] = settings_data[key]

    ocr_language = settings_data.get("ocr_language")
    if ocr_language:
        payload["ocr_languages"] = [ocr_language]
    if "theme" not in payload:
        payload["theme"] = "dark"
    return payload


def _build_index_payload(
    db_paths: Iterable[str],
    connections: List[Dict[str, Any]],
    redactor: PathRedactor,
) -> List[Dict[str, Any]]:
    connection_lookup = {
        str(Path(conn.get("db_path", "")).resolve()): conn
        for conn in connections
        if conn.get("db_path")
    }

    summaries: List[Dict[str, Any]] = []
    for raw_db_path in db_paths:
        if not raw_db_path:
            continue
        db_path = Path(raw_db_path)
        conn = connection_lookup.get(str(db_path.resolve()), {})
        summaries.append(_summarize_database(db_path, conn, redactor))
    return summaries


def _summarize_database(db_path: Path, connection: Dict[str, Any], redactor: PathRedactor) -> Dict[str, Any]:
    label = connection.get("name") or db_path.stem
    summary: Dict[str, Any] = {
        "id": connection.get("id") or _slugify(label),
        "label": label,
        "file_count": 0,
        "redacted_root": _redacted_root(connection, redactor),
        "formats": [],
        "enabled": bool(connection.get("enabled", True)),
        "sources_count": len(connection.get("sources", [])),
    }

    if not db_path.exists():
        summary["status"] = "missing"
        return summary

    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(str(db_path))
        version_columns = _table_columns(conn, "versions")
        where_clauses: List[str] = []
        if "is_deleted" in version_columns:
            where_clauses.append("COALESCE(v.is_deleted, 0) = 0")
        if "is_hidden" in version_columns:
            where_clauses.append("COALESCE(v.is_hidden, 0) = 0")
        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        count_sql = f"SELECT COUNT(*) FROM versions v{where_sql}"
        names_sql = f"SELECT v.name FROM versions v{where_sql}"

        summary["file_count"] = int(conn.execute(count_sql).fetchone()[0])
        rows = conn.execute(names_sql).fetchall()
        formats = {
            suffix.lower().lstrip(".")
            for (name,) in rows
            for suffix in [Path(name or "").suffix]
            if suffix
        }
        summary["formats"] = sorted(formats)
        summary["status"] = "ready"
    except sqlite3.Error as exc:
        summary["status"] = "error"
        summary["error"] = exc.__class__.__name__
    finally:
        if conn is not None:
            conn.close()

    return summary


def _build_privacy_summary(privacy_data: Dict[str, Any]) -> Dict[str, Any]:
    blacklist = list(privacy_data.get("blacklist", []) or [])
    whitelist = list(privacy_data.get("whitelist", []) or [])

    status = "rules_configured" if blacklist else "not_configured"
    return {
        "status": status,
        "sensitive_hit_count": 0,
        "categories": [],
        "blacklist_terms_count": len(blacklist),
        "whitelist_terms_count": len(whitelist),
        "clipboard_lock": bool(privacy_data.get("clipboard_lock", False)),
        "whole_words": bool(privacy_data.get("whole_words", False)),
        "case_sensitive": bool(privacy_data.get("case_sensitive", False)),
    }


def _build_tool_links(settings_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "prosync": {
            "enabled": True,
            "configured": bool(settings_data.get("prosync_path")),
        },
        "sqlite_viewer": {
            "configured": bool(settings_data.get("sqlite_viewer_path")),
        },
        "formconstructor": {
            "configured": bool(settings_data.get("formconstructor_path")),
        },
        "datenschutzampel": {
            "configured": PRIVACY_CONFIG_PATH.exists(),
        },
    }


def _apply_imported_settings(settings_manager: Any, imported_settings: Dict[str, Any]) -> List[str]:
    applied: List[str] = []
    for key in SAFE_IMPORT_SETTINGS:
        if key in imported_settings:
            settings_manager.set(key, imported_settings[key])
            applied.append(key)

    ocr_languages = imported_settings.get("ocr_languages")
    if isinstance(ocr_languages, list) and ocr_languages:
        settings_manager.set("ocr_language", ocr_languages[0])
        if "ocr_language" not in applied:
            applied.append("ocr_language")
    return applied


def _load_json_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _list_connections(connection_manager: Any) -> Iterable[Dict[str, Any]]:
    if hasattr(connection_manager, "list_connections"):
        return connection_manager.list_connections()
    return []


def _redacted_root(connection: Dict[str, Any], redactor: PathRedactor) -> str:
    sources = list(connection.get("sources", []) or [])
    if not sources:
        return "[source-root-unknown]"
    return str(redactor.redact(sources[0], "source-root"))


def _table_columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [row[1] for row in rows]


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "index"
