# module_registry.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ModuleInfo:
    key: str
    display_name: str
    filename: str
    configured_path: str = ""
    resolved_path: Optional[Path] = None
    available: bool = False


_KNOWN: List[tuple] = [
    # (key, display_name, filename, sibling_dir_hint, extra_candidates)
    (
        "prosync",
        "ProSync",
        "ProSyncStart_V3.1.py",
        "REL-PUB_ProSync",
        ["ProSync.exe", "START.bat", "dist/ProSync/ProSync.exe"],
    ),
    (
        "sqliteviewer",
        "SQLiteViewer",
        "SQLiteViewer.py",
        "REL-PUB_SQLiteViewer",
        [],
    ),
    (
        "datenschutzampel",
        "Datenschutzampel",
        "ProFiler_Datenschutzampel.py",
        "REL-PUB_Datenschutzampel",
        [],
    ),
    (
        "formconstructor",
        "FormConstructor",
        "FormConstructor_V1_5.py",
        "REL-PUB_FormConstructor",
        ["FormConstructor.py"],
    ),
    (
        "pythonbox",
        "PythonBox",
        "PythonBox.py",
        "REL-PUB_PythonBox",
        [],
    ),
]


class ModuleRegistry:
    """Erkennt alle ProFiler-Suite-Begleitmodule anhand von Pfadkandidaten."""

    def __init__(
        self,
        base_dir: Path,
        configured_paths: Optional[Dict[str, str]] = None,
    ):
        self._base_dir = Path(base_dir).expanduser().resolve()
        self._configured = configured_paths or {}
        self._modules: Dict[str, ModuleInfo] = {}
        self._detect_all()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[ModuleInfo]:
        return self._modules.get(key)

    def get_by_filename(self, filename: str) -> Optional[ModuleInfo]:
        """Liefert ModuleInfo zum bekannten Hauptdateinamen, oder None."""
        for info in self._modules.values():
            if info.filename == filename:
                return info
        return None

    def all_modules(self) -> List[ModuleInfo]:
        return list(self._modules.values())

    def refresh(self) -> None:
        self._modules.clear()
        self._detect_all()

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def _detect_all(self) -> None:
        for key, display_name, filename, sibling_hint, extras in _KNOWN:
            configured = self._configured.get(key, "")
            info = self._detect_one(key, display_name, filename, sibling_hint, extras, configured)
            self._modules[key] = info

    def _detect_one(
        self,
        key: str,
        display_name: str,
        filename: str,
        sibling_hint: str,
        extras: List[str],
        configured_path: str,
    ) -> ModuleInfo:
        candidates: List[Path] = []

        # 1) Konfigurierter Pfad hat höchste Priorität
        if configured_path:
            p = Path(configured_path).expanduser()
            if not p.is_absolute():
                p = self._base_dir / p
            if p.is_dir():
                candidates.append(p / filename)
                for ex in extras:
                    candidates.append(p / ex)
            else:
                candidates.append(p)

        # 2) Gleiches Verzeichnis
        candidates.append(self._base_dir / filename)
        for ex in extras:
            candidates.append(self._base_dir / ex)

        # 3) Benanntes Geschwister-Verzeichnis
        sibling = self._base_dir.parent / sibling_hint
        if sibling.exists():
            candidates.append(sibling / filename)
            for ex in extras:
                candidates.append(sibling / ex)

        seen: set = set()
        for c in candidates:
            resolved = c.resolve() if c.exists() else c
            key_str = str(resolved)
            if key_str in seen:
                continue
            seen.add(key_str)
            if resolved.exists():
                return ModuleInfo(
                    key=key,
                    display_name=display_name,
                    filename=filename,
                    configured_path=configured_path,
                    resolved_path=resolved,
                    available=True,
                )

        return ModuleInfo(
            key=key,
            display_name=display_name,
            filename=filename,
            configured_path=configured_path,
        )
