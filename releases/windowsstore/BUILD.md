# ProFiler Suite — Windows Store Packaging & Build-Anleitung

## Voraussetzungen

1. Python 3.10+ mit PySide6, PyMuPDF, pytesseract, Pillow, reportlab
2. PyInstaller für den Desktop-Build
3. Windows 10/11 SDK mit `makeappx.exe` und `appcert.exe` (WACK)
4. Lokaler Schreibpfad außerhalb synchronisierter Cloud-Ordner: `C:\_Local_DEV\codex_build\profiler`

## Schritt 0: Store-Material & Kacheln prüfen

```powershell
$projectRoot = "C:\_Local_DEV\repos\ProFiler"
Set-Location $projectRoot
python scripts\check_store_readiness.py
```

Erwartetes Ergebnis:
- Alle Kacheln in `store_assets/`, `store_package/ProFiler/icons/` und `releases/windowsstore/` vorhanden und maßhaltig.
- Screenshots in `screenshots/store/` und `releases/windowsstore/screenshots/` maßhaltig (1920x1080).
- Preflight-Auditor meldet 0 Findings (PASS).

## Schritt 1: Desktop-EXE bauen

```powershell
Set-Location $projectRoot
.\build_exe.bat
```

Erwartetes Build-Ergebnis:
- `C:\_Local_DEV\codex_build\profiler\dist\ProFiler.exe`

## Schritt 2: Desktop-Bridge Packaging vorbereiten

Das Packaging-Manifest liegt unter `store_package/ProFiler/AppxManifest.xml` bereit.
Kopiere die gebaute `ProFiler.exe` in den Staging-Ordner `store_package/ProFiler/`:

```powershell
Copy-Item "C:\_Local_DEV\codex_build\profiler\dist\ProFiler.exe" "store_package\ProFiler\"
```

## Schritt 3: MSIX-Paket erstellen (makeappx)

```powershell
$outputDir = "C:\_Local_DEV\codex_build\profiler-store"
New-Item -ItemType Directory -Force -Path $outputDir
& "C:\Program Files (x86)\Windows Kits\10\App Certification Kit\makeappx.exe" pack /d "store_package\ProFiler" /p "$outputDir\ProFiler.msix"
```

## Schritt 4: WACK-Prüfung ausführen

```powershell
python scripts\run_windows_wack.py --msix "$outputDir\ProFiler.msix"
```

Der resultierende Prüfbericht wird in `releases/windowsstore/test_reports/` abgelegt und in `releases/windowsstore/WACK_PROTOCOL.md` dokumentiert.
