"""
github_installer.py — ProFiler Suite Module Installer

Lädt fehlende Module direkt aus GitHub Releases herunter und installiert
sie in die Geschwister-Verzeichnisstruktur neben dem ProFiler-Ordner.

Verwendung (CLI; SHA-256 ist verpflichtend, falls GitHub keinen Asset-Digest liefert):
    python github_installer.py list
    python github_installer.py install prosync --sha256 <64-hex>
    python github_installer.py install-all

Verwendung (API):
    from github_installer import install_module, list_modules, GITHUB_REPOS
"""

from __future__ import annotations

import json
import hashlib
import shutil
import stat
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

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
_MAX_DOWNLOAD_BYTES = 512 * 1024 * 1024
_MAX_ARCHIVE_FILES = 10_000
_MAX_UNCOMPRESSED_BYTES = 1024 * 1024 * 1024
_ALLOWED_DOWNLOAD_HOSTS = frozenset({
    "api.github.com",
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
})


class InstallSafetyError(RuntimeError):
    """Ein Modularchiv verletzt den fail-closed Installationsvertrag."""


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
    expected_sha256: Optional[str] = None


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
    expected_sha256 = None
    if zip_name:
        for asset in data.get("assets", []):
            if asset.get("name") != zip_name:
                continue
            digest = str(asset.get("digest") or "")
            if digest.lower().startswith("sha256:"):
                candidate = digest.split(":", 1)[1].lower()
                if len(candidate) == 64 and all(ch in "0123456789abcdef" for ch in candidate):
                    expected_sha256 = candidate
            break
    return ReleaseInfo(
        tag_name=data.get("tag_name", ""),
        name=data.get("name", ""),
        zipball_url=data.get("zipball_url", ""),
        zip_asset_url=zip_url,
        zip_asset_name=zip_name,
        expected_sha256=expected_sha256,
    )


# ---------------------------------------------------------------------------
# Download und Extraktion
# ---------------------------------------------------------------------------

def _validated_https_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_DOWNLOAD_HOSTS:
        raise InstallSafetyError("Download-URL muss HTTPS und ein erlaubter GitHub-Host sein")
    if parsed.username or parsed.password:
        raise InstallSafetyError("Download-URL darf keine Zugangsdaten enthalten")
    return url


def download_file(
    url: str,
    dest: Path,
    token: Optional[str] = None,
    max_bytes: int = _MAX_DOWNLOAD_BYTES,
) -> None:
    """Lädt eine begrenzte Datei; Tokens werden nur an api.github.com gesendet."""
    _validated_https_url(url)
    headers = {"User-Agent": "ProFiler-Installer/1.0"}
    if token and urlparse(url).hostname == "api.github.com":
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        length_header = resp.headers.get("Content-Length") if getattr(resp, "headers", None) else None
        if length_header and int(length_header) > max_bytes:
            raise InstallSafetyError("Download überschreitet das Größenlimit")
        total = 0
        with open(dest, "wb") as handle:
            while chunk := resp.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    raise InstallSafetyError("Download überschreitet das Größenlimit")
                handle.write(chunk)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def extract_zip_to_sibling(zip_path: Path, sibling_dir: Path) -> None:
    """
    Entpackt zip_path in sibling_dir.
    GitHub-ZIPs enthalten typischerweise einen Unterordner (repo-tag/),
    dessen Inhalt direkt in sibling_dir landet.
    """
    sibling_dir = sibling_dir.resolve()
    if sibling_dir.exists():
        raise InstallSafetyError(
            f"Ziel existiert bereits; kein Merge oder Überschreiben erlaubt: {sibling_dir}"
        )
    sibling_dir.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        infos = zf.infolist()
        if len(infos) > _MAX_ARCHIVE_FILES:
            raise InstallSafetyError("Archiv enthält zu viele Einträge")
        total_size = sum(info.file_size for info in infos)
        if total_size > _MAX_UNCOMPRESSED_BYTES:
            raise InstallSafetyError("Archiv überschreitet das Entpacklimit")
        names = [info.filename.replace("\\", "/") for info in infos]
        for original in names:
            original_path = Path(original)
            if (
                original.startswith("/")
                or original_path.is_absolute()
                or original_path.drive
                or ".." in original_path.parts
            ):
                raise InstallSafetyError(f"Unsicherer Archivpfad: {original!r}")
        # Gemeinsames Präfix ermitteln (GitHub erzeugt repo-tag/ als Top-Level)
        prefix = ""
        if names:
            first_parts = names[0].split("/")
            if len(first_parts) > 1:
                candidate = first_parts[0] + "/"
                if all(n.startswith(candidate) for n in names):
                    prefix = candidate

        with tempfile.TemporaryDirectory(prefix="profiler-module-", dir=sibling_dir.parent) as tmp:
            staging = (Path(tmp) / "payload").resolve()
            staging.mkdir()
            seen: set[str] = set()
            extracted_files = 0
            for info, normalized_name in zip(infos, names):
                member_path = normalized_name[len(prefix):]
                if not member_path:
                    continue
                relative = Path(member_path)
                if (
                    normalized_name.startswith("/")
                    or relative.is_absolute()
                    or relative.drive
                    or ".." in relative.parts
                    or any(part in {"", "."} for part in relative.parts)
                ):
                    raise InstallSafetyError(f"Unsicherer Archivpfad: {info.filename!r}")
                file_type = (info.external_attr >> 16) & 0o170000
                if file_type not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise InstallSafetyError(f"Sonderdatei im Archiv ist nicht erlaubt: {info.filename!r}")

                collision_key = member_path.casefold()
                if collision_key in seen:
                    raise InstallSafetyError(f"Doppelter Archivpfad: {info.filename!r}")
                seen.add(collision_key)

                destination = (staging / relative).resolve()
                try:
                    destination.relative_to(staging)
                except ValueError as exc:
                    raise InstallSafetyError(f"Archivpfad verlässt das Ziel: {info.filename!r}") from exc
                if info.is_dir() or normalized_name.endswith("/"):
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                extracted_files += 1
                destination.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as source, destination.open("xb") as output:
                    shutil.copyfileobj(source, output)
            if extracted_files == 0:
                raise InstallSafetyError("Archiv enthält keine regulären Dateien")
            staging.replace(sibling_dir)


# ---------------------------------------------------------------------------
# Haupt-Installer
# ---------------------------------------------------------------------------

def install_module(
    key: str,
    parent_dir: Optional[Path] = None,
    token: Optional[str] = None,
    expected_sha256: Optional[str] = None,
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
    if sibling_dir.exists():
        return InstallResult(
            key=key,
            success=False,
            error=f"Ziel existiert bereits; kein Merge oder Überschreiben erlaubt: {sibling_dir}",
        )

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
    verified_sha256 = (expected_sha256 or release.expected_sha256 or "").lower()
    if len(verified_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in verified_sha256):
        return InstallResult(
            key=key,
            success=False,
            error="Kein verifizierter SHA-256 für das Release-Archiv vorhanden.",
        )
    try:
        _validated_https_url(download_url)
    except InstallSafetyError as exc:
        return InstallResult(key=key, success=False, error=str(exc))

    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "module.zip"
        try:
            # API-Token nie an Asset-/Redirect-Hosts weiterreichen.
            download_file(download_url, zip_path, token=None)
        except Exception as exc:
            return InstallResult(key=key, success=False, error=f"Download-Fehler: {exc}")

        actual_sha256 = _sha256(zip_path)
        if actual_sha256 != verified_sha256:
            return InstallResult(
                key=key,
                success=False,
                error=f"SHA-256 stimmt nicht: erwartet {verified_sha256}, erhalten {actual_sha256}",
            )

        try:
            extract_zip_to_sibling(zip_path, sibling_dir)
        except Exception as exc:
            return InstallResult(key=key, success=False, error=f"Extraktions-Fehler: {exc}")

    return InstallResult(
        key=key,
        success=True,
        installed_path=sibling_dir,
        message=(
            f"Installiert: {org}/{repo} {release.tag_name} → {sibling_dir} "
            f"(SHA-256 {verified_sha256})"
        ),
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
        expected_sha256 = None
        if "--sha256" in args[2:]:
            index = args.index("--sha256")
            if index + 1 >= len(args):
                print("Fehler: --sha256 benötigt einen Wert", file=sys.stderr)
                return 2
            expected_sha256 = args[index + 1]
        print(f"Installiere Modul '{key}'...")
        result = install_module(key, expected_sha256=expected_sha256)
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
    print("Befehle: list | install <key> [--sha256 <64-hex>] | install-all")
    return 2


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
