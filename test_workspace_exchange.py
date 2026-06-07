"""Tests for the redacted ProFiler workspace exchange."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from workspace_exchange import SCHEMA_NAME, build_workspace_export, import_workspace


class FakeSearchManager:
    def __init__(self, dbs):
        self.dbs = list(dbs)


class FakeSettingsManager:
    def __init__(self, data=None):
        self.data = dict(data or {})

    def set(self, key, value):
        self.data[key] = value


class FakeConnectionManager:
    def __init__(self, connections):
        self._connections = list(connections)

    def list_connections(self):
        return list(self._connections)


class WorkspaceExchangeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.db_path = self.root / "demo.db"
        self.export_path = self.root / "profiler-workspace-v1.json"
        self.preview_path = self.root / "imported-workspace.json"

        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(
                """
                CREATE TABLE files (
                    id INTEGER PRIMARY KEY,
                    content_hash TEXT,
                    size INTEGER
                );
                CREATE TABLE versions (
                    id INTEGER PRIMARY KEY,
                    file_id INTEGER,
                    name TEXT,
                    path TEXT,
                    is_deleted INTEGER DEFAULT 0,
                    is_hidden INTEGER DEFAULT 0
                );
                """
            )
            conn.execute(
                "INSERT INTO files(id, content_hash, size) VALUES (1, 'hash-a', 12), (2, 'hash-b', 24)"
            )
            conn.execute(
                "INSERT INTO versions(file_id, name, path, is_deleted, is_hidden) VALUES (?, ?, ?, 0, 0)",
                (1, "Bericht.pdf", r"C:\Users\User\Dokumente\Bericht.pdf"),
            )
            conn.execute(
                "INSERT INTO versions(file_id, name, path, is_deleted, is_hidden) VALUES (?, ?, ?, 0, 0)",
                (2, "Notiz.txt", r"C:\Users\User\Dokumente\Notiz.txt"),
            )
            conn.commit()
        finally:
            conn.close()

        self.search = FakeSearchManager([str(self.db_path)])
        self.settings = FakeSettingsManager(
            {
                "delete_mode": "soft",
                "ocr_enabled": True,
                "ocr_language": "deu",
                "prosync_path": r"C:\Users\User\Tools\ProSync.exe",
                "pdf_master_password_open": "secret-open",
                "pdf_master_password_save": "secret-save",
                "theme": "dark",
            }
        )
        self.connections = FakeConnectionManager(
            [
                {
                    "id": "local-docs",
                    "name": "Dokumente",
                    "enabled": True,
                    "sources": [r"C:\Users\User\Dokumente"],
                    "db_path": str(self.db_path),
                }
            ]
        )
        self.privacy_config = {
            "blacklist": ["geheim", "iban"],
            "whitelist": ["muster"],
            "clipboard_lock": True,
            "whole_words": True,
            "case_sensitive": False,
        }

    def test_build_workspace_export_redacts_paths_and_secrets(self):
        payload = build_workspace_export(
            self.search,
            self.settings,
            self.connections,
            exported_at=datetime(2026, 6, 3, 12, 0, tzinfo=timezone.utc),
            privacy_config=self.privacy_config,
        )

        dump = json.dumps(payload, ensure_ascii=False)

        self.assertEqual(payload["schema"], SCHEMA_NAME)
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["indexes"][0]["file_count"], 2)
        self.assertEqual(payload["indexes"][0]["formats"], ["pdf", "txt"])
        self.assertEqual(payload["indexes"][0]["redacted_root"], "[source-root-1]/Dokumente")
        self.assertEqual(payload["privacy_summary"]["blacklist_terms_count"], 2)
        self.assertTrue(payload["tool_links"]["prosync"]["configured"])
        self.assertNotIn(r"C:\Users\User", dump)
        self.assertNotIn("secret-open", dump)
        self.assertNotIn("secret-save", dump)

    def test_import_workspace_applies_safe_settings_and_writes_preview(self):
        payload = build_workspace_export(
            self.search,
            self.settings,
            self.connections,
            privacy_config=self.privacy_config,
        )
        self.export_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        target_settings = FakeSettingsManager({"prosync_path": r"C:\secret\keep-me.exe"})
        result = import_workspace(
            str(self.export_path),
            target_settings,
            preview_path=str(self.preview_path),
            imported_at=datetime(2026, 6, 3, 13, 0, tzinfo=timezone.utc),
        )

        raw = self.preview_path.read_bytes()
        preview = json.loads(raw.decode("utf-8"))

        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(result["workspace_name"], payload["workspace"]["name"])
        self.assertIn("ocr_language", result["applied_settings"])
        self.assertEqual(target_settings.data["ocr_language"], "deu")
        self.assertEqual(target_settings.data["theme"], "dark")
        self.assertEqual(target_settings.data["prosync_path"], r"C:\secret\keep-me.exe")
        self.assertEqual(preview["workspace"]["schema"], SCHEMA_NAME)


if __name__ == "__main__":
    unittest.main(verbosity=2)
