@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PROFILER_EXE=%~dp0ProFiler.exe"
set "PROFILER_SHA=%~dp0ProFiler.exe.sha256"

if not exist "%PROFILER_EXE%" (
    if exist "%~dp0dist\ProFiler.exe" (
        set "PROFILER_EXE=%~dp0dist\ProFiler.exe"
        set "PROFILER_SHA=%~dp0dist\ProFiler.exe.sha256"
    )
)

if exist "%PROFILER_EXE%" if exist "%PROFILER_SHA%" (
    for /f "usebackq tokens=1" %%H in ("%PROFILER_SHA%") do set "EXPECTED_SHA=%%H"
    for /f "delims=" %%H in ('powershell.exe -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath $env:PROFILER_EXE).Hash"') do set "ACTUAL_SHA=%%H"
    if /I "%EXPECTED_SHA%"=="%ACTUAL_SHA%" (
        start "" "%PROFILER_EXE%" %*
        exit /b 0
    )
    echo [FEHLER] ProFiler.exe stimmt nicht mit ProFiler.exe.sha256 überein.
    exit /b 1
)

if exist "%PROFILER_EXE%" (
    start "" "%PROFILER_EXE%" %*
    exit /b 0
)

if exist "%~dp0Profiler_Suite_V15.py" (
    where py >nul 2>&1
    if not errorlevel 1 (
        py -3 "%~dp0Profiler_Suite_V15.py" %*
        exit /b %ERRORLEVEL%
    )
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [FEHLER] Python 3 wurde nicht gefunden.
        exit /b 1
    )
    python "%~dp0Profiler_Suite_V15.py" %*
    exit /b %ERRORLEVEL%
)

echo [FEHLER] Kein verifiziertes EXE-Paar und keine V15-Quelle gefunden.
exit /b 1
