"""Redacted workspace export/import helpers for ProFiler."""

from __future__ import annotations

import json
import os
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote

from app_paths import app_data_dir, config_path, resolve_read_path
from version import APP_VERSION

APP_NAME = "ProFiler Suite"
SCHEMA_NAME = "profiler-workspace-v1"
SCHEMA_VERSION = 1
CONFIG_DIR = app_data_dir()
PRIVACY_CONFIG_PATH = config_path("datenschutzampel.json")
IMPORTED_WORKSPACE_PATH = config_path("imported_workspace_preview.json")
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
MAX_WORKSPACE_BYTES = 5 * 1024 * 1024
MAX_CONTAINER_ITEMS = 2_000
MAX_TREE_NODES = 20_000
MAX_TREE_DEPTH = 12
MAX_STRING_LENGTH = 8_192
SENSITIVE_KEY_PATTERN = re.compile(
    r"(?:password|passwd|passphrase|api[_-]?key|token|secret|private[_-]?key|authorization)",
    re.IGNORECASE,
)
REQUIRED_TOP_LEVEL_KEYS = frozenset({
    "schema",
    "schema_version",
    "workspace",
    "settings",
    "indexes",
    "privacy_summary",
    "tool_links",
    "redactions",
})


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
    _write_json_atomic(Path(output_path), payload)
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

    payload = {
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
    _validate_workspace_payload(payload)
    return payload


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
    _write_json_atomic(target_path, preview_record)

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
    source = Path(input_path)
    try:
        if not source.is_file():
            raise OSError("Pfad ist keine reguläre Datei")
        size = source.stat().st_size
        if size > MAX_WORKSPACE_BYTES:
            raise WorkspaceFormatError(
                f"Workspace-Datei ist größer als {MAX_WORKSPACE_BYTES} Bytes"
            )
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkspaceFormatError(f"Workspace-Datei konnte nicht gelesen werden: {exc}") from exc

    _validate_workspace_payload(payload)
    return payload


def _validate_workspace_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise WorkspaceFormatError("Workspace-Wurzel muss ein JSON-Objekt sein")
    if payload.get("schema") != SCHEMA_NAME:
        raise WorkspaceFormatError(
            f"Falsches Schema: erwartet '{SCHEMA_NAME}', erhalten '{payload.get('schema', '')}'"
        )
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise WorkspaceFormatError(
            f"Nicht unterstützte Schema-Version: {payload.get('schema_version')!r}"
        )

    missing = REQUIRED_TOP_LEVEL_KEYS - payload.keys()
    if missing:
        raise WorkspaceFormatError(
            f"Workspace-Pflichtfelder fehlen: {', '.join(sorted(missing))}"
        )
    for key in ("workspace", "settings", "privacy_summary", "tool_links", "redactions"):
        if not isinstance(payload.get(key), dict):
            raise WorkspaceFormatError(f"Workspace-Feld '{key}' muss ein Objekt sein")
    if not isinstance(payload.get("indexes"), list):
        raise WorkspaceFormatError("Workspace-Feld 'indexes' muss eine Liste sein")

    redactions = payload["redactions"]
    if redactions.get("paths") is not True or redactions.get("secrets") is not True:
        raise WorkspaceFormatError("Workspace bestätigt Pfad-/Secret-Redaktion nicht")
    if redactions.get("raw_documents") is not False:
        raise WorkspaceFormatError("Workspace darf keine Rohdokumente enthalten")

    _validate_safe_tree(payload)
    _validate_import_settings(payload["settings"])


def _validate_safe_tree(value: Any) -> None:
    nodes = 0
    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAX_TREE_NODES:
            raise WorkspaceFormatError("Workspace enthält zu viele Werte")
        if depth > MAX_TREE_DEPTH:
            raise WorkspaceFormatError("Workspace ist zu tief verschachtelt")

        if isinstance(current, dict):
            if len(current) > MAX_CONTAINER_ITEMS:
                raise WorkspaceFormatError("Workspace-Objekt enthält zu viele Felder")
            for key, nested in current.items():
                if not isinstance(key, str):
                    raise WorkspaceFormatError("Workspace-Schlüssel müssen Text sein")
                if key != "secrets" and SENSITIVE_KEY_PATTERN.search(key):
                    raise WorkspaceFormatError(f"Sensibles Feld ist nicht erlaubt: {key}")
                stack.append((nested, depth + 1))
        elif isinstance(current, list):
            if len(current) > MAX_CONTAINER_ITEMS:
                raise WorkspaceFormatError("Workspace-Liste enthält zu viele Einträge")
            stack.extend((item, depth + 1) for item in current)
        elif isinstance(current, str):
            if len(current) > MAX_STRING_LENGTH:
                raise WorkspaceFormatError("Workspace-Text ist zu lang")
            normalized = current.replace("\\", "/")
            if PathRedactor._is_absolute_path(normalized):
                raise WorkspaceFormatError("Workspace enthält einen absoluten lokalen Pfad")
        elif current is not None and not isinstance(current, (bool, int, float)):
            raise WorkspaceFormatError("Workspace enthält einen nicht unterstützten Werttyp")


def _validate_import_settings(settings: Dict[str, Any]) -> None:
    unknown = set(settings) - set(SAFE_IMPORT_SETTINGS) - {"ocr_languages"}
    if unknown:
        raise WorkspaceFormatError(
            f"Nicht unterstützte Einstellungen: {', '.join(sorted(unknown))}"
        )

    bool_keys = {"auto_cleanup_enabled", "ocr_enabled", "rename_in_filesystem"}
    int_keys = {"trash_retention_days"}
    string_keys = set(SAFE_IMPORT_SETTINGS) - bool_keys - int_keys
    for key, value in settings.items():
        if key in bool_keys and not isinstance(value, bool):
            raise WorkspaceFormatError(f"Einstellung '{key}' muss boolesch sein")
        if key in int_keys and (not isinstance(value, int) or isinstance(value, bool)):
            raise WorkspaceFormatError(f"Einstellung '{key}' muss eine Ganzzahl sein")
        if key in string_keys and not isinstance(value, str):
            raise WorkspaceFormatError(f"Einstellung '{key}' muss Text sein")
    delete_mode = settings.get("delete_mode")
    if delete_mode is not None and delete_mode not in {"soft", "safety"}:
        raise WorkspaceFormatError(
            "Workspace darf nur die Löschmodi 'soft' oder 'safety' übernehmen"
        )
    languages = settings.get("ocr_languages")
    if languages is not None and (
        not isinstance(languages, list)
        or not languages
        or len(languages) > 8
        or any(not isinstance(item, str) or not item or len(item) > 32 for item in languages)
    ):
        raise WorkspaceFormatError("Einstellung 'ocr_languages' ist ungültig")


def _build_workspace_metadata(connections: List[Dict[str, Any]]) -> Dict[str, Any]:
    enabled = [conn for conn in connections if conn.get("enabled", True)]
    if len(enabled) == 1:
        name = _safe_label(enabled[0].get("name"), "ProFiler Workspace")
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
    connection_lookup: Dict[str, Dict[str, Any]] = {}
    for conn in connections:
        raw_conn_db = conn.get("db_path")
        if not raw_conn_db:
            continue
        try:
            resolved_key = str(Path(raw_conn_db).resolve())
            connection_lookup[resolved_key] = conn
        except (OSError, RuntimeError):
            connection_lookup[str(raw_conn_db)] = conn

    summaries: List[Dict[str, Any]] = []
    for raw_db_path in db_paths:
        if not raw_db_path:
            continue
        db_path = Path(raw_db_path)
        try:
            resolved_str = str(db_path.resolve())
        except (OSError, RuntimeError):
            resolved_str = str(db_path)
        conn = connection_lookup.get(resolved_str, {})
        summaries.append(_summarize_database(db_path, conn, redactor))
    return summaries


def _summarize_database(db_path: Path, connection: Dict[str, Any], redactor: PathRedactor) -> Dict[str, Any]:
    label = _safe_label(connection.get("name"), "ProFiler Index")
    summary: Dict[str, Any] = {
        "id": _safe_identifier(connection.get("id"), _slugify(label)),
        "label": label,
        "file_count": 0,
        "redacted_root": _redacted_root(connection, redactor),
        "formats": [],
        "enabled": bool(connection.get("enabled", True)),
        "sources_count": len(connection.get("sources", [])),
    }

    try:
        if not db_path.exists():
            summary["status"] = "missing"
            return summary
    except (OSError, RuntimeError):
        summary["status"] = "missing"
        return summary

    conn: Optional[sqlite3.Connection] = None
    try:
        db_uri = f"file:{quote(db_path.resolve().as_posix(), safe='/:')}?mode=ro"
        conn = sqlite3.connect(db_uri, uri=True)
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
    read_path = resolve_read_path(path.name)
    if not read_path.exists():
        return {}
    try:
        return json.loads(read_path.read_text(encoding="utf-8-sig"))
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


def _safe_label(value: Any, fallback: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return fallback
    candidate = value.strip()
    normalized = candidate.replace("\\", "/")
    if PathRedactor._is_absolute_path(normalized) or len(candidate) > 120:
        return fallback
    return candidate


def _safe_identifier(value: Any, fallback: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return fallback
    candidate = value.strip()
    normalized = candidate.replace("\\", "/")
    if PathRedactor._is_absolute_path(normalized):
        return fallback
    safe = re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", candidate)
    return candidate if safe else fallback


def _write_json_atomic(target: Path, payload: Dict[str, Any]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    try:
        temporary.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
