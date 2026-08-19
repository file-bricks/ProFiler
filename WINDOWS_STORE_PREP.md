# Windows Store Prep - ProFiler Suite

Stand: 2026-08-14

## Erledigt

- `store_package.json` mit vollständigen Metadaten (`languages: ["de-DE", "en-US"]`, Logo-Pfad, Publisher-ID, AGPL-Lizenz) gepflegt
- Windows Store Packaging Staging unter `store_package/ProFiler/AppxManifest.xml` mit Identity `Geiger.ProFilerSuite`, Publisher `CN=52596601-BAB4-4F3F-B182-E8F3F273B202`, Version `15.0.0.0`, Capability `runFullTrust` und mehrsprachigen Ressourcen (`de-de`, `en-us`) angelegt
- Vollständiges Set an hochauflösenden MSIX-Tile- und Logo-Assets generiert:
  - `icon_44x44.png` (Square44x44Logo / Square71x71Logo)
  - `icon_50x50.png` (Square50x50Logo / StoreLogo)
  - `icon_150x150.png` (Square150x150Logo)
  - `icon_310x150.png` (Wide310x150Logo)
  - `icon_310x310.png` (Square310x310Logo)
  - gespiegelt in `store_package/ProFiler/icons/`, `store_assets/` und `assets/icons/`
- Vier hochauflösende Store-Screenshots (1920x1080) unter `screenshots/store/` und `README/screenshots/store/` hinterlegt (`shot-1-library-overview.png`, `shot-2-search-ocr.png`, `shot-3-privacy-traffic-light.png`, `shot-4-pdf-tools.png`)
- `STORE_LISTING.md` mit bilingualen Texten (DE/EN), maximal 7 Schlagwörtern pro Sprache (Policy 10.1.3), Feature-Listen und Screenshot-Referenzen synchronisiert
- `scripts/check_store_readiness.py` als 5-stufiges automatisiertes Readiness-Audit-Tool ausgebaut (5/5 Checks PASS)
- Testsuiten in `tests/test_store_materials.py` und `tests/test_app_assets.py` mit 100% Abdeckung verankert
- App-Datenpfad auf Windows für Store-/Desktop-Readiness auf `%LOCALAPPDATA%\ProFilerSuite` umgestellt
- Legacy-Lese-Fallback für alte `~/.profiler_suite`-Dateien bleibt erhalten
- `THIRD_PARTY_LICENSES.txt` bildet die direkten Runtime-Abhängigkeiten manifestnah ab
- Privacy- und Support-Links zeigen auf den realen Default-Branch `master`

## Vor der Einreichung im Partner Center (externe Gates)

- Signiertes MSIX-Paket im Partner Center hochladen
- WACK-Zertifizierungslauf mit der signierten MSIX-Binärdatei durchführen
- Poppler-/Tesseract-Bündelung gegen Store-Paket im Release-Workflow validieren
- Partner-Center-Zertifikatsabgleich abschließen

## Technische Hinweise

- lokaler Konfigurationspfad: `%LOCALAPPDATA%\ProFilerSuite` (`LOCALAPPDATA\ProFilerSuite`)
- OCR bleibt lokaler Desktop-Workflow über Tesseract
- PDF-Redaktion kann PyMuPDF nutzen; AGPL-Hinweise bleiben sichtbar dokumentiert
- `runFullTrust` ist bewusst gesetzt, weil lokale Dateisystem-, OCR- und Tool-Workflows benötigt werden
