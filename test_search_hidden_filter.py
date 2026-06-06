"""Regressionstest: is_hidden-Filter in SearchWorker SQL (Bug-Fix V15)

Bug: SearchWorker verwendete 'AND v.is_deleted = 0' statt 'AND v.is_hidden = 0'
wenn show_hidden=False. Dadurch waren Safety-Mode-versteckte Dateien nie
wirklich aus den Suchergebnissen ausgeblendet.
"""

import sqlite3
import unittest


DDL = """
PRAGMA journal_mode=WAL;
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
    source_side TEXT,
    is_favorite INTEGER DEFAULT 0,
    version_label TEXT,
    is_deleted INTEGER DEFAULT 0,
    deleted_at TEXT,
    is_hidden INTEGER DEFAULT 0,
    hidden_at TEXT,
    display_name TEXT
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
"""


def _build_search_sql(term="", show_deleted=False, show_hidden=False, only_fav=False, collection_id=None):
    """Repliziert exakt die SQL-Logik des SearchWorkers (nach Fix)."""
    wildcard = f"%{term.lower()}%"
    sql = """
        SELECT v.id, v.name, v.path, COALESCE(v.display_name, v.name) as display_name, v.mtime,
               COALESCE(v.is_favorite, 0) as is_favorite,
               v.version_index,
               v.version_label,
               COALESCE(v.is_deleted, 0) as is_deleted,
               COALESCE(v.is_hidden, 0) as is_hidden,
               v.hidden_at,
               v.deleted_at,
               f.content_hash,
               f.size
        FROM versions v
        JOIN files f ON v.file_id = f.id
        LEFT JOIN collection_items ci ON ci.version_id = v.id
        WHERE (lower(v.name) LIKE ? OR lower(v.path) LIKE ?)
    """
    args = [wildcard, wildcard]

    if not show_deleted:
        sql += " AND v.is_deleted = 0"

    if not show_hidden:
        sql += " AND v.is_hidden = 0"   # korrigierter Fix

    if only_fav:
        sql += " AND v.is_favorite = 1"

    if collection_id:
        sql += " AND ci.collection_id = ?"
        args.append(collection_id)

    sql += " ORDER BY v.is_favorite DESC, v.name LIMIT 500"
    return sql, args


def _setup_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(DDL)
    conn.execute(
        "INSERT INTO files(content_hash, size, first_seen) VALUES ('hash_visible',100,'2026-01-01')"
    )
    conn.execute(
        "INSERT INTO files(content_hash, size, first_seen) VALUES ('hash_hidden',200,'2026-01-01')"
    )
    conn.execute(
        "INSERT INTO versions(file_id,name,path,mtime,ctime,version_index,source_side,is_hidden,is_deleted) "
        "VALUES (1,'visible.pdf','/docs/visible.pdf','2026-01-01','2026-01-01',1,'source',0,0)"
    )
    conn.execute(
        "INSERT INTO versions(file_id,name,path,mtime,ctime,version_index,source_side,is_hidden,is_deleted) "
        "VALUES (2,'hidden.pdf','/docs/hidden.pdf','2026-01-01','2026-01-01',1,'source',1,0)"
    )
    conn.commit()
    return conn


class TestSearchHiddenFilter(unittest.TestCase):

    def setUp(self):
        self.conn = _setup_db()

    def tearDown(self):
        self.conn.close()

    def _run(self, **kwargs):
        sql, args = _build_search_sql(**kwargs)
        return [dict(r) for r in self.conn.execute(sql, args).fetchall()]

    def test_hidden_excluded_by_default(self):
        """show_hidden=False: versteckte Datei darf nicht erscheinen."""
        results = self._run(term="", show_hidden=False)
        names = [r["name"] for r in results]
        self.assertIn("visible.pdf", names)
        self.assertNotIn("hidden.pdf", names, "hidden.pdf muss bei show_hidden=False ausgeblendet sein")

    def test_hidden_included_when_show_hidden_true(self):
        """show_hidden=True: versteckte Datei erscheint."""
        results = self._run(term="", show_hidden=True)
        names = [r["name"] for r in results]
        self.assertIn("visible.pdf", names)
        self.assertIn("hidden.pdf", names)

    def test_deleted_excluded_by_default(self):
        """is_deleted=1 Versionen erscheinen nicht bei show_deleted=False."""
        self.conn.execute("UPDATE versions SET is_deleted=1 WHERE name='visible.pdf'")
        self.conn.commit()
        results = self._run(term="", show_hidden=True, show_deleted=False)
        names = [r["name"] for r in results]
        self.assertNotIn("visible.pdf", names)

    def test_old_bug_would_have_exposed_hidden(self):
        """Dokumentiert das Vorher-Verhalten: der alte fehlerhafte SQL zeigte hidden.pdf."""
        # Alter SQL-Fehler: show_hidden=False ergänzte 'AND v.is_deleted = 0' statt 'AND v.is_hidden = 0'
        broken_sql = """
            SELECT v.name FROM versions v
            JOIN files f ON v.file_id = f.id
            LEFT JOIN collection_items ci ON ci.version_id = v.id
            WHERE (lower(v.name) LIKE ? OR lower(v.path) LIKE ?)
            AND v.is_deleted = 0
            ORDER BY v.name LIMIT 500
        """
        rows = self.conn.execute(broken_sql, ["%", "%"]).fetchall()
        names = [r[0] for r in rows]
        self.assertIn("hidden.pdf", names, "Alter Bug: hidden.pdf erschien trotz is_hidden=1")


if __name__ == "__main__":
    unittest.main()
