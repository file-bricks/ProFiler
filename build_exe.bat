@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHONIOENCODING=utf-8"
set "PROJECT_ROOT=%CD%"
set "PROJECT_NAME=ProFiler"
set "ENTRY_SCRIPT=%PROJECT_ROOT%\Profiler_Suite_V15.py"
set "ICON_PATH=%PROJECT_ROOT%\ICO.ico"
set "SCANNER=%PROJECT_ROOT%\scripts\build_exclude_scanner.py"
set "PROVENANCE_WRITER=%PROJECT_ROOT%\scripts\write_build_provenance.py"
set "VERSION_WRITER=%PROJECT_ROOT%\scripts\write_windows_version_info.py"
set "BUILD_REQUIREMENTS=%PROJECT_ROOT%\requirements-build.txt"
if not defined BUILD_ROOT set "BUILD_ROOT=C:\_Local_DEV\codex_build\profiler"
if not defined BUILD_VENV set "BUILD_VENV=C:\_Local_DEV\venvs\profiler_build"
set "BUILD_PYTHON=%BUILD_VENV%\Scripts\python.exe"
set "EXCLUDE_ARGS=%BUILD_ROOT%\pyinstaller_excludes.txt"
set "VERSION_FILE=%BUILD_ROOT%\windows_version_info.txt"
set "RELEASE_OUTPUT=%BUILD_ROOT%\release"
set "PROVENANCE_FILE=%RELEASE_OUTPUT%\BUILD-PROVENANCE.json"

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Der Build muss aus einem Git-Checkout gestartet werden.
    exit /b 1
)
for /f "delims=" %%D in ('git status --porcelain --untracked-files^=all') do set "DIRTY_TREE=1"
if defined DIRTY_TREE (
    echo [FEHLER] Der Git-Arbeitsbaum ist nicht sauber. Kein Release-Build.
    git status --short
    exit /b 1
)

if not exist "%BUILD_PYTHON%" (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
    if errorlevel 1 (
        echo [FEHLER] Python 3.10 oder neuer wird benötigt.
        exit /b 1
    )
    python -m venv "%BUILD_VENV%"
    if errorlevel 1 (
        echo [FEHLER] Build-Venv konnte nicht angelegt werden.
        exit /b 1
    )
)

"%BUILD_PYTHON%" -m pip install --disable-pip-version-check -r "%BUILD_REQUIREMENTS%"
if errorlevel 1 (
    echo [FEHLER] Gepinnte Build-Abhängigkeiten konnten nicht installiert werden.
    exit /b 1
)

if not exist "%BUILD_ROOT%" mkdir "%BUILD_ROOT%"
"%BUILD_PYTHON%" "%SCANNER%" --project "%PROJECT_ROOT%" --emit pyinstaller > "%EXCLUDE_ARGS%"
if errorlevel 1 (
    echo [FEHLER] Build-Exclude-Scanner fehlgeschlagen.
    exit /b 1
)
set /p EXCLUDES=<"%EXCLUDE_ARGS%"

"%BUILD_PYTHON%" "%VERSION_WRITER%" --output "%VERSION_FILE%"
if errorlevel 1 exit /b 1

"%BUILD_PYTHON%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --onefile ^
  --name %PROJECT_NAME% ^
  --icon "%ICON_PATH%" ^
  --version-file "%VERSION_FILE%" ^
  --add-data "%PROJECT_ROOT%\locales;locales" ^
  %EXCLUDES% ^
  --distpath "%BUILD_ROOT%\dist" ^
  --workpath "%BUILD_ROOT%\build" ^
  --specpath "%BUILD_ROOT%" ^
  "%ENTRY_SCRIPT%"
if errorlevel 1 (
    echo [FEHLER] PyInstaller-Build fehlgeschlagen.
    exit /b 1
)

"%BUILD_PYTHON%" "%PROVENANCE_WRITER%" ^
  --source-root "%PROJECT_ROOT%" ^
  --exe "%BUILD_ROOT%\dist\%PROJECT_NAME%.exe" ^
  --output-dir "%RELEASE_OUTPUT%"
if errorlevel 1 (
    echo [FEHLER] Provenienz- und Prüfsummenvertrag fehlgeschlagen.
    exit /b 1
)
if not exist "%PROVENANCE_FILE%" (
    echo [FEHLER] BUILD-PROVENANCE.json wurde nicht erzeugt.
    exit /b 1
)

echo.
echo [OK] Lokal verifizierbares Build-Ergebnis:
echo   %RELEASE_OUTPUT%
echo [HINWEIS] Kein automatischer OneDrive-, Release- oder Upload-Schritt.
