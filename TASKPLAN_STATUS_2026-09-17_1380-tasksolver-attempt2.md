# TASKPLAN TASKSOLVER – ProFiler Task 1380

Datum: 2026-09-17
Rolle: TASKSOLVER / tasksolver-codex
Projekt: `C:/_Local_DEV/repos/ProFiler`
Task: `[ProFiler] Poppler- und Tesseract-Bündelung für OCR/PDF-Prozesse verifizieren`
Versuch: 2 über die laufende TASKSOLVER-Fortsetzung

## Fortschritt

Die fehlende Integrationskante wurde implementiert, ohne Runtime-Binaries zu erfinden oder herunterzuladen:

- `ocr_runtime.py` löst bei PyInstaller den expliziten Layoutvertrag `runtime/tesseract/` und `runtime/poppler/` auf und konfiguriert `pytesseract` sowie `pdf2image` nur bei vorhandenen Dateien.
- `scripts/write_ocr_bundle_args.py` erzeugt deterministische `--add-binary`-/`--add-data`-Argumente für Executables, DLLs und `tessdata` und verweigert unvollständige Bundles.
- `build_exe.bat` prüft die vier erforderlichen Runtime-Gates vor Venv-Erstellung/PyInstaller und beendet sich fail-closed.
- Vier neue Contract-Tests schützen Auflösung, Bundle-Argumente und den unvollständigen Zustand.

Commits:

- `4db39a4` – erster Prüfbericht.
- `9f4ef90` – `build: add fail-closed OCR runtime bundling contract`.

## Verifikation

- Pytest: `205 passed`.
- Ruff: `All checks passed!`.
- `git diff --check`: PASS.
- `cmd /c build_exe.bat` aus sauberem Checkout: Exit 1 vor PyInstaller mit:
  `OCR-Bundle fehlt: C:\_Local_DEV\repos\ProFiler\runtime\tesseract\tesseract.exe`.
- Kein `runtime/`-Verzeichnis, kein Build-Venv, kein Build-Output und keine OCR-Binary im MSIX-Staging vorhanden.
- `HEAD=9f4ef90a60ebb9442b7c58714e4e7fd6d028d270`; Remote `origin/master=5016595f6345af29b70a9d4133430aa366d6a4f6`.

## Offen / TASKPLAN

- Ein echter PyInstaller-/MSIX-Build mit gebündeltem Poppler/Tesseract und ein Installations-OCR-Smoke bleiben unbelegt, weil die freigegebenen lizenzierten Runtime-Dateien fehlen.
- Task 1380 bleibt offen. Dies ist Versuch 2; noch kein Skip und kein Projekt-Cursor-Sprung.
- Nächster sinnvoller Gate: Runtime-Verzeichnis mit `tesseract.exe`, `tessdata`, `pdftoppm.exe`, `pdfinfo.exe` und den zugehörigen DLLs bereitstellen und Lizenz-/Hash-Readback durchführen.
