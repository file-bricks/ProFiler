"""Copy a clean-checkout EXE to a local release folder and record provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from version import APP_VERSION  # noqa: E402


def _git(source_root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=source_root,
        text=True,
        encoding="utf-8",
        errors="strict",
    ).strip()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def write_provenance(source_root: Path, exe: Path, output_dir: Path) -> dict[str, object]:
    source_root = source_root.resolve()
    exe = exe.resolve()
    output_dir = output_dir.resolve()
    if not exe.is_file():
        raise FileNotFoundError(f"EXE fehlt: {exe}")
    if _inside(output_dir, source_root):
        raise ValueError("Release-Ausgabe muss außerhalb des Git-Checkouts liegen")
    dirty = _git(source_root, "status", "--porcelain", "--untracked-files=all")
    if dirty:
        raise RuntimeError("Git-Arbeitsbaum ist nicht sauber")

    source_sha = _git(source_root, "rev-parse", "HEAD")
    branch = _git(source_root, "rev-parse", "--abbrev-ref", "HEAD")
    remote = _git(source_root, "config", "--get", "remote.origin.url")
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact = output_dir / f"ProFiler-{APP_VERSION}-win64.exe"
    shutil.copy2(exe, artifact)
    sha256 = _hash_file(artifact)

    try:
        pyinstaller_version = subprocess.check_output(
            [sys.executable, "-m", "PyInstaller", "--version"],
            text=True,
            encoding="utf-8",
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        pyinstaller_version = "unknown"
    try:
        python_packages = sorted(
            line.strip()
            for line in subprocess.check_output(
                [sys.executable, "-m", "pip", "freeze", "--all"],
                text=True,
                encoding="utf-8",
            ).splitlines()
            if line.strip()
        )
    except (OSError, subprocess.CalledProcessError):
        python_packages = []

    payload: dict[str, object] = {
        "schema": "profiler-build-provenance-v1",
        "app_version": APP_VERSION,
        "artifact": artifact.name,
        "artifact_size": artifact.stat().st_size,
        "sha256": sha256,
        "source_commit": source_sha,
        "source_branch": branch,
        "source_remote": remote,
        "source_dirty": False,
        "built_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "python": platform.python_version(),
        "python_executable": str(Path(sys.executable).resolve()),
        "pyinstaller": pyinstaller_version,
        "python_packages": python_packages,
        "platform": platform.platform(),
        "signed": False,
        "publish_status": "local-only",
    }
    provenance = output_dir / "BUILD-PROVENANCE.json"
    temporary = provenance.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, provenance)
    (output_dir / "SHA256SUMS.txt").write_text(
        f"{sha256} *{artifact.name}\n",
        encoding="utf-8",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    write_provenance(args.source_root, args.exe, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
