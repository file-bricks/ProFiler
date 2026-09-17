# TASKPLAN TASKSOLVER – ProFiler Task 1380 – SKIP

Datum: 2026-09-17
Rolle: TASKSOLVER / tasksolver-codex
Projekt: `C:/_Local_DEV/repos/ProFiler`
Task: `[ProFiler] Poppler- und Tesseract-Bündelung für OCR/PDF-Prozesse verifizieren`
Versuch: 3 über die laufende TASKSOLVER-Fortsetzung

## SKIP-Grund

`SKIP_MISSING_AUTHORIZED_OCR_RUNTIME`: Die für einen belastbaren PyInstaller-/MSIX-Nachweis erforderlichen freigegebenen, lizenzierten Runtime-Dateien sind nicht erreichbar. Es fehlen:

- `runtime/tesseract/tesseract.exe`
- `runtime/tesseract/tessdata/`
- `runtime/poppler/pdftoppm.exe`
- `runtime/poppler/pdfinfo.exe`

Das System stellt nur `pdftoppm.exe`/`pdfinfo.exe` aus einer MiKTeX-Installation bereit; `tesseract.exe` ist nicht vorhanden. Ein Ersatz durch Systemdateien, Download oder erfundene Asset-/Lizenzdaten wäre nicht autorisiert.

## Was nach drei Versuchen belegt ist

- Versuch 1: Bestandsprüfung und echter synthetischer PDF-Smoke; Poppler rendert 1 Seite, OCR scheitert wegen fehlendem Tesseract.
- Versuch 2: `ocr_runtime.py`, `scripts/write_ocr_bundle_args.py` und fail-closed Gates in `build_exe.bat` ergänzt; `205/205` Pytests, Ruff und Bundle-Contract-Tests grün.
- Versuch 3: sauberer `cmd /c build_exe.bat`-Aufruf beendet vor PyInstaller mit Exit 1 und meldet das fehlende `tesseract.exe`.
- Store-Readiness `5/5` ist grün, belegt aber keine OCR-Binary-Bündelung.

Vorberichte:

- `TASKPLAN_STATUS_2026-09-17_1380-tasksolver-attempt1.md`, SHA-256 `D8B4A634896C6CC0983C6247CED681701AF038111F3E55CC2C4B6BE3347C6D7D`.
- `TASKPLAN_STATUS_2026-09-17_1380-tasksolver-attempt2.md`, SHA-256 `3894202C8F0A2942B3DC0AFDFC15705539BAB2B26E28B249FE9D4F32F85BD9C6`.

## TASKPLAN-Aktion

- Task 1380 bleibt absichtlich offen.
- Nach diesem dritten Fehlschlag wird ausschließlich Task 1380 mit `python -m taskplan skip --role tasksolver --task 1380` ans Ende gereiht.
- Der Projektcursor wird dadurch weitergesetzt; es wird kein Erfolg und kein fertiges PyInstaller-/MSIX-Paket behauptet.
- Nächster Gate nach Bereitstellung der Runtime: Lizenz-/Hash-Readback, PyInstaller-Build, Bundle-Inspektion, OCR-Installations-Smoke und erst danach MSIX-/WACK-Prüfung.

Ausführungsnachweis:

- `python -m taskplan skip --role tasksolver --task 1380` beendet mit Exit 0 und reiht Task 1380 ans Ende.
- Direkter Taskplan-Readback: `status=open`, `done_at=null`, `assigned_to=""`; der Task bleibt offen.
