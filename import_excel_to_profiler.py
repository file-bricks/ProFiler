"""Expliziter, fail-closed Excel-Import für ProFiler.

Der Importer arbeitet nur mit vom Aufrufer angegebenen Pfaden. Ein Cleanup ist
ausschließlich in einem durch diesen Importer markierten Ausgabeordner erlaubt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import pandas as pd
except ImportError:  # Optionale Importfunktion, nicht Desktop-Kernabhängigkeit.
    pd = None


OWNER_MARKER = ".profiler-import-owner.json"
OWNER_SCHEMA = "profiler-import-output-v1"
MATERIAL_KEYWORDS = (
    "regal", "schrank", "raum", "zimmer", "kasten", "fach", "schublade",
    "ablage", "ordner", "mappe", "box", "archiv", "theke", "wand", "tisch",
    "variabel", "selbst erstellt", "kostenlos", "lizenzpflichtig", "ca.",
)


class ImportSafetyError(RuntimeError):
    """Der Import wurde wegen einer nicht belegten Löschgrenze verweigert."""


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_folder(path: str | Path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if pd is not None:
        try:
            return bool(pd.isna(value))
        except (TypeError, ValueError):
            pass
    return False


def sanitize_filename(name: Any) -> str:
    if _is_missing(name):
        return "Unbenannt"
    safe = "".join(
        character
        for character in str(name)
        if character.isalnum() or character in (" ", ".", "_", "-")
    ).strip(" .")
    return (safe or "Unbenannt")[:100]


def safe_str(value: Any) -> str:
    if _is_missing(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def _single_line(value: Any) -> str:
    return " ".join(safe_str(value).replace("\r", " ").replace("\n", " ").split())


class ProfilerAutismoImporter:
    def __init__(self, db_path: str | Path, output_folder: str | Path):
        self.db_path = Path(db_path).expanduser().resolve()
        self.output_folder = Path(output_folder).expanduser().resolve()
        self._validate_root_boundary()
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def __enter__(self) -> "ProfilerAutismoImporter":
        return self

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        self.close()

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    @property
    def marker_path(self) -> Path:
        return self.output_folder / OWNER_MARKER

    def _validate_root_boundary(self) -> None:
        forbidden = {Path(self.output_folder.anchor).resolve(), Path.home().resolve()}
        if self.output_folder in forbidden:
            raise ImportSafetyError("Root- oder Benutzerverzeichnis ist kein zulässiger Importordner")
        if self.output_folder == self.db_path or self.output_folder in self.db_path.parents:
            raise ImportSafetyError("Importordner darf die Datenbank nicht enthalten")

    def _owner_payload(self) -> dict[str, str]:
        return {
            "schema": OWNER_SCHEMA,
            "output_folder": str(self.output_folder),
            "database": str(self.db_path),
        }

    def prepare_output_folder(self) -> None:
        if self.output_folder.exists():
            if self.marker_path.exists():
                self._validate_owned_output()
                return
            if any(self.output_folder.iterdir()):
                raise ImportSafetyError(
                    f"Ausgabeordner ist nicht leer und besitzt keinen Eigentumsmarker: {self.output_folder}"
                )
        self.output_folder.mkdir(parents=True, exist_ok=True)
        temporary = self.marker_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(self._owner_payload(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.marker_path)

    def _validate_owned_output(self) -> None:
        try:
            payload = json.loads(self.marker_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ImportSafetyError(f"Import-Eigentumsmarker ist unlesbar: {exc}") from exc
        if payload != self._owner_payload():
            raise ImportSafetyError("Import-Eigentumsmarker passt nicht zu Ausgabeordner und Datenbank")

    def cleanup_previous_import(self) -> dict[str, int]:
        """Entfernt nur belegte Importversionen; gemeinsame Dateiobjekte bleiben erhalten."""
        self._validate_owned_output()
        staged = self.output_folder.with_name(
            f".{self.output_folder.name}.cleanup-{uuid.uuid4().hex}"
        )
        self.output_folder.rename(staged)

        version_rows: list[tuple[int, int]] = []
        try:
            rows = self.cursor.execute("SELECT id, file_id, path FROM versions").fetchall()
            for version_id, file_id, raw_path in rows:
                try:
                    candidate = Path(raw_path).expanduser().resolve()
                    candidate.relative_to(self.output_folder)
                except (TypeError, ValueError, OSError):
                    continue
                version_rows.append((int(version_id), int(file_id)))

            self.conn.execute("BEGIN")
            version_ids = [row[0] for row in version_rows]
            file_ids = sorted({row[1] for row in version_rows})
            self.cursor.executemany(
                "DELETE FROM collection_items WHERE version_id = ?",
                [(version_id,) for version_id in version_ids],
            )
            self.cursor.executemany(
                "DELETE FROM versions WHERE id = ?",
                [(version_id,) for version_id in version_ids],
            )
            for file_id in file_ids:
                still_used = self.cursor.execute(
                    "SELECT 1 FROM versions WHERE file_id = ? LIMIT 1",
                    (file_id,),
                ).fetchone()
                if still_used:
                    continue
                self.cursor.execute("DELETE FROM tags WHERE file_id = ?", (file_id,))
                self.cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
            self.conn.commit()
        except Exception as exc:
            self.conn.rollback()
            if staged.exists() and not self.output_folder.exists():
                staged.rename(self.output_folder)
            raise ImportSafetyError(f"DB-Bereinigung abgebrochen; Dateien blieben erhalten: {exc}") from exc

        removal_error: OSError | None = None
        try:
            shutil.rmtree(staged)
        except OSError as exc:
            removal_error = exc
        self.prepare_output_folder()
        if removal_error is not None:
            raise ImportSafetyError(
                f"DB bereinigt, aber recoverable Staging-Ordner blieb erhalten: {staged}: {removal_error}"
            )
        return {"versions_deleted": len(version_rows)}

    def get_or_create_collection(self, name: Any) -> int | None:
        clean_name = safe_str(name)
        if not clean_name:
            return None
        self.cursor.execute("SELECT id FROM collections WHERE name = ?", (clean_name,))
        existing = self.cursor.fetchone()
        if existing:
            return int(existing[0])
        timestamp = datetime.now(timezone.utc).isoformat()
        self.cursor.execute(
            "INSERT INTO collections (name, description, created_at) VALUES (?, ?, ?)",
            (clean_name, "Importiert aus Excel", timestamp),
        )
        self.conn.commit()
        return int(self.cursor.lastrowid)

    def add_tags(self, file_id: int, tags_list: list[str]) -> None:
        for tag in tags_list:
            clean_tag = tag.strip()
            if clean_tag:
                self.cursor.execute(
                    "INSERT INTO tags (file_id, tag) VALUES (?, ?)",
                    (file_id, clean_tag),
                )

    def register_in_db(
        self,
        file_path: str | Path,
        category_id: int | None,
        tags_list: list[str],
        display_name: str,
    ) -> None:
        path = Path(file_path).resolve()
        if not path.is_file():
            return
        stat = path.stat()
        modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        content_hash = sha256_file(path)

        self.cursor.execute("SELECT id FROM files WHERE content_hash = ?", (content_hash,))
        existing = self.cursor.fetchone()
        if existing:
            file_id = int(existing[0])
        else:
            self.cursor.execute(
                "INSERT INTO files (content_hash, size, mime, first_seen, pdf_encrypted, pdf_has_text) "
                "VALUES (?, ?, ?, ?, 0, 1)",
                (content_hash, stat.st_size, "text/plain", modified_at),
            )
            file_id = int(self.cursor.lastrowid)

        try:
            self.cursor.execute(
                "INSERT INTO versions "
                "(file_id, name, path, mtime, ctime, version_index, source_side, is_deleted, display_name) "
                "VALUES (?, ?, ?, ?, ?, 1, 'source', 0, ?)",
                (file_id, path.name, str(path), modified_at, modified_at, display_name),
            )
        except sqlite3.OperationalError:
            self.cursor.execute(
                "INSERT INTO versions "
                "(file_id, name, path, mtime, ctime, version_index, source_side, is_deleted) "
                "VALUES (?, ?, ?, ?, ?, 1, 'source', 0)",
                (file_id, path.name, str(path), modified_at, modified_at),
            )
        version_id = int(self.cursor.lastrowid)

        if category_id:
            timestamp = datetime.now(timezone.utc).isoformat()
            self.cursor.execute(
                "INSERT OR IGNORE INTO collection_items (collection_id, version_id, added_at) "
                "VALUES (?, ?, ?)",
                (category_id, version_id, timestamp),
            )
        self.add_tags(file_id, tags_list)
        self.conn.commit()
        print(f"  -> {display_name}")

    def _output_path(self, filename: str) -> Path:
        self.prepare_output_folder()
        base = self.output_folder / filename
        if not base.exists():
            return base
        stem, suffix = base.stem, base.suffix
        for counter in range(2, 10_000):
            candidate = self.output_folder / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
        raise ImportSafetyError("Zu viele gleichnamige Importdateien")

    def _write_reference(self, filename: str, content: str) -> Path:
        path = self._output_path(filename)
        path.write_text(content, encoding="utf-8")
        return path

    def create_internet_resource(self, data: dict[str, Any]) -> Path:
        url = _single_line(data["Ort"])
        parsed = urlparse(url if "://" in url else f"https://{url}")
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Nur vollständige HTTP-/HTTPS-URLs sind zulässig")
        content = (
            "[InternetShortcut]\n"
            f"URL={parsed.geturl()}\n"
            "IconIndex=0\n\n"
            "[Metadata]\n"
            f"Bezeichnung={_single_line(data['Name'])}\n"
            f"Beschreibung={_single_line(data['Beschreibung'])}\n"
            f"Anmerkung={_single_line(data['Preis'])}\n"
            f"Kategorie={_single_line(data['Typ'])}\n"
            f"Tags={', '.join(_single_line(tag) for tag in data['Tags'])}\n"
            f"Erstellt={datetime.now().strftime('%Y-%m-%d')}\n"
            "Importiert=True\n"
        )
        return self._write_reference(f"{sanitize_filename(data['Name'])}.url", content)

    def create_material_reference(self, data: dict[str, Any]) -> Path:
        content = (
            f"Materialverweis: {data['Name']}\n"
            f"Erstellt: {datetime.now().strftime('%Y-%m-%d')}\n"
            + "=" * 80
            + f"\n\nBezeichnung: {data['Name']}\nStandort/Info: {data['Ort']}\n"
            f"Typ: {data['Typ']}\nTags: {', '.join(data['Tags'])}\n\n"
            f"Beschreibung:\n{data['Beschreibung']}\n\nPreis/Anmerkung:\n{data['Preis']}\n"
        )
        return self._write_reference(
            f"Material_{sanitize_filename(data['Name'])}.material.txt",
            content,
        )

    def create_literature_reference(self, data: dict[str, Any]) -> Path:
        content = (
            f"Literatur: {data['Name']}\nErstellt: {datetime.now().strftime('%Y-%m-%d')}\n"
            + "=" * 80
            + f"\n\nTitel: {data['Name']}\nQuelle/Ref: {data['Ort']}\nTyp: {data['Typ']}\n"
            f"Tags: {', '.join(data['Tags'])}\n\nBeschreibung/Inhalt:\n{data['Beschreibung']}\n\n"
            f"Anmerkung:\n{data['Preis']}\n"
        )
        return self._write_reference(f"Literatur_{sanitize_filename(data['Name'])}.txt", content)

    def create_generic_info(self, data: dict[str, Any]) -> Path:
        content = (
            f"Information: {data['Name']}\n" + "=" * 80
            + f"\n\nTyp: {data['Typ']}\nStatus: {data['Ort']}\n"
            f"Tags: {', '.join(data['Tags'])}\n\nBeschreibung:\n{data['Beschreibung']}\n\n"
            f"Anmerkung:\n{data['Preis']}\n"
        )
        return self._write_reference(f"Info_{sanitize_filename(data['Name'])}.txt", content)

    def run_import(self, excel_path: str | Path) -> int:
        if pd is None:
            raise RuntimeError(
                "Excel-Import benötigt optionale Pakete: pip install pandas openpyxl"
            )
        source = Path(excel_path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Excel-Datei nicht gefunden: {source}")
        self.prepare_output_folder()
        print(f"🚀 Starte Spezial-Import aus {source}...")

        workbook = pd.ExcelFile(source, engine="openpyxl")
        target_df = None
        for sheet in workbook.sheet_names:
            raw = pd.read_excel(workbook, sheet_name=sheet, header=None)
            for row_index, row in raw.head(20).iterrows():
                row_text = " ".join(str(value) for value in row.values)
                if "Name" in row_text and "Beschreibung" in row_text:
                    print(f"✅ Header gefunden in Blatt '{sheet}', Zeile {row_index + 1}")
                    target_df = pd.read_excel(workbook, sheet_name=sheet, header=row_index)
                    break
            if target_df is not None:
                break
        if target_df is None:
            raise ValueError("Spalten 'Name' und 'Beschreibung' wurden nicht gefunden")

        target_df.columns = target_df.columns.str.strip()
        location_column = next(
            (column for column in target_df.columns if "Ort" in column or "Hyperlink" in column),
            None,
        )
        if location_column is None:
            raise ValueError("Spalte für 'Ort/Hyperlink' wurde nicht gefunden")

        success = 0
        for row_index, row in target_df.iterrows():
            try:
                name = safe_str(row.get("Name"))
                if not name:
                    continue
                kind = safe_str(row.get("Typ"))
                data = {
                    "Name": name,
                    "Typ": kind,
                    "Beschreibung": safe_str(row.get("Beschreibung")),
                    "Preis": safe_str(row.get("Preis/Anmerkung")),
                    "Ort": safe_str(row.get(location_column)),
                    "Tags": [],
                }
                for source_column in ("Förderkategorien", "ICF-Bereiche"):
                    raw_tags = safe_str(row.get(source_column))
                    if raw_tags:
                        data["Tags"].extend(
                            tag.strip()
                            for tag in raw_tags.replace(";", ",").split(",")
                            if tag.strip()
                        )

                location_lower = data["Ort"].lower()
                kind_lower = kind.lower()
                if location_lower.startswith(("http://", "https://", "www.")):
                    path = self.create_internet_resource(data)
                elif "literatur" in kind_lower or "buch" in kind_lower:
                    path = self.create_literature_reference(data)
                elif any(keyword in location_lower for keyword in MATERIAL_KEYWORDS) or "material" in kind_lower:
                    path = self.create_material_reference(data)
                else:
                    path = self.create_generic_info(data)
                category_id = self.get_or_create_collection(kind)
                self.register_in_db(path, category_id, data["Tags"], name)
                success += 1
            except (OSError, ValueError, sqlite3.Error) as exc:
                print(f"⚠️ Fehler in Zeile {row_index}: {exc}", file=sys.stderr)
        print(f"\n🎉 Fertig! {success} Einträge erfolgreich importiert.")
        return success


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Excel-Daten explizit und lokal in ProFiler importieren")
    parser.add_argument("--input", required=True, type=Path, help="Excel-Datei (.xlsx)")
    parser.add_argument("--database", required=True, type=Path, help="Ziel-Datenbank")
    parser.add_argument("--output", required=True, type=Path, help="Dedizierter Import-Ausgabeordner")
    parser.add_argument("--cleanup", action="store_true", help="Vorherigen markierten Import entfernen")
    parser.add_argument("--yes", action="store_true", help="Bestätigt den expliziten Cleanup")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.cleanup and not args.yes:
        print("FEHLER: --cleanup erfordert zusätzlich --yes", file=sys.stderr)
        return 2
    try:
        with ProfilerAutismoImporter(args.database, args.output) as importer:
            if args.cleanup:
                importer.cleanup_previous_import()
            importer.run_import(args.input)
    except (ImportSafetyError, FileNotFoundError, RuntimeError, ValueError, sqlite3.Error) as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
