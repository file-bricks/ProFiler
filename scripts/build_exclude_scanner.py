#!/usr/bin/env python3
"""build_exclude_scanner.py -- Automatischer PyInstaller-Exclude-Scanner (.SOFTWARE-Standard).

Verbindlicher Bestandteil des .SOFTWARE-Build-Verfahrens (siehe ``BUILD-VERFAHREN.md`` im
Root und ``RELEASE-MANAGEMENT.md``). Loest das Kernproblem, dass PyInstaller beim Bauen mit
dem System-Python ungewollt **schwere Pakete** (torch, matplotlib, transformers, ...) in die
EXE zieht, sobald sie global installiert sind -- auch wenn die App sie gar nicht importiert
(empirisch belegt 2026-06-01 an FormConstructor: 'PULLED BY APP IMPORTS: []', torch trotzdem
gebundelt -> riesige, langsame, OOM-anfaellige EXE).

GEWAEHLTE LOESUNG (User-Entscheidung 2026-06-02): Option 3 'Excludes', aber mit AUTOMATISCH
gepflegter Liste -- statt die Exclude-Liste pro Projekt von Hand zu fuehren (das eigentliche
Risiko von Option 3), ermittelt dieses Tool sie. Faellt diese Loesung als unzuverlaessig auf,
ist der Eskalationspfad: Option 2 (dediziertes venv) bzw. Option 1 (venv + Excludes) -- siehe
ROADMAP in BUILD-VERFAHREN.md.

Verfahren:
  1. Kuratierte Liste bekannter SCHWERER / ungewollter Pakete (HEAVY_MODULES).
  2. Scanner prueft, welche davon im AKTUELLEN (= Build-)Python installiert sind
     -- der Scanner MUSS mit demselben ``python`` laufen, mit dem PyInstaller baut.
  3. Scanner prueft, ob die App eines davon tatsaechlich braucht
     (requirements*.txt + AST-Import-Scan ueber den Projekt-Quellcode).
  4. EXCLUDE := installiert  UND  von der App NICHT gebraucht.

Bewusst KONSERVATIV: Wird ein schweres Paket von der App importiert oder steht es in den
requirements, wird es NIE excludiert (lieber eine grosse EXE als eine kaputte). Das Tool
LOGGT jede Entscheidung nach stderr (nachvollziehbar, kein stilles Truncating).

Ausgabe-Modi (--emit):
  pyinstaller : "--exclude-module A --exclude-module B ..."  (eine Zeile, fuer build_exe.bat)
  list        : ein Modul pro Zeile (stdout)
  spec        : Python-Liste fuer .spec  excludes=[...]
  json        : {"excludes": [...], "installed_heavy": [...], "used": [...]}
  check       : nichts auf stdout; exit 0 immer (nur stderr-Report) -- fuer Hooks/CI

Zero Dependencies (nur stdlib). Windows + POSIX.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Kuratierte Negativliste: schwere/ungewollte Pakete als IMPORT-Modulnamen.
# Schluessel = Modulname (so wie 'import X' / fuer PyInstaller --exclude-module X).
# Diese gehoeren praktisch nie in eine Desktop-GUI-/CLI-App; sind sie dennoch
# installiert (z.B. weil das System-Python auch fuer ML-Projekte genutzt wird),
# zieht PyInstaller sie sonst mit. Erweiterbar -- zentral hier pflegen.
# ---------------------------------------------------------------------------
HEAVY_MODULES: frozenset[str] = frozenset({
    # Deep Learning / Tensor
    "torch", "torchvision", "torchaudio", "tensorflow", "tensorboard", "keras",
    "jax", "jaxlib", "flax", "transformers", "sentence_transformers", "datasets",
    "tokenizers", "safetensors", "accelerate", "onnx", "onnxruntime", "triton",
    # Wissenschaftliches Rechnen / Daten (schwer; via used-check geschuetzt)
    "scipy", "sklearn", "matplotlib", "sympy", "numba", "llvmlite", "pandas",
    "statsmodels", "pyarrow", "polars", "dask", "xarray", "h5py", "tables",
    # Vision / Audio / Media
    "cv2", "skimage", "librosa", "soundfile", "moviepy", "imageio_ffmpeg",
    # Game frameworks (fuer Nicht-Spiel-Tools typischerweise unerwuenscht)
    "pygame",
    # Plot / Viz
    "plotly", "bokeh", "seaborn", "altair",
    # Notebook / IPython
    "IPython", "ipykernel", "jupyter", "jupyter_core", "notebook", "nbconvert",
    # Grosse SDKs / NLP
    "spacy", "nltk", "gensim", "selenium", "playwright",
})

# Modul -> moegliche Distributions-/requirements-Namen (fuer den used-check).
# Nur dort noetig, wo Import-Name != PyPI-Name.
MODULE_TO_DISTS: dict[str, tuple[str, ...]] = {
    "sklearn": ("scikit-learn", "scikit_learn", "sklearn"),
    "cv2": ("opencv-python", "opencv-python-headless", "opencv_python", "cv2"),
    "skimage": ("scikit-image", "scikit_image", "skimage"),
    "PIL": ("pillow", "pil"),
    "imageio_ffmpeg": ("imageio-ffmpeg", "imageio_ffmpeg"),
    "sentence_transformers": ("sentence-transformers", "sentence_transformers"),
    "jupyter_core": ("jupyter-core", "jupyter_core"),
}

_REQ_NAME_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)")


def _norm(name: str) -> str:
    """Distributions-/Modulnamen auf einen Vergleichsschluessel normalisieren."""
    return name.strip().lower().replace("-", "_")


def find_source_root(project: Path) -> Path:
    """Bevorzugt ``src/`` als Quellwurzel, sonst das Projektverzeichnis selbst."""
    src = project / "src"
    return src if src.is_dir() else project


def iter_python_files(root: Path):
    """Alle .py-Dateien unter ``root`` -- ohne venvs, Build-, VCS- und Cache-Ordner."""
    skip = {".git", ".venv", "venv", "build", "dist", "__pycache__", ".pytest_cache",
            ".mypy_cache", ".ruff_cache", "node_modules", "site-packages"}
    for path in root.rglob("*.py"):
        if any(part in skip for part in path.parts):
            continue
        yield path


def collect_app_imports(project: Path) -> set[str]:
    """Top-Level-Importnamen aus dem Projekt-Quellcode (AST, robust gegen Syntaxfehler)."""
    root = find_source_root(project)
    found: set[str] = set()
    for py in iter_python_files(root):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8", errors="replace"), filename=str(py))
        except (SyntaxError, ValueError, OSError):
            continue  # eine unparsebare Datei darf den Scan nie kippen
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:  # nur absolute Imports
                    found.add(node.module.split(".")[0])
    return found


def collect_requirements(project: Path) -> set[str]:
    """Distributionsnamen aus allen requirements*.txt (normalisiert)."""
    names: set[str] = set()
    for req in project.glob("requirements*.txt"):
        try:
            for line in req.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                m = _REQ_NAME_RE.match(line)
                if m:
                    names.add(_norm(m.group(1)))
        except OSError:
            continue
    return names


def is_installed(module: str) -> bool:
    """Ist ``module`` im AKTUELLEN (Build-)Python importierbar? (kein Voll-Import)"""
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError, ModuleNotFoundError, AttributeError):
        # Manche Pakete werfen beim find_spec -> als 'nicht sauber verfuegbar' behandeln.
        return False


def app_uses(module: str, app_imports: set[str], req_names: set[str]) -> bool:
    """Braucht die App ``module`` (direkter Import ODER requirements-Eintrag)?"""
    if module in app_imports:
        return True
    candidates = {_norm(module), *(_norm(d) for d in MODULE_TO_DISTS.get(module, ()))}
    return bool(candidates & req_names)


def compute_excludes(project: Path) -> dict[str, list[str]]:
    """Kernlogik: liefert excludes + Diagnose-Listen (alles sortiert, deterministisch)."""
    app_imports = collect_app_imports(project)
    req_names = collect_requirements(project)

    installed_heavy: list[str] = sorted(m for m in HEAVY_MODULES if is_installed(m))
    used: list[str] = sorted(
        m for m in HEAVY_MODULES if app_uses(m, app_imports, req_names)
    )
    excludes = sorted(
        m for m in installed_heavy if not app_uses(m, app_imports, req_names)
    )
    return {
        "excludes": excludes,
        "installed_heavy": installed_heavy,
        "used": used,
        "app_imports": sorted(app_imports),
        "requirements": sorted(req_names),
    }


def _report(result: dict[str, list[str]], project: Path) -> None:
    """Nachvollziehbarer Bericht nach stderr (kein stilles Weglassen)."""
    print(f"[build-exclude-scanner] Projekt: {project}", file=sys.stderr)
    print(f"[build-exclude-scanner] Build-Python: {sys.executable}", file=sys.stderr)
    inst = result["installed_heavy"]
    used = result["used"]
    exc = result["excludes"]
    print(
        f"[build-exclude-scanner] schwere Pakete im Build-Python: "
        f"{', '.join(inst) if inst else '(keine)'}",
        file=sys.stderr,
    )
    if used:
        print(
            f"[build-exclude-scanner] von der App GEBRAUCHT (nicht excludiert): "
            f"{', '.join(used)}",
            file=sys.stderr,
        )
    print(
        f"[build-exclude-scanner] -> EXCLUDE ({len(exc)}): "
        f"{', '.join(exc) if exc else '(keine -- sauberes Build-Python)'}",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ermittelt PyInstaller-Excludes (schwere, ungenutzte Pakete im Build-Python).",
    )
    parser.add_argument(
        "--project", default=".", help="Projektwurzel (Default: aktuelles Verzeichnis)."
    )
    parser.add_argument(
        "--emit", choices=["pyinstaller", "list", "spec", "json", "check"],
        default="pyinstaller", help="Ausgabeformat (Default: pyinstaller).",
    )
    args = parser.parse_args(argv)

    project = Path(args.project).resolve()
    if not project.exists():
        print(f"[build-exclude-scanner] FEHLER: Projektpfad fehlt: {project}", file=sys.stderr)
        return 2

    result = compute_excludes(project)
    _report(result, project)
    excludes = result["excludes"]

    if args.emit == "pyinstaller":
        # Eine Zeile, direkt an den PyInstaller-Aufruf anzuhaengen (leer -> nichts).
        print(" ".join(f"--exclude-module {m}" for m in excludes))
    elif args.emit == "list":
        for m in excludes:
            print(m)
    elif args.emit == "spec":
        print("[" + ", ".join(repr(m) for m in excludes) + "]")
    elif args.emit == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    # 'check': nichts auf stdout (nur stderr-Report).
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
