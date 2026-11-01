"""Redacted workspace export/import helpers for ProFiler."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sqlite3
import sys
import tempfile
from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
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
PATH_HINT_PATTERN = re.compile(r"[\\/]|^[A-Za-z]:|^file:")
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
        self._refs: dict[str, str] = {}
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
        key = original.replace("\\", "/").rstrip("/")
        if key in self._refs:
            return self._refs[key]
        self._counters[preferred_prefix] += 1
        ref = f"{preferred_prefix}-{self._counters[preferred_prefix]}"
        self._refs[key] = ref
        return ref

    @staticmethod
    def _looks_like_path(value: str) -> bool:
        return bool(PATH_HINT_PATTERN.search(value))

    @staticmethod
    def _is_absolute_path(value: str) -> bool:
        if value.startswith(("file://", "file:/")):
            return True
        return value.startswith(("//", "/")) or bool(WINDOWS_ABS_PATTERN.match(value))


def export_workspace(
    output_path: str | Path,
    search_manager: Any,
    settings_manager: Any,
    connection_manager: Any,
    exported_at: datetime | None = None,
    privacy_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write the redacted workspace export and return the payload."""
    protected = _workspace_source_paths(search_manager, settings_manager, connection_manager)
    payload = build_workspace_export(
        search_manager,
        settings_manager,
        connection_manager,
        exported_at=exported_at,
        privacy_config=privacy_config,
    )
    _write_json_atomic(Path(output_path), payload, protected_paths=protected,
                       refresh_paths=lambda: _workspace_source_paths(search_manager, settings_manager, connection_manager))
    return payload


def build_workspace_export(
    search_manager: Any,
    settings_manager: Any,
    connection_manager: Any,
    exported_at: datetime | None = None,
    privacy_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
        "tool_links": _build_tool_links(settings_data, privacy_data),
        "redactions": {
            "paths": True,
            "secrets": True,
            "raw_documents": False,
        },
    }
    _validate_workspace_payload(payload)
    return payload


def import_workspace(
    input_path: str | Path,
    settings_manager: Any,
    preview_path: str | None = None,
    imported_at: datetime | None = None,
) -> dict[str, Any]:
    """Load a workspace export, apply safe settings, and persist a local preview."""
    payload = load_workspace(input_path)

    imported_at = imported_at or datetime.now(timezone.utc)
    target_path = Path(preview_path) if preview_path else IMPORTED_WORKSPACE_PATH
    preview_record = {
        "imported_at": imported_at.isoformat().replace("+00:00", "Z"),
        "source_filename": Path(input_path).name,
        "workspace": payload,
    }
    protected = _configuration_paths(settings_manager)
    protected.add(Path(input_path).absolute())
    _write_json_atomic(target_path, preview_record, protected_paths=protected,
                       refresh_paths=lambda: _configuration_paths(settings_manager))
    applied_settings = _apply_imported_settings(settings_manager, payload.get("settings", {}))

    workspace = payload.get("workspace", {})
    return {
        "payload": payload,
        "workspace_name": workspace.get("name", APP_NAME),
        "indexes_count": len(payload.get("indexes", [])),
        "applied_settings": applied_settings,
        "preview_path": str(target_path),
        "privacy_status": payload.get("privacy_summary", {}).get("status", "unknown"),
    }


def load_workspace(input_path: str | Path) -> dict[str, Any]:
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
    except WorkspaceFormatError:
        raise
    except (OSError, ValueError) as exc:
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


def _validate_import_settings(settings: dict[str, Any]) -> None:
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
        if key == "trash_retention_days" and (value < 0 or value > 3650):
            raise WorkspaceFormatError(
                "Einstellung 'trash_retention_days' muss zwischen 0 und 3650 Tagen liegen"
            )
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


def _build_workspace_metadata(connections: list[dict[str, Any]]) -> dict[str, Any]:
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


def _build_settings_payload(settings_data: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key in SAFE_EXPORT_SETTINGS:
        if key in settings_data:
            payload[key] = settings_data[key]

    delete_mode = payload.get("delete_mode")
    if delete_mode is not None and delete_mode not in {"soft", "safety"}:
        payload["delete_mode"] = "soft"

    ocr_language = settings_data.get("ocr_language")
    if ocr_language:
        payload["ocr_languages"] = [ocr_language]
    if "theme" not in payload:
        payload["theme"] = "dark"
    return payload


def _build_index_payload(
    db_paths: Iterable[str],
    connections: list[dict[str, Any]],
    redactor: PathRedactor,
) -> list[dict[str, Any]]:
    connection_lookup: dict[str, dict[str, Any]] = {}
    for conn in connections:
        raw_conn_db = conn.get("db_path")
        if not raw_conn_db:
            continue
        try:
            resolved_key = str(Path(raw_conn_db).resolve())
            connection_lookup[resolved_key] = conn
        except (OSError, RuntimeError):
            connection_lookup[str(raw_conn_db)] = conn

    summaries: list[dict[str, Any]] = []
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


def _summarize_database(db_path: Path, connection: dict[str, Any], redactor: PathRedactor) -> dict[str, Any]:
    label = _safe_label(connection.get("name"), "ProFiler Index")
    sources = connection.get("sources")
    sources_count = len(sources) if isinstance(sources, (list, tuple, set)) else 0
    summary: dict[str, Any] = {
        "id": _safe_identifier(connection.get("id"), _slugify(label)),
        "label": label,
        "file_count": 0,
        "redacted_root": _redacted_root(connection, redactor),
        "formats": [],
        "enabled": bool(connection.get("enabled", True)),
        "sources_count": sources_count,
    }

    try:
        if not db_path.exists():
            summary["status"] = "missing"
            return summary
    except (OSError, RuntimeError):
        summary["status"] = "missing"
        return summary

    conn: sqlite3.Connection | None = None
    try:
        db_uri = f"file:{quote(db_path.resolve().as_posix(), safe='/:')}?mode=ro"
        conn = sqlite3.connect(db_uri, uri=True)
        version_columns = _table_columns(conn, "versions")
        where_clauses: list[str] = []
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
    except (sqlite3.Error, OSError, RuntimeError) as exc:
        summary["status"] = "error"
        summary["error"] = exc.__class__.__name__
    finally:
        if conn is not None:
            conn.close()

    return summary


def _build_privacy_summary(privacy_data: dict[str, Any]) -> dict[str, Any]:
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


def _build_tool_links(
    settings_data: dict[str, Any],
    privacy_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    privacy_configured = False
    if privacy_data:
        privacy_configured = bool(
            privacy_data.get("blacklist") or privacy_data.get("whitelist")
        )
    if not privacy_configured:
        privacy_configured = resolve_read_path(PRIVACY_CONFIG_PATH.name).exists()

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
            "configured": privacy_configured,
        },
    }


def _apply_imported_settings(settings_manager: Any, imported_settings: dict[str, Any]) -> list[str]:
    applied: list[str] = []
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


def _load_json_file(path: Path) -> dict[str, Any]:
    read_path = resolve_read_path(path.name)
    if not read_path.exists():
        return {}
    try:
        return json.loads(read_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}


def _list_connections(connection_manager: Any) -> Iterable[dict[str, Any]]:
    if hasattr(connection_manager, "list_connections"):
        return connection_manager.list_connections()
    return []


def _redacted_root(connection: dict[str, Any], redactor: PathRedactor) -> str:
    sources = list(connection.get("sources", []) or [])
    for raw in sources:
        if isinstance(raw, str) and raw.strip():
            candidate = raw.strip()
            redacted = redactor.redact(candidate, "source-root")
            if str(redacted).startswith("[") and str(redacted).endswith("]"):
                return str(redacted)
            ref = redactor._register(candidate, "source-root")
            return f"[{ref}]"
    return "[source-root-unknown]"


def _table_columns(conn: sqlite3.Connection, table_name: str) -> list[str]:
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


def _configuration_paths(*managers: Any) -> set[Path]:
    names = ("profiler_settings.json", "search_config.json", "connections.json",
             "profiler_config.json", "datenschutzampel.json")
    paths = {Path(PRIVACY_CONFIG_PATH)}
    for name in names:
        paths.update((config_path(name), resolve_read_path(name)))
    for manager in managers:
        value = getattr(manager, "path", None)
        if value:
            paths.add(Path(value))
    return paths


def _workspace_source_paths(search_manager: Any, settings_manager: Any,
                            connection_manager: Any) -> set[Path]:
    databases = list(getattr(search_manager, "dbs", []) or [])
    databases.extend(item.get("db_path") for item in _list_connections(connection_manager))
    paths = _configuration_paths(search_manager, settings_manager, connection_manager)
    paths.add(Path(IMPORTED_WORKSPACE_PATH))
    for name in databases:
        if not name or str(name) == ":memory:":
            continue
        for path in (Path(name).absolute(), Path(name).resolve()):
            paths.add(path)
            paths.update(Path(str(path) + suffix) for suffix in ("-wal", "-shm", "-journal"))
    return {Path(os.path.abspath(path)) for path in paths}


def _check_workspace_target(target: Path, protected_paths: Iterable[Path]) -> None:
    lexical = Path(os.path.abspath(target))
    if os.name == "nt" and any(
        part not in (".", "..") and part.endswith((" ", ".")) for part in target.parts
    ):
        raise WorkspaceFormatError("Das Ziel enthält einen mehrdeutigen Windows-Dateinamen.")
    resolved = target.resolve()
    for protected in protected_paths:
        protected = Path(protected)
        if lexical == Path(os.path.abspath(protected)) or resolved == protected.resolve():
            raise WorkspaceFormatError("Das Ziel ist eine geschützte Quelldatei. Bitte einen anderen Pfad wählen.")
        try:
            identical = os.path.samefile(target, protected)
        except FileNotFoundError:
            identical = False
        if identical:
            raise WorkspaceFormatError("Das Ziel ist eine geschützte Quelldatei. Bitte einen anderen Pfad wählen.")


def _write_json_atomic(target: Path, payload: dict[str, Any],
                       protected_paths: Iterable[Path] = (), refresh_paths=None) -> None:
    target = target.absolute()
    protected = set(protected_paths)
    _check_workspace_target(target, protected)
    serialized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent,
                                         prefix=".profiler-workspace-", suffix=".tmp",
                                         delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        if refresh_paths is not None:
            protected.update(refresh_paths())
        _check_workspace_target(target, protected)
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                logging.getLogger(__name__).warning("Eigene temporäre Workspace-Datei konnte nicht entfernt werden: %s", temporary, exc_info=True)


class HeadlessConfigAdapter:
    """Headless configuration adapter for workspace export/import without Qt."""

    def __init__(self, config_dir: Path | None = None) -> None:
        self.config_dir = config_dir or CONFIG_DIR
        self.settings_path = config_path("profiler_settings.json")
        self.search_path = config_path("search_config.json")
        self.connections_path = config_path("connections.json")
        self.dbs: list[str] = []
        self.data: dict[str, Any] = {
            "delete_mode": "soft",
            "trash_retention_days": 30,
            "auto_cleanup_enabled": True,
            "ocr_language": "deu",
            "ocr_enabled": True,
            "prosync_path": "",
            "theme": "dark",
            "ui_language": "de",
        }
        self.connections: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        read_settings = resolve_read_path(self.settings_path.name)
        if read_settings.exists():
            try:
                loaded = json.loads(read_settings.read_text(encoding="utf-8-sig"))
                if isinstance(loaded, dict):
                    self.data.update(loaded)
            except (OSError, ValueError):
                pass

        read_search = resolve_read_path(self.search_path.name)
        if read_search.exists():
            try:
                loaded = json.loads(read_search.read_text(encoding="utf-8-sig"))
                if isinstance(loaded, dict):
                    self.dbs = list(loaded.get("databases", []))
            except (OSError, ValueError):
                pass

        read_conn = resolve_read_path(self.connections_path.name)
        if read_conn.exists():
            try:
                loaded = json.loads(read_conn.read_text(encoding="utf-8-sig"))
                if isinstance(loaded, dict):
                    self.connections = list(loaded.get("connections", []))
            except (OSError, ValueError):
                pass

    def list_connections(self) -> list[dict[str, Any]]:
        return list(self.connections)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def save(self) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.settings_path.with_suffix(f".tmp.{os.getpid()}")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.settings_path)
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass


def summarize_workspace(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate a structured summary dictionary from a validated workspace payload."""
    workspace = payload.get("workspace", {})
    indexes = payload.get("indexes", [])
    total_files = sum(int(idx.get("file_count", 0)) for idx in indexes if isinstance(idx, dict))
    all_formats = sorted({
        fmt.lower()
        for idx in indexes if isinstance(idx, dict)
        for fmt in idx.get("formats", [])
        if isinstance(fmt, str) and fmt
    })
    settings = payload.get("settings", {})
    privacy = payload.get("privacy_summary", {})
    redactions = payload.get("redactions", {})
    app = payload.get("app", {})

    return {
        "schema": payload.get("schema", SCHEMA_NAME),
        "schema_version": payload.get("schema_version", SCHEMA_VERSION),
        "exported_at": payload.get("exported_at", ""),
        "app_name": app.get("name", APP_NAME),
        "app_version": app.get("version", APP_VERSION),
        "workspace_name": workspace.get("name", APP_NAME),
        "workspace_notes": workspace.get("notes", ""),
        "connection_count": int(workspace.get("connection_count", 0)),
        "enabled_connection_count": int(workspace.get("enabled_connection_count", 0)),
        "indexes_count": len(indexes),
        "total_files": total_files,
        "formats": all_formats,
        "settings_count": len(settings),
        "settings": dict(settings),
        "privacy_status": privacy.get("status", "unknown"),
        "blacklist_terms_count": int(privacy.get("blacklist_terms_count", 0)),
        "whitelist_terms_count": int(privacy.get("whitelist_terms_count", 0)),
        "redactions": dict(redactions),
    }


def _ensure_utf8_streams() -> None:
    """Ensure stdout and stderr use UTF-8 on Windows consoles to prevent cp1252 errors."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser for workspace exchange."""
    parser = argparse.ArgumentParser(
        prog="workspace_exchange",
        description="ProFiler Workspace Exchange CLI (v1) — Validierung, Inspektion, Export und Import von Arbeitsständen.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--validate",
        metavar="DATEI",
        help="Workspace-Datei gegen das profiler-workspace-v1 Schema validieren",
    )
    group.add_argument(
        "--info",
        metavar="DATEI",
        help="Detaillierte Struktur- und Metadaten-Übersicht eines Snapshots anzeigen",
    )
    group.add_argument(
        "--export",
        metavar="ZIELDATEI",
        help="Aktuelle ProFiler-Workspace-Konfiguration und Indizes exportieren",
    )
    group.add_argument(
        "--import",
        dest="import_file",
        metavar="QUELLDATEI",
        help="Workspace-Snapshot importieren und sichere Einstellungen übernehmen",
    )
    parser.add_argument(
        "--preview-path",
        metavar="PFAD",
        help="Zielpfad für die importierte Workspace-Vorschau (Standard: imported_workspace_preview.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Validierung und Simulation; keine Änderungen an Einstellungen oder Vorschau",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Ergebnisse maschinenlesbar als JSON ausgeben",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI-Haupteinstiegspunkt für workspace_exchange."""
    _ensure_utf8_streams()
    parser = build_arg_parser()

    if argv is None and len(sys.argv) == 1:
        parser.print_help()
        return 2

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2

    is_json = bool(args.json)

    if args.validate:
        target = Path(args.validate)
        try:
            if not target.exists():
                err_msg = f"Datei existiert nicht: {target}"
                if is_json:
                    print(json.dumps({"valid": False, "file": str(target), "error": err_msg, "error_type": "FileNotFoundError"}, ensure_ascii=False))
                else:
                    print(f"[FEHLER] {err_msg}", file=sys.stderr)
                return 2
            load_workspace(target)
            if is_json:
                print(json.dumps({"valid": True, "file": str(target), "schema": SCHEMA_NAME, "schema_version": SCHEMA_VERSION}, ensure_ascii=False))
            else:
                print(f"[OK] Valide Workspace-Datei: {target} (Schema: {SCHEMA_NAME} v{SCHEMA_VERSION})")
            return 0
        except WorkspaceFormatError as exc:
            if is_json:
                print(json.dumps({"valid": False, "file": str(target), "error": str(exc), "error_type": "WorkspaceFormatError"}, ensure_ascii=False))
            else:
                print(f"[FEHLER] Ungültiges Workspace-Format in {target}: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            if is_json:
                print(json.dumps({"valid": False, "file": str(target), "error": str(exc), "error_type": exc.__class__.__name__}, ensure_ascii=False))
            else:
                print(f"[FEHLER] E/A-Fehler beim Lesen von {target}: {exc}", file=sys.stderr)
            return 2

    if args.info:
        target = Path(args.info)
        try:
            if not target.exists():
                err_msg = f"Datei existiert nicht: {target}"
                if is_json:
                    print(json.dumps({"success": False, "file": str(target), "error": err_msg, "error_type": "FileNotFoundError"}, ensure_ascii=False))
                else:
                    print(f"[FEHLER] {err_msg}", file=sys.stderr)
                return 2
            payload = load_workspace(target)
            summary = summarize_workspace(payload)
            if is_json:
                print(json.dumps(summary, indent=2, ensure_ascii=False))
            else:
                formats_str = ", ".join(summary["formats"]) if summary["formats"] else "keine"
                settings_keys = ", ".join(sorted(summary["settings"].keys())) if summary["settings"] else "keine"
                print("=" * 60)
                print(f"  ProFiler Workspace-Snapshot: {summary['workspace_name']}")
                print("=" * 60)
                print(f"  Schema:         {summary['schema']} (v{summary['schema_version']})")
                print(f"  Exportiert am:  {summary['exported_at']}")
                print(f"  Anwendung:      {summary['app_name']} v{summary['app_version']}")
                print(f"  Verbindungen:   {summary['enabled_connection_count']} / {summary['connection_count']} aktiv")
                print(f"  Indizes:        {summary['indexes_count']} ({summary['total_files']} Dateien)")
                print(f"  Formate:        {formats_str}")
                print(f"  Einstellungen:  {settings_keys}")
                print(f"  Datenschutz:    {summary['privacy_status']} ({summary['blacklist_terms_count']} Blacklist, {summary['whitelist_terms_count']} Whitelist)")
                print(f"  Redaktion:      Pfade={summary['redactions'].get('paths')}, Secrets={summary['redactions'].get('secrets')}, Rohdokumente={summary['redactions'].get('raw_documents')}")
                print("=" * 60)
            return 0
        except WorkspaceFormatError as exc:
            if is_json:
                print(json.dumps({"success": False, "file": str(target), "error": str(exc), "error_type": "WorkspaceFormatError"}, ensure_ascii=False))
            else:
                print(f"[FEHLER] Ungültiges Workspace-Format in {target}: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            if is_json:
                print(json.dumps({"success": False, "file": str(target), "error": str(exc), "error_type": exc.__class__.__name__}, ensure_ascii=False))
            else:
                print(f"[FEHLER] E/A-Fehler beim Lesen von {target}: {exc}", file=sys.stderr)
            return 2

    if args.export:
        target = Path(args.export)
        adapter = HeadlessConfigAdapter()
        try:
            payload = export_workspace(
                target,
                adapter,
                adapter,
                adapter,
            )
            file_size = target.stat().st_size if target.exists() else 0
            if is_json:
                print(json.dumps({
                    "success": True,
                    "exported_file": str(target),
                    "file_size": file_size,
                    "workspace_name": payload.get("workspace", {}).get("name", APP_NAME),
                    "indexes_count": len(payload.get("indexes", [])),
                }, ensure_ascii=False))
            else:
                print(f"[OK] Workspace erfolgreich exportiert nach: {target}")
                print(f"     Dateigröße: {file_size} Bytes | Indizes: {len(payload.get('indexes', []))}")
            return 0
        except WorkspaceFormatError as exc:
            if is_json:
                print(json.dumps({"success": False, "target": str(target), "error": str(exc), "error_type": "WorkspaceFormatError"}, ensure_ascii=False))
            else:
                print(f"[FEHLER] Export abgelehnt: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            if is_json:
                print(json.dumps({"success": False, "target": str(target), "error": str(exc), "error_type": exc.__class__.__name__}, ensure_ascii=False))
            else:
                print(f"[FEHLER] E/A-Fehler beim Export nach {target}: {exc}", file=sys.stderr)
            return 2

    if args.import_file:
        source = Path(args.import_file)
        try:
            if not source.exists():
                err_msg = f"Datei existiert nicht: {source}"
                if is_json:
                    print(json.dumps({"success": False, "file": str(source), "error": err_msg, "error_type": "FileNotFoundError"}, ensure_ascii=False))
                else:
                    print(f"[FEHLER] {err_msg}", file=sys.stderr)
                return 2

            if args.dry_run:
                payload = load_workspace(source)
                settings = payload.get("settings", {})
                applicable = [k for k in SAFE_IMPORT_SETTINGS if k in settings]
                if is_json:
                    print(json.dumps({
                        "success": True,
                        "dry_run": True,
                        "file": str(source),
                        "workspace_name": payload.get("workspace", {}).get("name", APP_NAME),
                        "indexes_count": len(payload.get("indexes", [])),
                        "applicable_settings": applicable,
                    }, ensure_ascii=False))
                else:
                    print(f"[DRY-RUN] Workspace-Snapshot ist valide: {source}")
                    print(f"          Workspace: {payload.get('workspace', {}).get('name', APP_NAME)}")
                    print(f"          Indizes im Snapshot: {len(payload.get('indexes', []))}")
                    print(f"          Anwendbare Einstellungen: {', '.join(applicable) if applicable else 'keine'}")
                return 0

            adapter = HeadlessConfigAdapter()
            result = import_workspace(source, adapter, preview_path=args.preview_path)
            adapter.save()
            if is_json:
                print(json.dumps({
                    "success": True,
                    "file": str(source),
                    "workspace_name": result["workspace_name"],
                    "indexes_count": result["indexes_count"],
                    "applied_settings": result["applied_settings"],
                    "preview_path": result["preview_path"],
                }, ensure_ascii=False))
            else:
                applied_str = ", ".join(result["applied_settings"]) if result["applied_settings"] else "keine"
                print(f"[OK] Workspace erfolgreich importiert: {source}")
                print(f"     Workspace: {result['workspace_name']}")
                print(f"     Indizes im Snapshot: {result['indexes_count']}")
                print(f"     Übernommene Einstellungen: {applied_str}")
                print(f"     Vorschau gespeichert unter: {result['preview_path']}")
            return 0
        except WorkspaceFormatError as exc:
            if is_json:
                print(json.dumps({"success": False, "file": str(source), "error": str(exc), "error_type": "WorkspaceFormatError"}, ensure_ascii=False))
            else:
                print(f"[FEHLER] Import abgelehnt: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            if is_json:
                print(json.dumps({"success": False, "file": str(source), "error": str(exc), "error_type": exc.__class__.__name__}, ensure_ascii=False))
            else:
                print(f"[FEHLER] E/A-Fehler beim Import von {source}: {exc}", file=sys.stderr)
            return 2

    return 2


if __name__ == "__main__":
    sys.exit(main())
