"""Contract tests for macOS and Linux platform smoke suites."""

from __future__ import annotations

import tests.linux_platform_smoke as linux_smoke
import tests.macos_platform_smoke as macos_smoke


def test_macos_platform_smoke_suite() -> None:
    """Run full suite of macOS platform smoke checks."""
    macos_smoke.test_macos_app_paths_and_legacy_fallback()
    macos_smoke.test_macos_offscreen_window_creation()
    macos_smoke.test_macos_file_and_folder_open_dispatch()
    macos_smoke.test_macos_sibling_launcher()
    macos_smoke.test_macos_workspace_exchange_without_bom_or_secrets()
    macos_smoke.test_macos_sqlite_and_umlaut_roundtrip()
    macos_smoke.test_macos_ocr_and_pdf_fallback()
    macos_smoke.test_macos_tier2_i18n_resolution()


def test_linux_platform_smoke_suite() -> None:
    """Run full suite of Linux platform smoke checks."""
    linux_smoke.test_linux_app_paths_and_legacy_fallback()
    linux_smoke.test_linux_offscreen_window_creation()
    linux_smoke.test_linux_file_and_folder_open_dispatch()
    linux_smoke.test_linux_sibling_launcher()
    linux_smoke.test_linux_workspace_exchange_without_bom_or_secrets()
    linux_smoke.test_linux_sqlite_and_umlaut_roundtrip()
    linux_smoke.test_linux_ocr_and_pdf_fallback()
    linux_smoke.test_linux_tier2_i18n_resolution()
