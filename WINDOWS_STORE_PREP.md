# Windows Store Prep - ProFiler Suite

Stand: 2026-06-12

## Erledigt

- `store_package.json` angelegt
- `STORE_LISTING.md`, `PRIVACY_POLICY.md` und `SUPPORT.md` ergänzt
- App-Datenpfad auf Windows für Store-/Desktop-Readiness auf `%LOCALAPPDATA%\ProFilerSuite` umgestellt
- Legacy-Lese-Fallback für alte `~/.profiler_suite`-Dateien bleibt erhalten
- `scripts/check_store_readiness.py` prüft Store-Basismaterialien reproduzierbar
- `THIRD_PARTY_LICENSES.txt` liegt vor und dokumentiert PyMuPDF/Tesseract-Kontext

## Vor der Einreichung noch offen

- finalen EXE-/MSIX-Pfad festziehen
- dediziertes Screenshot-Set ergänzen
- WACK-Lauf dokumentieren
- Poppler-/Tesseract-Bündelung gegen Store-Paket final prüfen

## Technische Hinweise

- lokaler Konfigurationspfad: `%LOCALAPPDATA%\ProFilerSuite` (`LOCALAPPDATA\ProFilerSuite`)
- OCR bleibt lokaler Desktop-Workflow über Tesseract
- PDF-Redaktion kann PyMuPDF nutzen; AGPL-Hinweise bleiben sichtbar dokumentiert
- `runFullTrust` ist bewusst gesetzt, weil lokale Dateisystem-, OCR- und Tool-Workflows benötigt werden
