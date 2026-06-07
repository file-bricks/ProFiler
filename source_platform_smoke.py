"""
Source-Platform-Smoke für ProFiler Suite V15.
Läuft auf Linux/macOS (offscreen) und Windows ohne Anzeige.
6 Checks: stdlib, PySide6, workspace_exchange, SQLite, Umlaut, headless Window.
"""
import sys
import os
import tempfile
import sqlite3
import json
from pathlib import Path
from unittest import mock

CHECKS_TOTAL = 6
passed = 0


def ok(label: str) -> None:
    global passed
    passed += 1
    print(f"  OK  {label}")


def fail(label: str, exc: Exception) -> None:
    print(f"FAIL  {label}: {exc}", file=sys.stderr)


# ── 1. Stdlib ─────────────────────────────────────────────────────────────────
try:
    import pathlib, json, sqlite3 as _sqlite3
    ok("stdlib (pathlib, json, sqlite3)")
except Exception as e:
    fail("stdlib", e)

# ── 2. PySide6 vorhanden ──────────────────────────────────────────────────────
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication
    ok("PySide6 importierbar")
except Exception as e:
    fail("PySide6", e)
    print("Abbruch: PySide6 fehlt.", file=sys.stderr)
    sys.exit(1)

# ── 3. workspace_exchange importieren + Schema prüfen ─────────────────────────
try:
    import workspace_exchange
    assert workspace_exchange.SCHEMA_NAME == "profiler-workspace-v1", \
        f"SCHEMA_NAME falsch: {workspace_exchange.SCHEMA_NAME!r}"
    ok("workspace_exchange (SCHEMA_NAME korrekt)")
except Exception as e:
    fail("workspace_exchange", e)

# ── 4. SQLite CRUD ────────────────────────────────────────────────────────────
try:
    with tempfile.TemporaryDirectory() as tmpd:
        db_path = Path(tmpd) / "smoke.db"
        con = sqlite3.connect(str(db_path))
        con.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
        con.execute("INSERT INTO t VALUES (1, 'hello')")
        con.commit()
        row = con.execute("SELECT val FROM t WHERE id=1").fetchone()
        assert row and row[0] == "hello", f"Unexpected row: {row}"
        con.close()
    ok("SQLite CRUD")
except Exception as e:
    fail("SQLite CRUD", e)

# ── 5. Umlaut-Roundtrip (JSON UTF-8) ─────────────────────────────────────────
try:
    with tempfile.TemporaryDirectory() as tmpd:
        p = Path(tmpd) / "umlaute.json"
        data = {"text": "Ärger mit Öl und Übungen – schön, grüß Gott!"}
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        back = json.loads(p.read_text(encoding="utf-8"))
        assert back["text"] == data["text"], f"Roundtrip-Fehler: {back['text']!r}"
    ok("Umlaut-Roundtrip (JSON UTF-8)")
except Exception as e:
    fail("Umlaut-Roundtrip", e)

# ── 6. Headless UnifiedMainWindow ─────────────────────────────────────────────
try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    import Profiler_Suite_V15 as profiler

    app = QApplication.instance() or QApplication(sys.argv[:1])

    with tempfile.TemporaryDirectory() as tmpd:
        tmp = Path(tmpd)
        with mock.patch.object(profiler, "_CONFIG_DIR", tmp), \
             mock.patch.object(profiler, "SEARCH_CONFIG_PATH", str(tmp / "search.json")), \
             mock.patch.object(profiler, "SYNC_CONFIG_PATH", str(tmp / "profiler.json")), \
             mock.patch.object(profiler, "SETTINGS_PATH", str(tmp / "settings.json")):
            win = profiler.UnifiedMainWindow()
            assert win.isVisible() is False
            win.close()

    ok("headless UnifiedMainWindow (offscreen)")
except Exception as e:
    fail("headless UnifiedMainWindow", e)

# ── Ergebnis ──────────────────────────────────────────────────────────────────
print(f"\n{passed}/{CHECKS_TOTAL} Checks bestanden.")
if passed < CHECKS_TOTAL:
    sys.exit(1)
