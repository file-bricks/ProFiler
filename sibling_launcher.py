"""Modularer Starter für ProFiler-Geschwister-Anwendungen (z. B. ProSync).

Dieses Modul kapselt die gesamte Logik zum Auffinden und Starten von
Begleitanwendungen der ProFiler Suite. ProFiler importiert es optional —
es gibt keinerlei harte Abhängigkeit: ProFiler läuft vollständig weiter,
auch wenn ProSync oder ein anderes Geschwistermodul nicht installiert ist.

Hier liegt die kanonische Implementierung von
``normalize_configured_tool_path`` und ``resolve_prosync_launch_path``.
``Profiler_Suite_V15.py`` importiert sie von hier und definiert sie
nicht mehr selbst.

Öffentliche API
---------------
normalize_configured_tool_path(base_dir, configured_path) -> Path | None
resolve_prosync_launch_path(base_dir, configured_path="")  -> Path | None
launch_tool_process(tool_path)                             -> None
launch_prosync(base_dir, configured_path="")               -> LaunchOutcome
launch_sibling(key, display_name, base_dir, ...)           -> LaunchOutcome
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Muster für Windows-Umgebungsvariablen (%VAR%)
_WINDOWS_ENV_VAR_PATTERN = re.compile(r"%([^%]+)%")


# ---------------------------------------------------------------------------
# Pfad-Auflösung
# ---------------------------------------------------------------------------

def normalize_configured_tool_path(base_dir, configured_path) -> Path | None:
    """Expandiert einen konfigurierten Tool-Pfad und verankert relative Pfade am App-Root.

    Unterstützt Windows-%VAR%-Syntax sowie Unix-~/‑Tilde-Expansion.
    Gibt None zurück, wenn ``configured_path`` leer ist.
    """
    raw_path = str(configured_path).strip()
    if not raw_path:
        return None

    expanded_raw_path = _WINDOWS_ENV_VAR_PATTERN.sub(
        lambda match: os.environ.get(match.group(1), match.group(0)),
        raw_path,
    )
    expanded_path = Path(os.path.expandvars(expanded_raw_path)).expanduser()
    if not expanded_path.is_absolute():
        expanded_path = Path(base_dir).expanduser() / expanded_path
    return expanded_path


def _first_existing(candidates: list[Path]) -> Path | None:
    """Gibt den ersten existierenden Pfad aus der Liste zurück, oder None."""
    seen: set = set()
    for candidate in candidates:
        candidate = Path(candidate).expanduser()
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            return candidate
    return None


def resolve_prosync_launch_path(base_dir, configured_path: str = "") -> Path | None:
    """Ermittelt den besten verfügbaren ProSync-Einstiegspunkt.

    Kandidatenreihenfolge (höchste Priorität zuerst):

    1. Konfigurierter Pfad (mit %VAR%- und ~/-Expansion)
    2. Gleiches Verzeichnis wie ProFiler
    3. Geschwister-Verzeichnis ``../REL-PUB_ProSync/``

    Returns:
        Path zum ersten gefundenen Einstiegspunkt, oder None.
    """
    base_dir = Path(base_dir).expanduser()
    sibling_root = base_dir.parent / "REL-PUB_ProSync"

    candidates: list[Path] = []
    if configured_path:
        configured = normalize_configured_tool_path(base_dir, configured_path)
        if configured is not None:
            if configured.is_dir():
                candidates.extend([
                    configured / "ProSync.exe",
                    configured / "ProSyncStart_V3.1.py",
                    configured / "START.bat",
                    configured / "dist" / "ProSync" / "ProSync.exe",
                ])
            else:
                candidates.append(configured)

    candidates.extend([
        base_dir / "ProSync.exe",
        base_dir / "ProSyncStart_V3.1.py",
        base_dir / "START.bat",
        sibling_root / "ProSync.exe",
        sibling_root / "ProSyncStart_V3.1.py",
        sibling_root / "START.bat",
        sibling_root / "dist" / "ProSync" / "ProSync.exe",
    ])

    return _first_existing(candidates)


# ---------------------------------------------------------------------------
# Prozessstart
# ---------------------------------------------------------------------------

def launch_tool_process(tool_path) -> None:
    """Startet eine externe Python-, Batch- oder EXE-Datei als Subprozess.

    Wirft bei Fehler eine Exception (subprocess.SubprocessError oder OSError).
    Ist eine eigenständige Funktion, die kein PySide6 benötigt.
    """
    tool_path = Path(tool_path).expanduser()
    suffix = tool_path.suffix.lower()
    if suffix == ".py":
        subprocess.Popen([sys.executable, str(tool_path)], cwd=str(tool_path.parent))
    elif suffix == ".bat":
        subprocess.Popen(["cmd", "/c", str(tool_path)], cwd=str(tool_path.parent))
    else:
        subprocess.Popen([str(tool_path)], cwd=str(tool_path.parent))


# ---------------------------------------------------------------------------
# Ergebnis-Typen
# ---------------------------------------------------------------------------

class LaunchResult(Enum):
    """Ergebniscode eines Launch-Versuchs."""
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    LAUNCH_ERROR = "launch_error"


@dataclass
class LaunchOutcome:
    """Enthält das Ergebnis und eine menschenlesbare Meldung."""
    result: LaunchResult
    message: str
    path: Path | None = None

    @property
    def ok(self) -> bool:
        """True wenn der Start erfolgreich war."""
        return self.result == LaunchResult.SUCCESS


# ---------------------------------------------------------------------------
# Öffentliche Launcher-Funktionen
# ---------------------------------------------------------------------------

def launch_prosync(base_dir, configured_path: str = "") -> LaunchOutcome:
    """Startet ProSync als optionale Companion-App aus ProFiler heraus.

    Args:
        base_dir:        Verzeichnis von Profiler_Suite_V15.py (app_base_dir()).
        configured_path: Nutzerdefinierter Pfad aus den Einstellungen (kann leer sein).

    Returns:
        LaunchOutcome — ProFiler wertet nur ``result`` und ``message`` aus;
        kein Crash, wenn ProSync nicht gefunden wird.
    """
    path = resolve_prosync_launch_path(base_dir, configured_path)
    if path is None:
        return LaunchOutcome(
            result=LaunchResult.NOT_FOUND,
            message=(
                "ProSync konnte nicht automatisch gefunden werden.\n\n"
                "Bitte lege den Pfad in profiler_settings.json unter 'prosync_path' fest\n"
                "oder platziere ProSync neben ProFiler im gemeinsamen Software-Baum."
            ),
        )
    try:
        launch_tool_process(path)
        return LaunchOutcome(
            result=LaunchResult.SUCCESS,
            message=(
                "ProSync wurde als optionale Companion-App gestartet.\n\n"
                "ProFiler bleibt geöffnet, beide Werkzeuge laufen unabhängig."
            ),
            path=path,
        )
    except Exception as exc:
        return LaunchOutcome(
            result=LaunchResult.LAUNCH_ERROR,
            message=f"Konnte ProSync nicht starten:\n{exc}",
        )


def launch_sibling(
    key: str,
    display_name: str,
    base_dir,
    configured_path: str = "",
    candidates_fn: Callable[[Path, Path | None], list[Path]] | None = None,
) -> LaunchOutcome:
    """Allgemeiner Launcher für beliebige Geschwister-Module der ProFiler Suite.

    Ermöglicht es, künftige Module (z. B. PythonBox, FormConstructor) auf die
    gleiche Weise wie ProSync zu starten, ohne den Start-Code zu duplizieren.

    Args:
        key:            Modul-Schlüssel (z. B. ``"prosync"``).
        display_name:   Anzeigename für Meldungen (z. B. ``"ProSync"``).
        base_dir:       Verzeichnis der Kern-App.
        configured_path: Nutzerdefinierter Pfad aus den Einstellungen.
        candidates_fn:  Optionale Funktion ``(base_dir, configured) -> [Path, ...]``
                        zum Bereitstellen eigener Pfad-Kandidaten.
                        Wenn None, werden gleiches Verzeichnis und das
                        benannte Geschwister-Verzeichnis durchsucht.

    Returns:
        LaunchOutcome — NOT_FOUND mit erklärender Meldung wenn nicht gefunden,
        kein Crash.
    """
    base_dir = Path(base_dir).expanduser()
    configured: Path | None = None
    if configured_path:
        configured = normalize_configured_tool_path(base_dir, configured_path)

    if candidates_fn is not None:
        candidates = candidates_fn(base_dir, configured)
    else:
        sibling_hint = f"REL-PUB_{display_name.replace(' ', '')}"
        sibling_root = base_dir.parent / sibling_hint
        candidates = []
        if configured is not None:
            if configured.is_dir():
                candidates.extend([
                    configured / f"{display_name}.exe",
                    configured / f"{display_name}.py",
                    configured / "START.bat",
                ])
            else:
                candidates.append(configured)
        candidates.extend([
            base_dir / f"{display_name}.exe",
            base_dir / f"{display_name}.py",
            sibling_root / f"{display_name}.exe",
            sibling_root / f"{display_name}.py",
            sibling_root / "START.bat",
        ])

    path = _first_existing(candidates)
    if path is None:
        return LaunchOutcome(
            result=LaunchResult.NOT_FOUND,
            message=(
                f"{display_name} konnte nicht automatisch gefunden werden.\n\n"
                f"Bitte lege den Pfad in den Einstellungen unter '{key}_path' fest\n"
                "oder platziere das Modul neben ProFiler im gemeinsamen Software-Baum."
            ),
        )
    try:
        launch_tool_process(path)
        return LaunchOutcome(
            result=LaunchResult.SUCCESS,
            message=(
                f"{display_name} wurde als optionale Companion-App gestartet.\n\n"
                "ProFiler bleibt geöffnet, beide Werkzeuge laufen unabhängig."
            ),
            path=path,
        )
    except Exception as exc:
        return LaunchOutcome(
            result=LaunchResult.LAUNCH_ERROR,
            message=f"Konnte {display_name} nicht starten:\n{exc}",
        )
