from __future__ import annotations

from pathlib import Path

from app_paths import app_data_dir, config_path, legacy_config_dir, resolve_read_path


def test_windows_app_data_uses_localappdata() -> None:
    path = app_data_dir(
        platform="nt",
        env={"LOCALAPPDATA": r"C:\Users\User\AppData\Local"},
        home=Path(r"C:\Users\User"),
    )
    assert path == Path(r"C:\Users\User\AppData\Local\ProFilerSuite")


def test_non_windows_keeps_legacy_hidden_dir() -> None:
    path = app_data_dir(platform="posix", env={}, home=Path("/home/lukas"))
    assert path == Path("/home/lukas/.profiler_suite")


def test_resolve_read_path_prefers_legacy_when_new_file_missing(tmp_path: Path) -> None:
    home = tmp_path / "home"
    legacy = legacy_config_dir(home=home)
    legacy.mkdir(parents=True)
    legacy_file = legacy / "settings.json"
    legacy_file.write_text("{}", encoding="utf-8")

    resolved = resolve_read_path("settings.json", platform="nt", env={}, home=home)
    assert resolved == legacy_file


def test_config_path_targets_localappdata_on_windows() -> None:
    path = config_path(
        "connections.json",
        platform="nt",
        env={"LOCALAPPDATA": r"C:\Users\User\AppData\Local"},
        home=Path(r"C:\Users\User"),
    )
    assert path == Path(r"C:\Users\User\AppData\Local\ProFilerSuite\connections.json")
