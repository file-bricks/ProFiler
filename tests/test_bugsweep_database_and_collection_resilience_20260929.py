import os
import sqlite3
import tempfile
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from Profiler_Suite_V15 import (
    ConnectionDB,
    SearchWorker,
    DuplicateWorker,
    PDFUtils,
    get_file_category,
    DDL_BASE,
)


class TestBugsweepRegressions20260929:
    """Hermetic regression tests for bugs identified during 2026-09-29 Bugsweep."""

    def test_repro_database_has_display_name_column(self, tmp_path):
        """Bug 1: Fresh ConnectionDB should provide display_name column in versions."""
        db_path = str(tmp_path / "test_fresh.db")
        db = ConnectionDB(db_path)
        try:
            cur = db.conn.cursor()
            cur.execute("PRAGMA table_info(versions)")
            cols = {row[1] for row in cur.fetchall()}
            assert "display_name" in cols, "display_name column missing in versions table after ConnectionDB init"

            # Query should succeed without error
            cur.execute("SELECT v.id, v.name, v.path, COALESCE(v.display_name, v.name) as display_name FROM versions v")
            assert True
        finally:
            db.close()

    def test_repro_search_worker_on_database_without_display_name(self, tmp_path):
        """Bug 2a: SearchWorker must succeed even on an old database without display_name."""
        db_path = str(tmp_path / "test_legacy_search.db")
        conn = sqlite3.connect(db_path)
        # Create legacy schema explicitly WITHOUT display_name
        conn.executescript("""
            CREATE TABLE files(id INTEGER PRIMARY KEY, content_hash TEXT UNIQUE, size INTEGER, mime TEXT, first_seen TEXT);
            CREATE TABLE versions(id INTEGER PRIMARY KEY, file_id INTEGER, name TEXT, path TEXT, mtime TEXT, ctime TEXT, version_index INTEGER, source_side TEXT, is_deleted INTEGER DEFAULT 0, is_hidden INTEGER DEFAULT 0);
            INSERT INTO files(id, content_hash, size) VALUES (1, 'hash1', 1234);
            INSERT INTO versions(id, file_id, name, path, mtime, is_deleted, is_hidden) VALUES (1, 1, 'report.pdf', '/data/report.pdf', '2026-09-29T00:00:00Z', 0, 0);
        """)
        conn.commit()
        conn.close()

        manager = MagicMock()
        manager.dbs = [db_path]
        settings = MagicMock()
        worker = SearchWorker(manager, {"term": "report"}, settings)

        results_collector = []
        worker.results_found.connect(results_collector.extend)
        worker.run()

        assert len(results_collector) == 1, "SearchWorker failed to return results on legacy database without display_name"
        assert results_collector[0]["name"] == "report.pdf"

    def test_repro_duplicate_worker_on_database_without_display_name(self, tmp_path):
        """Bug 2b: DuplicateWorker must succeed even on an old database without display_name."""
        db_path = str(tmp_path / "test_legacy_dup.db")
        conn = sqlite3.connect(db_path)
        # Create legacy schema explicitly WITHOUT display_name
        conn.executescript("""
            CREATE TABLE files(id INTEGER PRIMARY KEY, content_hash TEXT UNIQUE, size INTEGER, mime TEXT, first_seen TEXT);
            CREATE TABLE versions(id INTEGER PRIMARY KEY, file_id INTEGER, name TEXT, path TEXT, mtime TEXT, ctime TEXT, version_index INTEGER, source_side TEXT, is_deleted INTEGER DEFAULT 0, is_hidden INTEGER DEFAULT 0);
            INSERT INTO files(id, content_hash, size) VALUES (1, 'hash_dup', 1234);
            INSERT INTO versions(id, file_id, name, path, mtime, is_deleted) VALUES (1, 1, 'copy1.pdf', '/data/copy1.pdf', '2026-09-29T00:00:00Z', 0);
            INSERT INTO versions(id, file_id, name, path, mtime, is_deleted) VALUES (2, 1, 'copy2.pdf', '/data/copy2.pdf', '2026-09-29T00:00:00Z', 0);
        """)
        conn.commit()
        conn.close()

        worker = DuplicateWorker([db_path], "hash")
        results_collector = {}
        worker.results_ready.connect(results_collector.update)
        worker.run()

        assert "hash_dup" in results_collector, "DuplicateWorker failed on legacy database without display_name"
        assert len(results_collector["hash_dup"]) == 2

    def test_repro_collection_export_query_uses_collection_items_not_file_tags(self, tmp_path):
        """Bug 3: Collection files query must query collection_items and not non-existent file_tags."""
        db_path = str(tmp_path / "test_coll.db")
        db = ConnectionDB(db_path)
        try:
            db.add_collection("MyCollection", "Test Desc")
            collections = db.get_collections()
            coll_id = collections[0][0]

            fid = db.upsert_file("hash_coll", 4321)
            vid = db.upsert_version(fid, "doc.pdf", str(tmp_path / "doc.pdf"), "2026-09-29T00:00:00Z", "2026-09-29T00:00:00Z", 1, "source")
            db.add_to_collection(coll_id, vid)

            # The buggy query used in export_collection_list before fix was:
            buggy_query = """
                SELECT v.path, v.name, v.mtime, f.size, f.category
                FROM file_tags ft
                JOIN versions v ON ft.version_id = v.id
                JOIN files f ON v.file_id = f.id
                WHERE ft.collection_id = ? AND v.is_deleted = 0
                ORDER BY v.path
            """
            with pytest.raises(sqlite3.OperationalError):
                db.conn.execute(buggy_query, (coll_id,)).fetchall()

            # The correct resilient query
            fixed_query = """
                SELECT v.path, v.name, v.mtime, f.size
                FROM collection_items ci
                JOIN versions v ON ci.version_id = v.id
                JOIN files f ON v.file_id = f.id
                WHERE ci.collection_id = ? AND v.is_deleted = 0
                ORDER BY v.path
            """
            rows = db.conn.execute(fixed_query, (coll_id,)).fetchall()
            assert len(rows) == 1
            assert rows[0][1] == "doc.pdf"
            cat = get_file_category(rows[0][1])
            assert cat == "Dokumente"
        finally:
            db.close()

    def test_repro_pdf_utils_extract_pages_creates_parent_dir(self, tmp_path):
        """Bug 4: extract_pages creates output directory if it doesn't exist."""
        # Create minimal dummy PDF
        pypdf = pytest.importorskip("pypdf")
        from pypdf import PdfWriter
        
        src_pdf = tmp_path / "source.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        with open(src_pdf, "wb") as f:
            writer.write(f)

        nested_out = tmp_path / "nested" / "sub" / "out.pdf"
        assert not nested_out.parent.exists()
        
        # Test extract_pages handles non-existent parent directory
        PDFUtils.extract_pages(str(src_pdf), str(nested_out), [0])
        assert nested_out.exists()

    def test_repro_pdf_utils_encrypt_and_decrypt_creates_parent_dir(self, tmp_path):
        """PDFUtils encrypt and decrypt create non-existent parent directories."""
        pytest.importorskip("pypdf")
        from pypdf import PdfWriter

        src_pdf = tmp_path / "source.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        with open(src_pdf, "wb") as f:
            writer.write(f)

        enc_out = tmp_path / "enc_dir" / "nested" / "encrypted.pdf"
        assert not enc_out.parent.exists()
        success = PDFUtils.encrypt_pdf(str(src_pdf), str(enc_out), "secret123")
        assert success is True
        assert enc_out.exists()

        dec_out = tmp_path / "dec_dir" / "nested" / "decrypted.pdf"
        assert not dec_out.parent.exists()
        success = PDFUtils.decrypt_pdf(str(enc_out), str(dec_out), "secret123")
        assert success is True
        assert dec_out.exists()

    def test_search_worker_propagates_display_name(self, tmp_path):
        """SearchWorker should include custom display_name in result dict."""
        db_path = str(tmp_path / "test_display_prop.db")
        db = ConnectionDB(db_path)
        try:
            fid = db.upsert_file("hash_custom", 2048)
            vid = db.upsert_version(fid, "raw_name.txt", str(tmp_path / "raw_name.txt"), "2026-09-29T00:00:00Z", "2026-09-29T00:00:00Z", 1, "source")
            db.conn.execute("UPDATE versions SET display_name=? WHERE id=?", ("Custom Display Name.txt", vid))
            db.conn.commit()

            manager = MagicMock()
            manager.dbs = [db_path]
            settings = MagicMock()
            worker = SearchWorker(manager, {"term": "raw_name"}, settings)

            results_collector = []
            worker.results_found.connect(results_collector.extend)
            worker.run()

            assert len(results_collector) == 1
            assert results_collector[0]["name"] == "raw_name.txt"
            assert results_collector[0]["display_name"] == "Custom Display Name.txt"
        finally:
            db.close()

    def test_search_worker_with_collection_id_on_legacy_db_without_table(self, tmp_path):
        """SearchWorker should gracefully skip DBs missing collection_items table when collection_id is queried."""
        db_path = str(tmp_path / "test_no_ci_table.db")
        conn = sqlite3.connect(db_path)
        conn.executescript("""
            CREATE TABLE files(id INTEGER PRIMARY KEY, content_hash TEXT UNIQUE, size INTEGER);
            CREATE TABLE versions(id INTEGER PRIMARY KEY, file_id INTEGER, name TEXT, path TEXT, mtime TEXT, is_deleted INTEGER DEFAULT 0);
            INSERT INTO files(id, content_hash, size) VALUES (1, 'hash_no_ci', 100);
            INSERT INTO versions(id, file_id, name, path, mtime, is_deleted) VALUES (1, 1, 'item.txt', '/path/item.txt', '2026-09-29T00:00:00Z', 0);
        """)
        conn.commit()
        conn.close()

        manager = MagicMock()
        manager.dbs = [db_path]
        settings = MagicMock()
        worker = SearchWorker(manager, {"term": "item", "collection_id": 999}, settings)

        results_collector = []
        worker.results_found.connect(results_collector.extend)
        worker.run()

        # Should not raise exception, but return 0 results since table doesn't exist
        assert results_collector == []

    def test_connection_db_migrate_adds_display_name_to_legacy_db(self, tmp_path):
        """ConnectionDB initialization should auto-migrate legacy databases to add display_name."""
        db_path = str(tmp_path / "test_legacy_to_migrate.db")
        conn = sqlite3.connect(db_path)
        conn.executescript("""
            CREATE TABLE files(id INTEGER PRIMARY KEY, content_hash TEXT UNIQUE, size INTEGER);
            CREATE TABLE versions(id INTEGER PRIMARY KEY, file_id INTEGER, name TEXT, path TEXT, mtime TEXT);
        """)
        conn.commit()
        conn.close()

        # Opening via ConnectionDB runs _migrate_v9()
        db = ConnectionDB(db_path)
        try:
            cur = db.conn.cursor()
            cur.execute("PRAGMA table_info(versions)")
            cols = {row[1] for row in cur.fetchall()}
            assert "display_name" in cols, "_migrate_v9 should add display_name column to legacy versions table"
        finally:
            db.close()

    def test_pdf_excerpt_dialog_html_escaping_contract(self):
        """Contract: PDFExcerptDialog must escape text before inserting into HTML preview."""
        import html
        raw_text = "<script>alert('xss')</script> & <b>bold</b>"
        escaped = html.escape(raw_text[:500])
        preview_text = f"<h3>Seite 1</h3><pre>{escaped}...</pre>"
        assert "<script>" not in preview_text
        assert "&lt;script&gt;" in preview_text

        v15_src = (Path(__file__).parent.parent / "Profiler_Suite_V15.py").read_text(encoding="utf-8")
        assert "html.escape(text[:500])" in v15_src, "PDFExcerptDialog.show_current_page must use html.escape(text[:500])"

    def test_rename_selected_does_not_contain_stray_restore_version(self):
        """Contract: rename_selected must never restore a version on rename."""
        v15_src = (Path(__file__).parent.parent / "Profiler_Suite_V15.py").read_text(encoding="utf-8")
        start = v15_src.find("def rename_selected")
        end = v15_src.find("def hard_delete_selected")
        assert start > 0 and end > start
        func_src = v15_src[start:end]
        assert "restore_version" not in func_src, "rename_selected contains stray restore_version call"

    def test_export_collection_list_uses_collection_items_not_file_tags(self):
        """Contract: export_collection_list must query collection_items and not file_tags."""
        v15_src = (Path(__file__).parent.parent / "Profiler_Suite_V15.py").read_text(encoding="utf-8")
        start = v15_src.find("def export_collection_list")
        end = v15_src.find("def show_about_dialog", start)
        if end == -1:
            end = start + 3000
        func_src = v15_src[start:end]
        assert "FROM collection_items" in func_src
        assert "file_tags" not in func_src


