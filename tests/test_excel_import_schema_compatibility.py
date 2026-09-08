"""Regression tests for database schema compatibility in import_excel_to_profiler."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from import_excel_to_profiler import ProfilerAutismoImporter

DDL_BASE_TEST = """
CREATE TABLE IF NOT EXISTS files(
    id INTEGER PRIMARY KEY, 
    content_hash TEXT UNIQUE, 
    size INTEGER, 
    mime TEXT, 
    first_seen TEXT
);
CREATE TABLE IF NOT EXISTS versions(
    id INTEGER PRIMARY KEY, 
    file_id INTEGER, 
    name TEXT, 
    path TEXT, 
    mtime TEXT, 
    ctime TEXT, 
    version_index INTEGER, 
    source_side TEXT
);
CREATE TABLE IF NOT EXISTS collections(
    id INTEGER PRIMARY KEY, 
    name TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS collection_items(
    collection_id INTEGER, 
    version_id INTEGER, 
    PRIMARY KEY(collection_id, version_id)
);
CREATE TABLE IF NOT EXISTS tags(
    id INTEGER PRIMARY KEY, 
    file_id INTEGER, 
    tag TEXT
);
"""

DDL_MINIMAL_NO_COLLECTIONS = """
CREATE TABLE IF NOT EXISTS files(
    id INTEGER PRIMARY KEY, 
    content_hash TEXT UNIQUE, 
    size INTEGER, 
    mime TEXT, 
    first_seen TEXT
);
CREATE TABLE IF NOT EXISTS versions(
    id INTEGER PRIMARY KEY, 
    file_id INTEGER, 
    name TEXT, 
    path TEXT, 
    mtime TEXT, 
    ctime TEXT, 
    version_index INTEGER, 
    source_folder TEXT
);
CREATE TABLE IF NOT EXISTS tags(
    id INTEGER PRIMARY KEY, 
    file_id INTEGER, 
    tag TEXT
);
"""

DDL_V9_FULL = """
CREATE TABLE IF NOT EXISTS files(
    id INTEGER PRIMARY KEY, 
    content_hash TEXT UNIQUE, 
    size INTEGER, 
    mime TEXT, 
    first_seen TEXT,
    pdf_encrypted INTEGER DEFAULT 0,
    pdf_has_text INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS versions(
    id INTEGER PRIMARY KEY, 
    file_id INTEGER, 
    name TEXT, 
    path TEXT, 
    mtime TEXT, 
    ctime TEXT, 
    version_index INTEGER, 
    source_side TEXT,
    is_deleted INTEGER DEFAULT 0,
    display_name TEXT
);
CREATE TABLE IF NOT EXISTS collections(
    id INTEGER PRIMARY KEY, 
    name TEXT UNIQUE,
    description TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS collection_items(
    collection_id INTEGER, 
    version_id INTEGER, 
    added_at TEXT,
    PRIMARY KEY(collection_id, version_id)
);
CREATE TABLE IF NOT EXISTS tags(
    id INTEGER PRIMARY KEY, 
    file_id INTEGER, 
    tag TEXT
);
"""


class TestExcelImportSchemaCompatibility(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)
        self.out_dir = self.root / "imported_docs"

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_base_schema_compatibility(self):
        db_path = self.root / "base_schema.db"
        conn = sqlite3.connect(db_path)
        conn.executescript(DDL_BASE_TEST)
        conn.close()

        sample_file = self.root / "doc.txt"
        sample_file.write_text("Test content", encoding="utf-8")

        with ProfilerAutismoImporter(db_path, self.out_dir) as importer:
            importer.prepare_output_folder()
            cid = importer.get_or_create_collection("TestCategory")
            self.assertIsNotNone(cid)
            self.assertGreater(cid, 0)

            cid2 = importer.get_or_create_collection("TestCategory")
            self.assertEqual(cid, cid2)

            importer.register_in_db(sample_file, cid, ["tag1", "tag2"], "Sample Display")

        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, content_hash FROM files")
            file_rows = cursor.fetchall()
            self.assertEqual(len(file_rows), 1)

            cursor.execute("SELECT id, file_id, name, path, source_side FROM versions")
            version_rows = cursor.fetchall()
            self.assertEqual(len(version_rows), 1)
            self.assertEqual(version_rows[0][2], "doc.txt")
            self.assertEqual(version_rows[0][4], "source")

            cursor.execute("SELECT collection_id, version_id FROM collection_items")
            ci_rows = cursor.fetchall()
            self.assertEqual(len(ci_rows), 1)
            self.assertEqual(ci_rows[0][0], cid)
            self.assertEqual(ci_rows[0][1], version_rows[0][0])

            cursor.execute("SELECT tag FROM tags WHERE file_id = ?", (file_rows[0][0],))
            tags = {r[0] for r in cursor.fetchall()}
            self.assertEqual(tags, {"tag1", "tag2"})
        finally:
            conn.close()

    def test_minimal_schema_without_collections(self):
        db_path = self.root / "minimal_schema.db"
        conn = sqlite3.connect(db_path)
        conn.executescript(DDL_MINIMAL_NO_COLLECTIONS)
        conn.close()

        sample_file = self.root / "doc2.txt"
        sample_file.write_text("More test content", encoding="utf-8")

        with ProfilerAutismoImporter(db_path, self.out_dir) as importer:
            importer.prepare_output_folder()
            cid = importer.get_or_create_collection("TestCategory")
            self.assertIsNone(cid)

            importer.register_in_db(sample_file, cid, ["quick"], "Sample 2")

        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM files")
            self.assertEqual(len(cursor.fetchall()), 1)

            cursor.execute("SELECT id, name, source_folder FROM versions")
            vrows = cursor.fetchall()
            self.assertEqual(len(vrows), 1)
            self.assertEqual(vrows[0][1], "doc2.txt")
            self.assertEqual(vrows[0][2], "source")
        finally:
            conn.close()

    def test_v9_full_schema_roundtrip(self):
        db_path = self.root / "v9_schema.db"
        conn = sqlite3.connect(db_path)
        conn.executescript(DDL_V9_FULL)
        conn.close()

        sample_file = self.root / "doc_v9.txt"
        sample_file.write_text("V9 content", encoding="utf-8")

        with ProfilerAutismoImporter(db_path, self.out_dir) as importer:
            importer.prepare_output_folder()
            cid = importer.get_or_create_collection("FullCategory")
            self.assertIsNotNone(cid)

            importer.register_in_db(sample_file, cid, ["v9_tag"], "Full Display Name")

        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT description, created_at FROM collections WHERE id = ?", (cid,))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "Importiert aus Excel")
            self.assertTrue(bool(row[1]))

            cursor.execute("SELECT display_name, is_deleted FROM versions")
            vrow = cursor.fetchone()
            self.assertEqual(vrow[0], "Full Display Name")
            self.assertEqual(vrow[1], 0)

            cursor.execute("SELECT added_at FROM collection_items WHERE collection_id = ?", (cid,))
            ci_row = cursor.fetchone()
            self.assertTrue(bool(ci_row[0]))
        finally:
            conn.close()

    def test_cleanup_previous_import_without_collection_items(self):
        db_path = self.root / "cleanup_schema.db"
        conn = sqlite3.connect(db_path)
        conn.executescript(DDL_MINIMAL_NO_COLLECTIONS)
        conn.close()

        with ProfilerAutismoImporter(db_path, self.out_dir) as importer:
            importer.prepare_output_folder()
            imported_file = self.out_dir / "managed_doc.txt"
            imported_file.write_text("inside managed output", encoding="utf-8")
            importer.register_in_db(imported_file, None, ["cleanup_tag"], "Managed Doc")

            # Cleanup should succeed even though collection_items table does not exist
            result = importer.cleanup_previous_import()
            self.assertEqual(result["versions_deleted"], 1)

        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM versions")
            self.assertEqual(cursor.fetchone()[0], 0)
            cursor.execute("SELECT COUNT(*) FROM files")
            self.assertEqual(cursor.fetchone()[0], 0)
        finally:
            conn.close()
