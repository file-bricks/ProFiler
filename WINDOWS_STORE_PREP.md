# Windows Store Prep - ProFiler Suite

Stand: 2026-07-22

## Erledigt

- `store_package.json` angelegt
- `STORE_LISTING.md`, `PRIVACY_POLICY.md` und `SUPPORT.md` ergänzt
- App-Datenpfad auf Windows für Store-/Desktop-Readiness auf `%LOCALAPPDATA%\ProFilerSuite` umgestellt
- Legacy-Lese-Fallback für alte `~/.profiler_suite`-Dateien bleibt erhalten
- `scripts/check_store_readiness.py` prüft ausschließlich die lokale Materialbasis reproduzierbar
- `THIRD_PARTY_LICENSES.txt` bildet die direkten Runtime-Abhängigkeiten manifestnah ab
- Privacy- und Support-Links zeigen auf den realen Default-Branch `master`

## Vor der Einreichung noch offen

- signiertes MSIX/AppxManifest erzeugen und Installationspfad prüfen
- dediziertes Screenshot-Set ergänzen
- WACK-Lauf dokumentieren
- Poppler-/Tesseract-Bündelung gegen Store-Paket prüfen und OCR/PDF real smoken
- Publisher-/Zertifikats- und Partner-Center-Readback durchführen

## Technische Hinweise

- lokaler Konfigurationspfad: `%LOCALAPPDATA%\ProFilerSuite` (`LOCALAPPDATA\ProFilerSuite`)
- OCR bleibt lokaler Desktop-Workflow über Tesseract
- PDF-Redaktion kann PyMuPDF nutzen; AGPL-Hinweise bleiben sichtbar dokumentiert
- `runFullTrust` ist bewusst gesetzt, weil lokale Dateisystem-, OCR- und Tool-Workflows benötigt werden

`STORE MATERIAL BASELINE: OK` bedeutet ausdrücklich nicht Store-, MSIX- oder
WACK-Freigabe. Diese externen Gates bleiben offen.
