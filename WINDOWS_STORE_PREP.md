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

## Verifikation 2026-08-13 — Package-Gate Task 1380

Die Paket-/OCR-Voraussetzungen wurden read-only geprüft:

- `tesseract_portable/`, `tessdata/`, `poppler/`, `dist/` und `release/` sind
  im Checkout nicht vorhanden.
- `requirements.txt` und `requirements-lock.txt` enthalten nur die Python-
  Wrapper (`pytesseract`, `pdf2image` usw.), keine Tesseract-/Poppler-Binärdaten.
- `build_exe.bat` nimmt nur `locales` als `--add-data` auf; es gibt keinen
  Tesseract-/Poppler-Bundle-Schritt.
- `python scripts/check_store_readiness.py` bestätigt `STORE MATERIAL BASELINE:
  OK (nicht einreichungsbereit)` und führt Paket-Bundle sowie installierte
  OCR/PDF-Smokes weiterhin als offen.

Ergebnis: Task 1380 bleibt mit diesem konkreten Restpunkt offen. Für eine
Abnahme fehlen autorisierte Runtime-Artefakte, ein sauberer Build-Checkout, ein
erzeugtes Paket und ein echter installierter OCR/PDF-Smoke. Es wurde kein
Release- oder Store-Status behauptet.

## Technische Hinweise

- lokaler Konfigurationspfad: `%LOCALAPPDATA%\ProFilerSuite` (`LOCALAPPDATA\ProFilerSuite`)
- OCR bleibt lokaler Desktop-Workflow über Tesseract
- PDF-Redaktion kann PyMuPDF nutzen; AGPL-Hinweise bleiben sichtbar dokumentiert
- `runFullTrust` ist bewusst gesetzt, weil lokale Dateisystem-, OCR- und Tool-Workflows benötigt werden

`STORE MATERIAL BASELINE: OK` bedeutet ausdrücklich nicht Store-, MSIX- oder
WACK-Freigabe. Diese externen Gates bleiben offen.
