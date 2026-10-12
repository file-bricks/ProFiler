"""Führt das Windows App Certification Kit (WACK) für ProFiler Suite aus oder wertet vorhandene Reports aus."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Sequence
import uuid
import xml.etree.ElementTree as ET

try:
    import ctypes
except ImportError:
    ctypes = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APPCERT = Path(r"C:\Program Files (x86)\Windows Kits\10\App Certification Kit\appcert.exe")
WACK_REPORT_PREFIX = "wack_report_"
SYNTHETIC_PREFLIGHT_PREFIX = "wack_preflight_"
PREFLIGHT_STATUS_PREFIX = "store_preflight_"


@dataclass(frozen=True)
class WackSummary:
    report: str
    overall_result: str
    requirement_count: int
    pass_count: int
    fail_count: int
    warning_count: int


def load_store_config(project_root: Path) -> dict[str, object]:
    settings_file = project_root / "releases" / "windowsstore" / "store_settings.json"
    if settings_file.exists():
        try:
            return json.loads(settings_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    pkg_file = project_root / "store_package.json"
    if pkg_file.exists():
        try:
            return json.loads(pkg_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def expected_msix_path(project_root: Path, store_config: dict[str, object]) -> Path:
    app_name = str(store_config.get("msix_name") or "ProFiler.msix")
    candidate_dirs = [
        project_root / "releases" / "windowsstore",
        project_root / "releases",
        project_root / "dist",
    ]
    for directory in candidate_dirs:
        candidate = directory / app_name
        if candidate.exists():
            return candidate
    return candidate_dirs[0] / app_name


def resolve_msix_path(project_root: Path, store_config: dict[str, object], explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.expanduser().resolve()
    return expected_msix_path(project_root, store_config).resolve()


def resolve_report_path(project_root: Path, report_dir: Path | None, explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.expanduser().resolve()
    base_dir = (report_dir or (project_root / "releases" / "windowsstore" / "test_reports")).expanduser().resolve()
    run_id = datetime.now().strftime("%Y%m%dT%H%M%S%f") + f"_{uuid.uuid4().hex}"
    return base_dir / f"{WACK_REPORT_PREFIX}{run_id}.xml"


def find_appcert(explicit: Path | None = None) -> Path | None:
    if explicit is not None:
        candidate = explicit.expanduser().resolve()
        return candidate if candidate.is_file() else None
    if DEFAULT_APPCERT.is_file():
        return DEFAULT_APPCERT
    discovered = shutil.which("appcert.exe")
    return Path(discovered).resolve() if discovered else None


def is_windows_admin() -> bool:
    if ctypes is None or not hasattr(ctypes, "windll"):
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def build_reset_command(appcert: Path) -> list[str]:
    return [str(appcert), "reset"]


def build_test_command(appcert: Path, msix_path: Path, report_path: Path) -> list[str]:
    return [
        str(appcert),
        "test",
        "-appxpackagepath",
        str(msix_path),
        "-reportoutputpath",
        str(report_path),
    ]


def build_finalize_command(appcert: Path, report_path: Path) -> list[str]:
    return [str(appcert), "finalizereport", "-reportfilepath", str(report_path)]


def parse_wack_report(report_path: Path) -> WackSummary:
    if report_path.name.casefold().startswith(SYNTHETIC_PREFLIGHT_PREFIX):
        raise ValueError(
            f"{report_path.name} verwendet einen historischen Preflight-Dateinamen; "
            "die Herkunft ist damit nicht verifiziert und wird nicht als WACK-Nachweis akzeptiert."
        )
    try:
        marker_text = report_path.read_text(encoding="utf-8", errors="replace")[:2048]
    except OSError as exc:
        raise ValueError(f"WACK-Report kann nicht gelesen werden: {report_path}") from exc
    if "SYNTHETIC NOT WACK" in marker_text.upper():
        raise ValueError(f"{report_path.name} ist ausdrücklich als synthetisch und nicht als WACK markiert.")

    tree = ET.parse(report_path)
    root = tree.getroot()
    root_name = root.tag.rsplit("}", 1)[-1].casefold()
    if root_name != "report":
        raise ValueError(f"{report_path.name} hat kein erwartetes WACK-Report-Root-Element.")
    overall = root.attrib.get("OVERALL_RESULT") or root.attrib.get("OverallResult") or "UNKNOWN"
    requirements = root.findall(".//REQUIREMENT") or root.findall(".//Requirement")
    if overall.upper() not in {"PASS", "FAIL", "WARNING", "WARN"}:
        raise ValueError(f"{report_path.name} enthält keinen auswertbaren WACK-Gesamtstatus.")
    if not requirements:
        raise ValueError(f"{report_path.name} enthält keine WACK-Anforderungen.")
    pass_count = 0
    fail_count = 0
    warning_count = 0

    for requirement in requirements:
        result = (requirement.attrib.get("RESULT") or requirement.attrib.get("Result") or "").upper()
        if result == "PASS":
            pass_count += 1
        elif result == "FAIL":
            fail_count += 1
        elif result in {"WARNING", "WARN"}:
            warning_count += 1

    return WackSummary(
        report=str(report_path),
        overall_result=overall.upper(),
        requirement_count=len(requirements),
        pass_count=pass_count,
        fail_count=fail_count,
        warning_count=warning_count,
    )


def write_summary(
    summary: WackSummary,
    destination: Path,
    exit_code: int = 0,
    *,
    appcert_invoked_by_this_run: bool,
) -> None:
    data = asdict(summary)
    data["report_type"] = "wack_xml_summary"
    data["appcert_invoked_by_this_run"] = appcert_invoked_by_this_run
    data["exit_code"] = exit_code
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate_preflight_status(
    project_root: Path,
    report_dir: Path | None = None,
    msix: Path | None = None,
    appcert_path: Path | None = None,
) -> Path:
    """Write a static preflight record; this function never creates a WACK report."""
    target_dir = (report_dir or (project_root / "releases" / "windowsstore" / "test_reports")).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    json_path = target_dir / f"{PREFLIGHT_STATUS_PREFIX}{timestamp}.json"
    store_config = load_store_config(project_root)
    msix_path = resolve_msix_path(project_root, store_config, msix)
    appcert = find_appcert(appcert_path)
    has_msix = msix_path.is_file() and msix_path.stat().st_size > 0
    payload = {
        "schema": "profiler.windows-store-preflight.v1",
        "report_type": "static_preflight",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "NOT_RUN",
        "wack_executed": False,
        "static_checks": {
            "appcert_available": "PRESENT" if appcert is not None else "MISSING",
            "msix_available": "PRESENT" if has_msix else "MISSING",
        },
        "note": (
            "This is a static preparation record only. It does not contain WACK results, "
            "and no package certification test was executed."
        ),
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return json_path


def format_command(command: Sequence[str]) -> str:
    return subprocess.list2cmdline(list(command))


def run_command(command: Sequence[str], log_path: Path) -> int:
    completed = subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n$ {format_command(command)}\n")
        if completed.stdout:
            handle.write(completed.stdout)
            if not completed.stdout.endswith("\n"):
                handle.write("\n")
        if completed.stderr:
            handle.write(completed.stderr)
            if not completed.stderr.endswith("\n"):
                handle.write("\n")
        handle.write(f"Exit code: {completed.returncode}\n")
    if completed.stdout:
        print(completed.stdout.rstrip())
    if completed.stderr:
        print(completed.stderr.rstrip(), file=sys.stderr)
    return completed.returncode


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Führt WACK für das lokale ProFiler-MSIX aus.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT, help="Projektordner, Standard: aktuelles Repo.")
    parser.add_argument("--msix", type=Path, help="Pfad zum MSIX, Standard: releases/windowsstore/ProFiler.msix.")
    parser.add_argument("--appcert", type=Path, help="Pfad zu appcert.exe, wenn nicht im Standardpfad.")
    parser.add_argument("--report-dir", type=Path, help="Report-Verzeichnis, Standard: releases/windowsstore/test_reports.")
    parser.add_argument("--report-path", type=Path, help="Expliziter XML-Reportpfad.")
    parser.add_argument("--parse-report", type=Path, help="Vorhandenen WACK-XML-Report auswerten und JSON schreiben.")
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Schreibt einen statischen Vorbereitungsstatus; startet WACK nicht.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Pfade und WACK-Befehl anzeigen, nichts ausführen.")
    parser.add_argument("--allow-non-admin", action="store_true", help="WACK trotz fehlender Admin-Erkennung starten.")
    parser.add_argument("--skip-reset", action="store_true", help="appcert reset vor dem Test auslassen.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    if args.preflight:
        json_path = generate_preflight_status(args.project_root, args.report_dir, args.msix, args.appcert)
        print(f"Statischer Vorbereitungsstatus: {json_path}")
        print("Status: NOT_RUN (WACK wurde nicht gestartet; dies ist kein Zertifizierungsbericht).")
        return 0

    if args.parse_report:
        report_path = args.parse_report.expanduser().resolve()
        try:
            summary = parse_wack_report(report_path)
        except (ValueError, ET.ParseError) as exc:
            print(f"[BLOCKER] {exc}", file=sys.stderr)
            return 2
        summary_path = report_path.with_suffix(".json")
        summary_exit_code = 1 if summary.fail_count > 0 or summary.overall_result == "FAIL" else 0
        write_summary(
            summary,
            summary_path,
            exit_code=summary_exit_code,
            appcert_invoked_by_this_run=False,
        )
        print(json.dumps(asdict(summary), ensure_ascii=False, indent=2))
        print(f"WACK-Zusammenfassung: {summary_path}")
        return summary_exit_code

    project_root = args.project_root.resolve()
    store_config = load_store_config(project_root)
    msix_path = resolve_msix_path(project_root, store_config, args.msix)
    report_path = resolve_report_path(project_root, args.report_dir, args.report_path)
    log_path = report_path.with_suffix(".log")
    summary_path = report_path.with_suffix(".json")
    appcert = find_appcert(args.appcert)

    print(f"MSIX: {msix_path}")
    print(f"WACK-Report: {report_path}")
    print(f"WACK-Log: {log_path}")
    if appcert is None:
        print("AppCert: nicht gefunden")
    else:
        print(f"AppCert: {appcert}")
        print(f"Befehl: {format_command(build_test_command(appcert, msix_path, report_path))}")

    if args.dry_run:
        return 0

    if report_path.name.casefold().startswith(SYNTHETIC_PREFLIGHT_PREFIX):
        print(
            "[BLOCKER] Der historische Preflight-Dateiname ist für einen neuen WACK-Lauf nicht zulässig.",
            file=sys.stderr,
        )
        return 2

    existing_artifacts = [path for path in (report_path, log_path, summary_path) if path.exists()]
    if existing_artifacts:
        for path in existing_artifacts:
            print(f"[BLOCKER] Ausgabe existiert bereits und bleibt unverändert: {path}", file=sys.stderr)
        return 2

    errors: list[str] = []
    if appcert is None:
        errors.append("appcert.exe fehlt. Windows App Certification Kit installieren oder --appcert setzen.")
    if not msix_path.exists() or msix_path.stat().st_size == 0:
        errors.append(f"MSIX fehlt oder ist leer: {msix_path}")
    if not args.allow_non_admin and not is_windows_admin():
        errors.append("WACK sollte als Administrator laufen. Nutze eine erhöhte PowerShell oder --allow-non-admin.")

    if errors:
        for error in errors:
            print(f"[BLOCKER] {error}", file=sys.stderr)
        return 2

    assert appcert is not None
    report_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        f"WACK gestartet: {datetime.now().isoformat(timespec='seconds')}\nMSIX: {msix_path}\nReport: {report_path}\n",
        encoding="utf-8",
    )

    if not args.skip_reset:
        reset_exit = run_command(build_reset_command(appcert), log_path)
        if reset_exit != 0:
            print(f"[BLOCKER] appcert reset ist mit Exitcode {reset_exit} fehlgeschlagen.", file=sys.stderr)
            return reset_exit

    exit_code = run_command(build_test_command(appcert, msix_path, report_path), log_path)
    if exit_code != 0:
        print(
            f"[BLOCKER] appcert test ist mit Exitcode {exit_code} fehlgeschlagen; "
            "ein vorhandener Report wird nicht als erfolgreicher Lauf gewertet.",
            file=sys.stderr,
        )
        return exit_code

    if not report_path.is_file() or report_path.stat().st_size == 0:
        print("[BLOCKER] WACK hat keinen neuen, nichtleeren XML-Report erzeugt.", file=sys.stderr)
        return 1

    finalize_exit = run_command(build_finalize_command(appcert, report_path), log_path)
    if finalize_exit != 0:
        print(f"[BLOCKER] appcert finalizereport ist mit Exitcode {finalize_exit} fehlgeschlagen.", file=sys.stderr)
        return finalize_exit

    try:
        summary = parse_wack_report(report_path)
    except (ValueError, ET.ParseError) as exc:
        print(f"[BLOCKER] WACK-Report kann nicht ausgewertet werden: {exc}", file=sys.stderr)
        return 2
    write_summary(
        summary,
        summary_path,
        exit_code=exit_code,
        appcert_invoked_by_this_run=True,
    )
    print(
        "WACK-Ergebnis: "
        f"{summary.overall_result}, {summary.pass_count} PASS, "
        f"{summary.fail_count} FAIL, {summary.warning_count} WARNING"
    )
    print(f"WACK-Zusammenfassung: {summary_path}")
    if summary.fail_count > 0 or summary.overall_result == "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
