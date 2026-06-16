"""
github_installer.py — ProFiler Suite Module Installer

Lädt fehlende Module direkt aus GitHub Releases herunter und installiert
sie in die Geschwister-Verzeichnisstruktur neben dem ProFiler-Ordner.

Verwendung (CLI):
    python github_installer.py list
    python github_installer.py install prosync
    python github_installer.py install-all

Verwendung (API):
    from github_installer import install_module, list_modules, GITHUB_REPOS
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# GitHub-Repo-Konfiguration
# ---------------------------------------------------------------------------

# key -> (org, repo) oder None wenn kein Repo verfügbar
GITHUB_REPOS: Dict[str, Optional[Tuple[str, str]]] = {
    "prosync": ("file-bricks", "ProSync"),
    "sqliteviewer": ("file-bricks", "SQLiteViewer"),
    "datenschutzampel": None,  # kein öffentliches GitHub-Repo verifiziert (file-bricks hat nur AmpelClip)
    "formconstructor": None,  # kein Git-Repo vorhanden
    "pythonbox": ("dev-bricks", "pythonbox"),
}

# Sibling-Verzeichnisnamen (identisch mit module_registry._KNOWN sibling_dir_hint)
_SIBLING_DIRS: Dict[str, str] = {
    "prosync": "REL-PUB_ProSync",
    "sqliteviewer": "REL-PUB_SQLiteViewer",
    "datenschutzampel": "REL-PUB_Datenschutzampel",
    "formconstructor": "REL-PUB_FormConstructor",
    "pythonbox": "REL-PUB_PythonBox",
}

_GITHUB_API = "https://api.github.com"
_TIMEOUT = 30  # Sekunden


# ---------------------------------------------------------------------------
# Datenklassen
# ---------------------------------------------------------------------------

@dataclass
class ReleaseInfo:
    tag_name: str
    name: str
    zipball_url: str
    zip_asset_url: Optional[str] = None
    zip_asset_name: Optional[str] = None


@dataclass
class InstallResult:
    key: str
    success: bool
    installed_path: Optional[Path] = None
    message: str = ""
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# GitHub-API-Abfragen
# ---------------------------------------------------------------------------

def fetch_latest_release(
    org: str,
    repo: str,
    token: Optional[str] = None,
) -> Optional[dict]:
    """Ruft das neueste Release von GitHub ab. Gibt None zurück wenn keins existiert."""
    url = f"{_GITHUB_API}/repos/{org}/{repo}/releases/latest"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ProFiler-Installer/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None  # Kein Release vorhanden
        raise
    except urllib.error.URLError:
        raise


def find_zip_asset(release: dict) -> Tuple[str, Optional[str]]:
    """
    Gibt (download_url, asset_name) zurück.
    Bevorzugt einen expliziten .zip-Asset; fällt auf zipball_url zurück.
    """
    for asset in release.get("assets", []):
        name = asset.get("name", "")
        if name.endswith(".zip"):
            return asset["browser_download_url"], name
    return release["zipball_url"], None


def parse_release(data: dict) -> ReleaseInfo:
    zip_url, zip_name = find_zip_asset(data)
    return ReleaseInfo(
        tag_name=data.get("tag_name", ""),
        name=data.get("name", ""),
        zipball_url=data.get("zipball_url", ""),
        zip_asset_url=zip_url,
        zip_asset_name=zip_name,
    )


# ---------------------------------------------------------------------------
# Download und Extraktion
# ---------------------------------------------------------------------------

def download_file(url: str, dest: Path, token: Optional[str] = None) -> None:
    """Lädt eine Datei von url nach dest herunter."""
    headers = {"User-Agent": "ProFiler-Installer/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        with open(dest, "wb") as f:
            shutil.copyfileobj(resp, f)


def extract_zip_to_sibling(zip_path: Path, sibling_dir: Path) -> None:
    """
    Entpackt zip_path in sibling_dir.
    GitHub-ZIPs enthalten typischerweise einen Unterordner (repo-tag/),
    dessen Inhalt direkt in sibling_dir landet.
    """
    sibling_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        # Gemeinsames Präfix ermitteln (GitHub erzeugt repo-tag/ als Top-Level)
        prefix = ""
        if names:
            first_parts = names[0].split("/")
            if len(first_parts) > 1:
                candidate = first_parts[0] + "/"
                if all(n.startswith(candidate) for n in names):
                    prefix = candidate

        for member in names:
            member_path = member[len(prefix):]  # Präfix abschneiden
            if not member_path:
                continue
            dest = sibling_dir / member_path
            if member.endswith("/"):
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, open(dest, "wb") as out:
                    shutil.copyfileobj(src, out)


# ---------------------------------------------------------------------------
# Haupt-Installer
# ---------------------------------------------------------------------------

def install_module(
    key: str,
    parent_dir: Optional[Path] = None,
    token: Optional[str] = None,
) -> InstallResult:
    """
    Installiert ein Modul aus dem GitHub-Release in das Geschwister-Verzeichnis.

    Args:
        key: Modul-Schlüssel (z. B. "prosync")
        parent_dir: Übergeordnetes Verzeichnis für die Sibling-Struktur.
                    Standard: Elternordner von github_installer.py
        token: Optionales GitHub-API-Token für höhere Rate-Limits

    Returns:
        InstallResult mit Ergebnis und ggf. Fehlermeldung
    """
    if key not in GITHUB_REPOS:
        return InstallResult(key=key, success=False, error=f"Unbekannter Modul-Schlüssel: {key!r}")

    repo_info = GITHUB_REPOS[key]
    if repo_info is None:
        return InstallResult(
            key=key,
            success=False,
            message=f"Modul '{key}' hat kein GitHub-Repository. Bitte manuell installieren.",
        )

    org, repo = repo_info
    if parent_dir is None:
        parent_dir = Path(__file__).parent.parent

    sibling_name = _SIBLING_DIRS.get(key, f"REL-PUB_{key.capitalize()}")
    sibling_dir = parent_dir / sibling_name

    try:
        release_data = fetch_latest_release(org, repo, token=token)
    except Exception as exc:
        return InstallResult(key=key, success=False, error=f"Netzwerkfehler: {exc}")

    if release_data is None:
        return InstallResult(
            key=key,
            success=False,
            message=f"Kein Release für {org}/{repo} gefunden. Bitte manuell installieren.",
        )

    release = parse_release(release_data)
    download_url = release.zip_asset_url or release.zipball_url

    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "module.zip"
        try:
            download_file(download_url, zip_path, token=token)
        except Exception as exc:
            return InstallResult(key=key, success=False, error=f"Download-Fehler: {exc}")

        try:
            extract_zip_to_sibling(zip_path, sibling_dir)
        except Exception as exc:
            return InstallResult(key=key, success=False, error=f"Extraktions-Fehler: {exc}")

    return InstallResult(
        key=key,
        success=True,
        installed_path=sibling_dir,
        message=f"Installiert: {org}/{repo} {release.tag_name} → {sibling_dir}",
    )


def install_all(parent_dir: Optional[Path] = None, token: Optional[str] = None) -> list:
    """Installiert alle Module mit verfügbarem GitHub-Repo."""
    results = []
    for key in GITHUB_REPOS:
        print(f"  Installiere {key}...")
        result = install_module(key, parent_dir=parent_dir, token=token)
        results.append(result)
        if result.success:
            print(f"    ✓ {result.message}")
        else:
            msg = result.error or result.message
            print(f"    ✗ {msg}")
    return results


def list_modules(parent_dir: Optional[Path] = None) -> None:
    """Gibt eine Statusübersicht aller Module aus."""
    if parent_dir is None:
        parent_dir = Path(__file__).parent.parent

    print("ProFiler Suite — Modul-Status")
    print("=" * 50)
    for key, repo_info in GITHUB_REPOS.items():
        sibling_name = _SIBLING_DIRS.get(key, f"REL-PUB_{key.capitalize()}")
        sibling_dir = parent_dir / sibling_name
        installed = "✓" if sibling_dir.exists() else "✗"
        if repo_info:
            org, repo = repo_info
            github = f"github.com/{org}/{repo}"
        else:
            github = "(kein Repo)"
        print(f"  {installed} {key:<18} {sibling_name:<25} {github}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli(args: list) -> int:
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    cmd = args[0]

    if cmd == "list":
        list_modules()
        return 0

    if cmd == "install" and len(args) >= 2:
        key = args[1]
        print(f"Installiere Modul '{key}'...")
        result = install_module(key)
        if result.success:
            print(f"Erfolgreich: {result.message}")
            return 0
        else:
            msg = result.error or result.message
            print(f"Fehler: {msg}", file=sys.stderr)
            return 1

    if cmd == "install-all":
        print("Installiere alle Module...")
        results = install_all()
        failed = [r for r in results if not r.success and r.error]
        return 1 if failed else 0

    print(f"Unbekannter Befehl: {cmd!r}", file=sys.stderr)
    print("Befehle: list | install <key> | install-all")
    return 2


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
