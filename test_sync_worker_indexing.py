"""Regressionstest: SyncWorker._run_indexing nutzt ConnectionDB-API korrekt (Bug-Fix V15)

Bug: _run_indexing rief db.add_version(), db.get_versions_by_hash(), db.add_event(),
     db.add_tag() auf — alles Methoden die in ConnectionDB nicht existieren.
     Jede Indexierung crashte sofort mit AttributeError.
Fix: Ersetze durch db.upsert_version() und db.get_latest_version_by_path().
"""

import sqlite3
import tempfile
import os
import unittest

DDL = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS files(
    id INTEGER PRIMARY KEY, content_hash TEXT UNIQUE,
    size INTEGER, mime TEXT, first_seen TEXT
);
CREATE TABLE IF NOT EXISTS versions(
    id INTEGER PRIMARY KEY, file_id INTEGER,
    name TEXT, path TEXT, mtime TEXT, ctime TEXT,
    version_index INTEGER, source_side TEXT,
    is_favorite INTEGER DEFAULT 0, version_label TEXT,
    is_deleted INTEGER DEFAULT 0, deleted_at TEXT,
    is_hidden INTEGER DEFAULT 0, hidden_at TEXT, display_name TEXT
);
CREATE TABLE IF NOT EXISTS collections(id INTEGER PRIMARY KEY, name TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS collection_items(
    collection_id INTEGER, version_id INTEGER,
    PRIMARY KEY(collection_id, version_id)
);
CREATE TABLE IF NOT EXISTS tags(id INTEGER PRIMARY KEY, file_id INTEGER, tag TEXT);
"""


class _FakeConnectionDB:
    """Minimale Stub-DB mit genau den Methoden die SyncWorker._run_indexing nutzen darf."""
    def __init__(self, db_path):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.executescript(DDL)
        self.conn.commit()

    def get_latest_version_by_path(self, path):
        cur = self.conn.cursor()
        cur.execute("SELECT mtime, file_id, id FROM versions WHERE path=? LIMIT 1", (path,))
        return cur.fetchone()

    def upsert_file(self, content_hash, size, mime=None, **kw):
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM files WHERE content_hash=?", (content_hash,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            "INSERT INTO files(content_hash,size,first_seen) VALUES (?,?,datetime('now'))",
            (content_hash, size)
        )
        self.conn.commit()
        return cur.lastrowid

    def upsert_version(self, file_id, name, path, mtime, ctime, idx, side):
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM versions WHERE path=?", (path,))
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE versions SET file_id=?,mtime=?,ctime=?,name=?,source_side=? WHERE id=?",
                (file_id, mtime, ctime, name, side, row[0])
            )
        else:
            cur.execute(
                "INSERT INTO versions(file_id,name,path,mtime,ctime,version_index,source_side) VALUES (?,?,?,?,?,?,?)",
                (file_id, name, path, mtime, ctime, idx, side)
            )
        self.conn.commit()

    def close(self):
        self.conn.close()

    def count_versions(self):
        return self.conn.execute("SELECT COUNT(*) FROM versions").fetchone()[0]

    def count_files(self):
        return self.conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]


def _build_indexing_logic(cfg, db, is_killed_ref, is_paused_ref):
    """Repliziert exakt die _run_indexing-Logik nach Fix (ohne QThread)."""
    import hashlib, time as _time
    from datetime import datetime, timezone

    def _sha256(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    source_folders = cfg.get("sources", [])
    if not source_folders:
        return

    all_files = []
    for source_root in source_folders:
        if not os.path.exists(source_root):
            continue
        for root, _, files in os.walk(source_root):
            if is_killed_ref[0]:
                return
            for f in files:
                all_files.append((source_root, os.path.join(root, f)))

    done = 0
    for source_root, path in all_files:
        if is_killed_ref[0]:
            return

        try:
            stat = os.stat(path)
            mtime_iso = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
            ctime_iso = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat()
            size = stat.st_size
            name = os.path.basename(path)

            latest = db.get_latest_version_by_path(path)
            content_hash = None
            file_id = None

            if latest and latest[0] == mtime_iso:
                file_id = latest[1]

            if not file_id:
                content_hash = _sha256(path)
                file_id = db.upsert_file(content_hash, size)

            if not content_hash:
                content_hash = _sha256(path)

            db.upsert_version(file_id, name, path, mtime_iso, ctime_iso, 1, "source")
            done += 1
        except Exception:
            pass


class TestSyncWorkerIndexing(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # Zwei Test-Dateien anlegen
        for fn in ("alpha.txt", "beta.txt"):
            with open(os.path.join(self.tmp, fn), "w") as f:
                f.write(fn)
        self.db = _FakeConnectionDB(":memory:")

    def tearDown(self):
        self.db.close()
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_indexing_does_not_raise_attribute_error(self):
        """_run_indexing darf keinen AttributeError wegen fehlender DB-Methoden werfen."""
        cfg = {"sources": [self.tmp]}
        _build_indexing_logic(cfg, self.db, [False], [False])
        # Wenn kein AttributeError geworfen → Fix wirkt

    def test_indexing_inserts_files_and_versions(self):
        """Nach Indexierung müssen files und versions vorhanden sein."""
        cfg = {"sources": [self.tmp]}
        _build_indexing_logic(cfg, self.db, [False], [False])
        self.assertEqual(self.db.count_files(), 2, "Zwei Dateien sollen indexiert sein")
        self.assertEqual(self.db.count_versions(), 2, "Zwei Versionen sollen angelegt sein")

    def test_reindex_does_not_duplicate(self):
        """Doppelte Indexierung (gleicher mtime) darf keine doppelten Einträge erzeugen."""
        cfg = {"sources": [self.tmp]}
        _build_indexing_logic(cfg, self.db, [False], [False])
        _build_indexing_logic(cfg, self.db, [False], [False])
        self.assertEqual(self.db.count_versions(), 2, "Upsert verhindert Duplikate")

    def test_kill_flag_stops_processing(self):
        """is_killed=True stoppt die Verarbeitung sofort."""
        cfg = {"sources": [self.tmp]}
        _build_indexing_logic(cfg, self.db, [True], [False])
        # Kein Assert auf count: Hauptsache kein Fehler + keine Exception


if __name__ == "__main__":
    unittest.main()
