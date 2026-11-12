"""Pytest runner for individual source platform smoke checks."""

from __future__ import annotations

import tests.source_platform_smoke as smoke


def test_supported_desktop_target() -> None:
    smoke.test_supported_desktop_target()


def test_app_paths_and_sandbox() -> None:
    smoke.test_app_paths_and_sandbox()


def test_workspace_exchange_unicode_roundtrip() -> None:
    smoke.test_workspace_exchange_unicode_roundtrip()


def test_sqlite_and_umlaut_roundtrip() -> None:
    smoke.test_sqlite_and_umlaut_roundtrip()


def test_ocr_and_pdf_fallback() -> None:
    smoke.test_ocr_and_pdf_fallback()


def test_tier2_i18n_resolution() -> None:
    smoke.test_tier2_i18n_resolution()


def test_translation_parity_check() -> None:
    smoke.test_translation_parity_check()
