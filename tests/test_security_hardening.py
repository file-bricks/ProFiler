from __future__ import annotations

import io
import json
import sqlite3
import sys
import zipfile
from pathlib import Path
from unittest import mock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def _make_import_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(
            """
            CREATE TABLE files (id INTEGER PRIMARY KEY, content_hash TEXT, size INTEGER);
            CREATE TABLE versions (
                id INTEGER PRIMARY KEY,
                file_id INTEGER,
                name TEXT,
                path TEXT
            );
            CREATE TABLE tags (file_id INTEGER, tag TEXT);
            CREATE TABLE collections (id INTEGER PRIMARY KEY, name TEXT, description TEXT, created_at TEXT);
            CREATE TABLE collection_items (collection_id INTEGER, version_id INTEGER, added_at TEXT);
            """
        )
        conn.commit()
    finally:
        conn.close()


def test_settings_passwords_are_session_only_and_legacy_values_are_purged(monkeypatch, tmp_path: Path) -> None:
    import Profiler_Suite_V15 as profiler

    settings_path = tmp_path / "profiler_settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "theme": "dark",
                "pdf_master_password_open": "legacy-open",
                "pdf_master_password_save": "legacy-save",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(profiler, "SETTINGS_PATH", str(settings_path))
    monkeypatch.setattr(profiler, "resolve_read_path", lambda _name: settings_path)

    settings = profiler.SettingsManager()
    assert settings.get("pdf_master_password_open") == ""
    assert settings.get("pdf_master_password_save") == ""

    settings.set("pdf_master_password_open", "runtime-only")
    settings.set("pdf_master_password_save", "also-runtime-only")
    persisted = json.loads(settings_path.read_text(encoding="utf-8"))

    assert settings.get("pdf_master_password_open") == "runtime-only"
    assert settings.get("pdf_master_password_save") == "also-runtime-only"
    assert "pdf_master_password_open" not in persisted
    assert "pdf_master_password_save" not in persisted


def test_excel_cleanup_refuses_unowned_output_folder(tmp_path: Path) -> None:
    from import_excel_to_profiler import ImportSafetyError, ProfilerAutismoImporter

    db_path = tmp_path / "profiler.db"
    _make_import_db(db_path)
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")

    importer = ProfilerAutismoImporter(db_path, output)
    with pytest.raises(ImportSafetyError):
        importer.cleanup_previous_import()
    importer.close()

    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_excel_cleanup_keeps_file_rows_shared_with_non_import_versions(tmp_path: Path) -> None:
    from import_excel_to_profiler import ProfilerAutismoImporter

    db_path = tmp_path / "profiler.db"
    _make_import_db(db_path)
    output = tmp_path / "owned-import"
    importer = ProfilerAutismoImporter(db_path, output)
    importer.prepare_output_folder()
    imported_file = output / "generated.txt"
    imported_file.write_text("generated", encoding="utf-8")

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("INSERT INTO files(id, content_hash, size) VALUES (1, 'hash', 9)")
        conn.execute(
            "INSERT INTO versions(id, file_id, name, path) VALUES (1, 1, 'generated.txt', ?)",
            (str(imported_file.resolve()),),
        )
        conn.execute(
            "INSERT INTO versions(id, file_id, name, path) VALUES (2, 1, 'outside.txt', ?)",
            (str((tmp_path / 'outside.txt').resolve()),),
        )
        conn.execute("INSERT INTO tags(file_id, tag) VALUES (1, 'shared')")
        conn.execute("INSERT INTO collection_items(collection_id, version_id, added_at) VALUES (1, 1, 'now')")
        conn.commit()
    finally:
        conn.close()

    importer.cleanup_previous_import()
    importer.close()

    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("SELECT id FROM versions ORDER BY id").fetchall() == [(2,)]
        assert conn.execute("SELECT id FROM files").fetchall() == [(1,)]
        assert conn.execute("SELECT tag FROM tags").fetchall() == [("shared",)]
    finally:
        conn.close()


def test_workspace_import_rejects_wrong_version_paths_and_secret_keys(tmp_path: Path) -> None:
    from workspace_exchange import WorkspaceFormatError, load_workspace

    base = {
        "schema": "profiler-workspace-v1",
        "schema_version": 1,
        "workspace": {"name": "Demo"},
        "settings": {},
        "indexes": [],
        "privacy_summary": {},
        "tool_links": {},
        "redactions": {"paths": True, "secrets": True, "raw_documents": False},
    }

    for mutation in (
        {"schema_version": 2},
        {"workspace": {"name": r"C:\\Users\\Alice\\Secret"}},
        {"settings": {"api_token": "should-not-enter-preview"}},
        {"settings": {"delete_mode": "hard"}},
    ):
        payload = dict(base)
        payload.update(mutation)
        candidate = tmp_path / f"bad-{len(list(tmp_path.iterdir()))}.json"
        candidate.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(WorkspaceFormatError):
            load_workspace(str(candidate))


def test_workspace_import_rejects_oversized_file(tmp_path: Path) -> None:
    from workspace_exchange import (
        MAX_WORKSPACE_BYTES,
        WorkspaceFormatError,
        load_workspace,
    )

    candidate = tmp_path / "too-large.json"
    candidate.write_bytes(b" " * (MAX_WORKSPACE_BYTES + 1))
    with pytest.raises(WorkspaceFormatError):
        load_workspace(str(candidate))


def test_workspace_export_redacts_path_shaped_connection_identity(tmp_path: Path) -> None:
    from workspace_exchange import build_workspace_export

    class Search:
        dbs = [str(tmp_path / "missing.db")]

    class Settings:
        data = {"theme": "dark"}

    class Connections:
        @staticmethod
        def list_connections():
            return [
                {
                    "id": r"C:\\Users\\Alice\\Case-A",
                    "name": r"C:\\Users\\Alice\\Case-A",
                    "db_path": str(tmp_path / "missing.db"),
                    "sources": [r"C:\\Users\\Alice\\Documents"],
                    "enabled": True,
                }
            ]

    payload = build_workspace_export(Search(), Settings(), Connections(), privacy_config={})
    serialized = json.dumps(payload, ensure_ascii=False)

    assert r"C:\\Users\\Alice" not in serialized
    assert payload["workspace"]["name"] == "ProFiler Workspace"
    assert payload["indexes"][0]["label"] == "ProFiler Index"
    assert payload["indexes"][0]["redacted_root"] == "[source-root-1]"


def test_pdf_ocr_writes_searchable_pdf_pages(monkeypatch, tmp_path: Path) -> None:
    import Profiler_Suite_V15 as profiler

    source = tmp_path / "scan.pdf"
    target = tmp_path / "scan-ocr.pdf"
    source.write_bytes(b"original")

    page_bytes = io.BytesIO()
    writer = profiler.PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(page_bytes)

    monkeypatch.setattr(profiler, "HAS_OCR", True)
    monkeypatch.setattr(profiler, "HAS_PDF", True)
    monkeypatch.setattr(profiler, "HAS_PDF2IMAGE", True)
    monkeypatch.setattr(profiler, "convert_from_path", lambda _path: [object(), object()])
    monkeypatch.setattr(
        profiler.pytesseract,
        "image_to_pdf_or_hocr",
        lambda _image, extension, lang: page_bytes.getvalue(),
    )

    assert profiler.PDFUtils.apply_ocr_to_pdf(str(source), str(target), "deu") is True
    assert target.read_bytes() != source.read_bytes()
    assert len(profiler.PdfReader(str(target)).pages) == 2


def _write_zip(path: Path, entries: dict[str, bytes | str]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)


@pytest.mark.parametrize("unsafe_name", ["../escape.txt", "/absolute.txt", "C:/drive.txt", "dir\\..\\escape.txt"])
def test_module_installer_rejects_zip_traversal(tmp_path: Path, unsafe_name: str) -> None:
    from github_installer import InstallSafetyError, extract_zip_to_sibling

    archive = tmp_path / "unsafe.zip"
    _write_zip(archive, {unsafe_name: "bad"})
    with pytest.raises(InstallSafetyError):
        extract_zip_to_sibling(archive, tmp_path / "target")
    assert not (tmp_path / "escape.txt").exists()


def test_module_installer_refuses_existing_target(tmp_path: Path) -> None:
    from github_installer import InstallSafetyError, extract_zip_to_sibling

    archive = tmp_path / "safe.zip"
    _write_zip(archive, {"repo-v1/main.py": "# safe"})
    target = tmp_path / "target"
    target.mkdir()
    (target / "keep.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(InstallSafetyError):
        extract_zip_to_sibling(archive, target)
    assert (target / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_module_installer_requires_verified_sha256(monkeypatch, tmp_path: Path) -> None:
    from github_installer import install_module

    release = {
        "tag_name": "v1.2.3",
        "name": "Release",
        "zipball_url": "https://api.github.com/repos/file-bricks/ProSync/zipball/v1.2.3",
        "assets": [],
    }
    monkeypatch.setattr("github_installer.fetch_latest_release", lambda *_args, **_kwargs: release)
    with mock.patch("github_installer.download_file") as download:
        result = install_module("prosync", parent_dir=tmp_path)

    assert not result.success
    assert "SHA-256" in (result.error or result.message)
    download.assert_not_called()
