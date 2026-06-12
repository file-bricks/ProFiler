"""Shared application data paths for ProFiler."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping, Optional


APP_DATA_DIRNAME = "ProFilerSuite"
LEGACY_CONFIG_DIRNAME = ".profiler_suite"


def app_data_dir(
    platform: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    home: Optional[Path] = None,
) -> Path:
    """Return the preferred local app-data directory for ProFiler."""
    platform = platform or os.name
    env = env or os.environ
    home = home or Path.home()

    if platform == "nt":
        local_appdata = env.get("LOCALAPPDATA")
        if local_appdata:
            return Path(local_appdata) / APP_DATA_DIRNAME
        return home / "AppData" / "Local" / APP_DATA_DIRNAME

    return home / LEGACY_CONFIG_DIRNAME


def legacy_config_dir(home: Optional[Path] = None) -> Path:
    """Return the legacy config directory used before store-readiness cleanup."""
    return (home or Path.home()) / LEGACY_CONFIG_DIRNAME


def config_path(
    filename: str,
    platform: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    home: Optional[Path] = None,
) -> Path:
    """Return the preferred config/data file path for a given filename."""
    return app_data_dir(platform=platform, env=env, home=home) / filename


def resolve_read_path(
    filename: str,
    platform: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    home: Optional[Path] = None,
) -> Path:
    """Return the best existing read path, falling back to the legacy folder."""
    preferred = config_path(filename, platform=platform, env=env, home=home)
    legacy = legacy_config_dir(home=home) / filename

    if preferred.exists():
        return preferred
    if legacy.exists():
        return legacy
    return preferred
