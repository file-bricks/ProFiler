from __future__ import annotations

from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_app_icon_ico_and_png_exist() -> None:
    ico_root = PROJECT_ROOT / "ICO.ico"
    assert ico_root.exists()
    with Image.open(ico_root) as img:
        assert img.format == "ICO"

    icon_png = PROJECT_ROOT / "assets" / "icon.png"
    assert icon_png.exists()
    with Image.open(icon_png) as img:
        assert img.format == "PNG"

    app_ico = PROJECT_ROOT / "assets" / "app_icon.ico"
    assert app_ico.exists()
    with Image.open(app_ico) as img:
        assert img.format == "ICO"

    favicon = PROJECT_ROOT / "assets" / "favicon.ico"
    assert favicon.exists()
    with Image.open(favicon) as img:
        assert img.format == "ICO"


def test_all_store_package_icons() -> None:
    icons_dir = PROJECT_ROOT / "store_package" / "ProFiler" / "icons"
    assert icons_dir.exists()

    expected_sizes = {
        "icon_44x44.png": (44, 44),
        "icon_50x50.png": (50, 50),
        "icon_150x150.png": (150, 150),
        "icon_310x150.png": (310, 150),
        "icon_310x310.png": (310, 310),
    }

    for name, size in expected_sizes.items():
        p = icons_dir / name
        assert p.exists()
        with Image.open(p) as img:
            assert img.format == "PNG"
            assert img.size == size


def test_all_store_assets_and_aliases() -> None:
    store_assets_dir = PROJECT_ROOT / "store_assets"
    assert store_assets_dir.exists()

    expected_files = [
        ("icon_44x44.png", (44, 44)),
        ("icon_50x50.png", (50, 50)),
        ("icon_150x150.png", (150, 150)),
        ("icon_310x150.png", (310, 150)),
        ("icon_310x310.png", (310, 310)),
        ("Square44x44Logo.png", (44, 44)),
        ("Square50x50Logo.png", (50, 50)),
        ("StoreLogo.png", (50, 50)),
        ("Square150x150Logo.png", (150, 150)),
        ("Wide310x150Logo.png", (310, 150)),
        ("Square310x310Logo.png", (310, 310)),
    ]

    for name, size in expected_files:
        p = store_assets_dir / name
        assert p.exists()
        with Image.open(p) as img:
            assert img.format == "PNG"
            assert img.size == size
