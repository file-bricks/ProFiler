# TASKPLAN TASKSOLVER – ProFiler Task 1380

Datum: 2026-09-17
Rolle: TASKSOLVER / tasksolver-codex
Projekt: `C:/_Local_DEV/repos/ProFiler`
Task: `[ProFiler] Poppler- und Tesseract-Bündelung für OCR/PDF-Prozesse verifizieren`
Selektor: Exit 0, Deep/Medium, Rechte `read/create/modify`
Versuch: 1 über die laufende TASKSOLVER-Fortsetzung

## Ergebnis

Der Versuch ist fehlgeschlagen und bleibt offen. Es gibt keinen belastbaren Nachweis für eine Poppler-/Tesseract-Bündelung im PyInstaller- oder MSIX-Paket.

- `build_exe.bat` enthält nur `--add-data "%PROJECT_ROOT%\locales;locales"`; es gibt keinen `--add-binary`-Schritt für Poppler oder Tesseract.
- Im Repository fehlen Runtime-Verzeichnisse für `tesseract`, `poppler` oder vergleichbare Vendor-Bundles.
- `C:\_Local_DEV\venvs\profiler_build` und `C:\_Local_DEV\codex_build\profiler` existieren nicht; ein Release-Build ist damit nicht reproduzierbar vorhanden.
- Python-Abhängigkeiten (`pdf2image`, `pytesseract`, `PyMuPDF`, `pypdf`) sind importierbar.
- `pdftoppm.exe` und `pdfinfo.exe` werden nur aus `C:\Users\lukas\AppData\Local\Programs\MiKTeX\miktex\bin\x64` gefunden; das ist kein Projektbundle.
- `tesseract.exe` ist weder im PATH noch in den geprüften lokalen Installationspfaden vorhanden.

## Tatsächlicher OCR/PDF-Smoke

Ein synthetisches einseitiges PDF wurde lokal erzeugt. Der PDF-Render mit dem vorhandenen Poppler bestand (`1` Seite). Der anschließende reale Aufruf `PDFUtils.apply_ocr_to_pdf(..., "eng")` scheiterte erwartungsgemäß mit:

`OCR fehlgeschlagen: tesseract is not installed or it's not in your PATH.`

Damit ist nur der Poppler-Renderpfad teilweise beobachtet; ein Installations-/Paket-OCR-Smoke ist nicht bestanden.

## Nebenprüfungen

- Pytest: `201 passed`.
- Ruff: `All checks passed!`.
- `source_platform_smoke.py`: `6/6 Checks bestanden`.
- `scripts/check_store_readiness.py`: `5/5 Checks OK`; dieser Audit deckt Icons, Metadaten, Listing und Screenshots ab, nicht die externe OCR-Binary-Bündelung.
- Git-Arbeitsbaum vor dem Bericht sauber; `HEAD=origin/master=5016595f6345af29b70a9d4133430aa366d6a4f`.

## TASKPLAN-Status

- Keine Binaries erfunden, heruntergeladen oder in das Repository kopiert.
- Kein PyInstaller-/MSIX-Erfolg behauptet.
- Task 1380 bleibt offen. Dies ist Versuch 1; kein Skip und kein Projekt-Cursor-Sprung nach dem ersten Fehlschlag.
- Für einen späteren Versuch benötigt das Projekt freigegebene, lizenzierte Runtime-Verzeichnisse mit `tesseract.exe`, `tessdata` sowie Poppler-Executables/DLLs und einen reproduzierbaren Build-/MSIX-Lauf.
