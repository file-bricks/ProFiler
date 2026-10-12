"""Isolate tests before application modules are imported.

The environment, Python audit guards and Qt test paths are installed at pytest
collection time. The audit hook blocks Python-level mutations outside the
sandbox, reads from the real ProFiler config folders, network operations and
child-process launches. Native C/Qt file operations may bypass Python audit
events, so Qt's standard paths are redirected separately to test mode.
"""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import sys


_HOST_TEMP = Path(tempfile.gettempdir()).resolve()
_REPO_ROOT = Path(__file__).resolve().parents[1]
_REAL_LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")).resolve()
_REAL_USERPROFILE = Path(os.environ.get("USERPROFILE", Path.home())).resolve()
_PROTECTED_READ_ROOTS = (
    _REAL_LOCALAPPDATA / "ProFilerSuite",
    _REAL_USERPROFILE / ".profiler_suite",
)
_configured = os.environ.get("PROFILER_TEST_SANDBOX")
if _configured:
    _SANDBOX = Path(_configured).expanduser().resolve()
else:
    _SANDBOX = Path(tempfile.mkdtemp(prefix="ProFiler-TestSandbox-", dir=_HOST_TEMP)).resolve()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except (OSError, RuntimeError, ValueError):
        return False


if _is_within(_SANDBOX, _REPO_ROOT):
    raise RuntimeError("PROFILER_TEST_SANDBOX must be outside the source checkout")
if _SANDBOX == _HOST_TEMP or _SANDBOX.parent != _HOST_TEMP:
    raise RuntimeError("PROFILER_TEST_SANDBOX must be one task-specific directory below host temp")
if _configured and not _SANDBOX.name.startswith("ProFiler-TestSandbox-"):
    raise RuntimeError("PROFILER_TEST_SANDBOX must use the ProFiler-TestSandbox- task prefix")
if any(_is_within(_SANDBOX, root) or _is_within(root, _SANDBOX) for root in _PROTECTED_READ_ROOTS):
    raise RuntimeError("PROFILER_TEST_SANDBOX must not overlap a real ProFiler config folder")

_DIRS = {
    "LOCALAPPDATA": _SANDBOX / "localappdata",
    "APPDATA": _SANDBOX / "roaming",
    "USERPROFILE": _SANDBOX / "userprofile",
    "HOME": _SANDBOX / "home",
    "TEMP": _SANDBOX / "tmp",
    "TMP": _SANDBOX / "tmp",
    "TMPDIR": _SANDBOX / "tmp",
    "PROGRAMDATA": _SANDBOX / "programdata",
    "XDG_CONFIG_HOME": _SANDBOX / "xdg-config",
    "XDG_CACHE_HOME": _SANDBOX / "xdg-cache",
    "XDG_DATA_HOME": _SANDBOX / "xdg-data",
    "PROFILER_QT_RUNTIME": _SANDBOX / "qt-runtime",
    "PROFILER_QT_APP_CONFIG": _SANDBOX / "qt-app-config",
    "PROFILER_QT_APP_DATA": _SANDBOX / "qt-app-data",
    "PROFILER_QT_CACHE": _SANDBOX / "qt-cache",
    "PROFILER_QT_GENERIC_CACHE": _SANDBOX / "qt-generic-cache",
    "PROFILER_QT_GENERIC_DATA": _SANDBOX / "qt-generic-data",
}
for _name, _path in _DIRS.items():
    _path.mkdir(parents=True, exist_ok=True)
    os.environ[_name] = str(_path)
_home_drive, _home_path = os.path.splitdrive(str(_DIRS["USERPROFILE"]))
if os.name == "nt":
    os.environ["HOMEDRIVE"] = _home_drive
    os.environ["HOMEPATH"] = _home_path or "\\"
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["PROFILER_TEST_SANDBOX"] = str(_SANDBOX)
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
tempfile.tempdir = str(_DIRS["TEMP"])


def _is_os_null_device(value: object) -> bool:
    """Recognize only the platform null device for an explicit open sink."""
    if isinstance(value, int):
        return False
    try:
        raw_path = os.fsdecode(os.fspath(value))
    except (TypeError, ValueError, OSError):
        return False
    if os.path.normcase(os.path.normpath(raw_path)) == os.path.normcase(
        os.path.normpath(os.devnull)
    ):
        return True
    return os.name == "nt" and raw_path.replace("/", "\\").casefold() in {
        "nul:",
        "\\\\.\\nul",
    }


def _path_is_sandboxed(value: object) -> bool:
    if isinstance(value, int):
        return True
    try:
        raw_path = os.fsdecode(os.fspath(value))
    except (TypeError, ValueError, OSError):
        return False
    path = Path(raw_path)
    return _is_within(path, _SANDBOX)


def _path_is_protected_profile(value: object) -> bool:
    if isinstance(value, int):
        return False
    try:
        path = Path(os.fsdecode(os.fspath(value)))
    except (TypeError, ValueError, OSError):
        return False
    return any(_is_within(path, root) for root in _PROTECTED_READ_ROOTS)


_WRITE_FLAGS = (
    os.O_WRONLY
    | os.O_RDWR
    | os.O_CREAT
    | os.O_TRUNC
    | os.O_APPEND
    | getattr(os, "O_TEMPORARY", 0)
)
_WRITE_EVENTS = {
    "os.chmod": (0,),
    "os.chown": (0,),
    "os.link": (0, 1),
    "os.mkdir": (0,),
    "os.remove": (0,),
    "os.rmdir": (0,),
    "os.symlink": (1,),
    "os.truncate": (0,),
    "os.unlink": (0,),
    "os.utime": (0,),
    "os.rename": (0, 1),
    "os.replace": (0, 1),
}
_PROFILE_READ_EVENTS = {
    "os.listdir": (0,),
    "os.scandir": (0,),
}
_BLOCKED_EVENTS = {
    "os.exec",
    "os.fork",
    "os.forkpty",
    "os.posix_spawn",
    "os.spawn",
    "os.startfile",
    "os.system",
    "socket.bind",
    "socket.connect",
    "socket.getaddrinfo",
    "socket.gethostbyaddr",
    "socket.gethostbyname",
    "socket.getnameinfo",
    "subprocess.Popen",
    "winreg.CreateKey",
    "winreg.CreateKeyEx",
    "winreg.DeleteKey",
    "winreg.DeleteKeyEx",
    "winreg.DeleteValue",
    "winreg.FlushKey",
    "winreg.LoadKey",
    "winreg.SaveKey",
    "winreg.SetValue",
    "winreg.SetValueEx",
}


def _sandbox_audit(event: str, args: tuple[object, ...]) -> None:
    if event == "open":
        path = args[0] if args else None
        mode = args[1] if len(args) > 1 else None
        flags = args[2] if len(args) > 2 else 0
        writes = isinstance(mode, str) and any(char in mode for char in "wax+")
        writes = writes or (isinstance(flags, int) and bool(flags & _WRITE_FLAGS))
        if writes and not (_path_is_sandboxed(path) or _is_os_null_device(path)):
            raise PermissionError(f"test sandbox blocked file write outside sandbox: {path!s}")
        if not writes and _path_is_protected_profile(path):
            raise PermissionError("test sandbox blocked read from a real ProFiler config folder")
        return

    if event in _WRITE_EVENTS:
        indexes = _WRITE_EVENTS[event]
        paths = [args[index] for index in indexes if index < len(args)]
        if any(not _path_is_sandboxed(path) for path in paths):
            raise PermissionError(f"test sandbox blocked filesystem mutation: {event}")
        return

    if event in _PROFILE_READ_EVENTS:
        indexes = _PROFILE_READ_EVENTS[event]
        paths = [args[index] for index in indexes if index < len(args)]
        if any(_path_is_protected_profile(path) for path in paths):
            raise PermissionError("test sandbox blocked directory read from a real ProFiler config folder")
        return

    if event in _BLOCKED_EVENTS:
        raise PermissionError(f"test sandbox blocked external side effect: {event}")


sys.addaudithook(_sandbox_audit)


def _qt_sandbox_path_map(QStandardPaths):
    paths = {
        QStandardPaths.AppConfigLocation: _DIRS["PROFILER_QT_APP_CONFIG"],
        QStandardPaths.AppDataLocation: _DIRS["PROFILER_QT_APP_DATA"],
        QStandardPaths.CacheLocation: _DIRS["PROFILER_QT_CACHE"],
        QStandardPaths.GenericCacheLocation: _DIRS["PROFILER_QT_GENERIC_CACHE"],
        QStandardPaths.GenericDataLocation: _DIRS["PROFILER_QT_GENERIC_DATA"],
        QStandardPaths.HomeLocation: _DIRS["HOME"],
        QStandardPaths.RuntimeLocation: _DIRS["PROFILER_QT_RUNTIME"],
        QStandardPaths.TempLocation: _DIRS["TEMP"],
    }
    if hasattr(QStandardPaths, "AppLocalDataLocation"):
        paths[QStandardPaths.AppLocalDataLocation] = _DIRS["PROFILER_QT_APP_DATA"]
    return paths


def _redirect_qt_location(location, sandbox_paths, original):
    sandbox_path = sandbox_paths.get(location)
    return str(sandbox_path) if sandbox_path is not None else original(location)


def _redirect_qt_locations(location, sandbox_paths, original):
    sandbox_path = sandbox_paths.get(location)
    return [str(sandbox_path)] if sandbox_path is not None else original(location)


def pytest_configure(config):
    """Redirect Qt paths and guard process-launch APIs when Qt is available."""
    try:
        from PySide6.QtCore import QProcess, QStandardPaths
        from PySide6.QtGui import QDesktopServices
    except ImportError:
        return

    QStandardPaths.setTestModeEnabled(True)
    _original_writable_location = QStandardPaths.writableLocation
    _original_standard_locations = QStandardPaths.standardLocations
    _qt_sandbox_paths = _qt_sandbox_path_map(QStandardPaths)

    def _sandbox_qt_location(location):
        return _redirect_qt_location(
            location, _qt_sandbox_paths, _original_writable_location
        )

    def _sandbox_qt_locations(location):
        return _redirect_qt_locations(
            location, _qt_sandbox_paths, _original_standard_locations
        )

    QStandardPaths.writableLocation = staticmethod(_sandbox_qt_location)
    QStandardPaths.standardLocations = staticmethod(_sandbox_qt_locations)
    _qt_locations = (
        QStandardPaths.AppConfigLocation,
        QStandardPaths.AppDataLocation,
        QStandardPaths.CacheLocation,
        QStandardPaths.GenericCacheLocation,
        QStandardPaths.GenericDataLocation,
        QStandardPaths.HomeLocation,
        QStandardPaths.TempLocation,
        QStandardPaths.RuntimeLocation,
    )
    for _location in _qt_locations:
        _qt_path = QStandardPaths.writableLocation(_location)
        if _qt_path and not _is_within(Path(_qt_path), _SANDBOX):
            raise RuntimeError(f"Qt writable path escaped test sandbox: {_qt_path}")

    def _deny_qprocess(*args, **kwargs):
        raise PermissionError("test sandbox blocked QProcess launch")

    QProcess.start = _deny_qprocess
    QProcess.startDetached = _deny_qprocess
    QDesktopServices.openUrl = _deny_qprocess


def pytest_report_header(config):
    return f"ProFiler test sandbox: {_SANDBOX}"
