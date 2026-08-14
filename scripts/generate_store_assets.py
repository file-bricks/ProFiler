#!/usr/bin/env python3
"""
generate_store_assets.py - Generate multi-resolution Windows Store tile assets and screenshots for ProFiler.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def generate_icons():
    ico_path = PROJECT_ROOT / "ICO.ico"
    with Image.open(ico_path) as base_img:
        base = base_img.convert("RGBA")
        
        # Target directories
        dirs = [
            PROJECT_ROOT / "store_package" / "ProFiler" / "icons",
            PROJECT_ROOT / "store_assets",
            PROJECT_ROOT / "assets" / "icons",
            PROJECT_ROOT / "assets"
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            
        # Standard tile sizes
        sizes = {
            "icon_44x44.png": (44, 44),
            "icon_50x50.png": (50, 50),
            "icon_150x150.png": (150, 150),
            "icon_310x310.png": (310, 310),
        }
        
        for name, size in sizes.items():
            resized = base.resize(size, Image.Resampling.LANCZOS)
            for d in [PROJECT_ROOT / "store_package" / "ProFiler" / "icons", PROJECT_ROOT / "store_assets", PROJECT_ROOT / "assets" / "icons"]:
                resized.save(d / name, format="PNG")
                
        # 310x150 Wide Tile (Centered icon on 310x150 canvas)
        wide = Image.new("RGBA", (310, 150), (0, 0, 0, 0))
        icon_fit = base.resize((130, 130), Image.Resampling.LANCZOS)
        offset_x = (310 - 130) // 2
        offset_y = (150 - 130) // 2
        wide.paste(icon_fit, (offset_x, offset_y), icon_fit)
        
        for d in [PROJECT_ROOT / "store_package" / "ProFiler" / "icons", PROJECT_ROOT / "store_assets", PROJECT_ROOT / "assets" / "icons"]:
            wide.save(d / "icon_310x150.png", format="PNG")

        # Aliases in store_assets
        aliases = {
            "Square44x44Logo.png": "icon_44x44.png",
            "Square50x50Logo.png": "icon_50x50.png",
            "StoreLogo.png": "icon_50x50.png",
            "Square150x150Logo.png": "icon_150x150.png",
            "Wide310x150Logo.png": "icon_310x150.png",
            "Square310x310Logo.png": "icon_310x310.png",
        }
        for alias_name, src_name in aliases.items():
            src_file = PROJECT_ROOT / "store_assets" / src_name
            alias_file = PROJECT_ROOT / "store_assets" / alias_name
            with Image.open(src_file) as im:
                im.save(alias_file, format="PNG")

        # assets/icon.png and app_icon.ico
        base.save(PROJECT_ROOT / "assets" / "icon.png", format="PNG")
        base.save(PROJECT_ROOT / "assets" / "app_icon.ico", format="ICO")
        
        favicon = base.resize((32, 32), Image.Resampling.LANCZOS)
        favicon.save(PROJECT_ROOT / "assets" / "favicon.ico", format="ICO")
        
        print("Generated all store tile icons and assets successfully.")


def generate_store_screenshots():
    main_shot_path = PROJECT_ROOT / "screenshots" / "main.png"
    if not main_shot_path.exists():
        main_shot_path = PROJECT_ROOT / "README" / "screenshots" / "main.png"

    with Image.open(main_shot_path) as base_ui_img:
        ui_raw = base_ui_img.convert("RGBA")
        
        # 1920x1080 Canvas configuration
        canvas_w, canvas_h = 1920, 1080
        
        # Color palette (Dark theme / slate blue / teal accents matching ProFiler brand)
        bg_color = (24, 28, 36, 255)
        card_bg = (34, 40, 52, 255)
        border_color = (60, 72, 90, 255)
        accent_color = (37, 95, 99, 255) # teal
        
        # Screenshot variations
        shots = [
            {
                "filename": "shot-1-library-overview.png",
                "title": "ProFiler Suite — Lokale Dokumentenverwaltung & Suche",
                "subtitle": "Volltextsuche, Dateibaum und strukturierte Metadaten ohne Cloud-Zwang",
                "tag": "DOKUMENTENVERWALTUNG",
                "tag_color": (52, 152, 219, 255),
            },
            {
                "filename": "shot-2-search-ocr.png",
                "title": "Tesseract OCR & Deep Search Engine",
                "subtitle": "Vollständige Textextraktion aus Scans, Bildern und verschachtelten PDF-Dokumenten",
                "tag": "OCR & DEEP SEARCH",
                "tag_color": (155, 89, 182, 255),
            },
            {
                "filename": "shot-3-privacy-traffic-light.png",
                "title": "Integrierte Datenschutzampel & DSGVO-Prüfung",
                "subtitle": "Automatische Erkennung sensibler Schlüsselwörter, IBANs und vertraulicher Inhalte",
                "tag": "DATENSCHUTZAMPEL",
                "tag_color": (46, 204, 113, 255),
            },
            {
                "filename": "shot-4-pdf-tools.png",
                "title": "PDF-Werkzeuge, Schwärzung & Workspace-Export",
                "subtitle": "Seitenextraktion, Entschlüsselung, Redaktion und sicherer Austausch",
                "tag": "PDF-WORKFLOWS & EXPORT",
                "tag_color": (230, 126, 34, 255),
            },
        ]
        
        target_dirs = [
            PROJECT_ROOT / "screenshots" / "store",
            PROJECT_ROOT / "README" / "screenshots" / "store"
        ]
        for td in target_dirs:
            td.mkdir(parents=True, exist_ok=True)

        for spec in shots:
            img = Image.new("RGBA", (canvas_w, canvas_h), bg_color)
            draw = ImageDraw.Draw(img)
            
            # Draw header bar
            header_h = 110
            draw.rectangle([(0, 0), (canvas_w, header_h)], fill=(18, 22, 28, 255))
            draw.line([(0, header_h), (canvas_w, header_h)], fill=border_color, width=2)
            
            # Badge pill
            badge_x, badge_y = 60, 24
            badge_w, badge_h = 240, 28
            draw.rounded_rectangle([(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)], radius=6, fill=spec["tag_color"])
            
            # Load default font or simple text
            # Draw tag text
            draw.text((badge_x + 16, badge_y + 6), spec["tag"], fill=(255, 255, 255, 255))
            
            # Title & subtitle
            draw.text((badge_x, badge_y + 36), spec["title"], fill=(240, 245, 250, 255))
            draw.text((badge_x, badge_y + 58), spec["subtitle"], fill=(160, 175, 195, 255))
            
            # UI mockup frame placement
            # Resize UI to fit within (1800, 910)
            ui_w = 1760
            aspect = ui_raw.height / ui_raw.width
            ui_h = int(ui_w * aspect)
            if ui_h > 900:
                ui_h = 900
                ui_w = int(ui_h / aspect)
                
            ui_resized = ui_raw.resize((ui_w, ui_h), Image.Resampling.LANCZOS)
            
            pos_x = (canvas_w - ui_w) // 2
            pos_y = header_h + 25 + (920 - ui_h) // 2
            
            # Shadow / card behind UI
            draw.rounded_rectangle([(pos_x - 8, pos_y - 8), (pos_x + ui_w + 8, pos_y + ui_h + 8)], radius=10, fill=card_bg, outline=border_color, width=2)
            
            # Paste UI
            img.paste(ui_resized, (pos_x, pos_y), ui_resized if ui_resized.mode == "RGBA" else None)
            
            for td in target_dirs:
                img.save(td / spec["filename"], format="PNG")
                
        print("Generated all 4 store screenshots successfully.")


if __name__ == "__main__":
    generate_icons()
    generate_store_screenshots()
