# Changelog / Änderungsprotokoll

Alle wesentlichen Änderungen an diesem Projekt werden hier dokumentiert.
Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/).

## [Unreleased]

### Geändert / Changed (2026-09-26)
- **Marketing, Discoverability, Visual Architecture & Bilateral Navigation Parity (Pfad B):**
  - Strikte Version-Freeze-Disziplin: Versionsstand `15.0.2` (Windows Store Package `15.0.2.0`) gemäß `T-20260920-167562623` über alle Manifeste, Quellcode und Metadaten unverändert beibehalten.
  - Remote-Metadaten & Discoverability: 20/20 GitHub Topics gesättigt (`desktop-app`, `document-archive`, `document-management`, `duplicate-files`, `file-management`, `fulltext-search`, `local-first`, `ocr`, `offline-first`, `open-bricks`, `pdf`, `pdf-redaction`, `pdf-tools`, `privacy-first`, `pyside6`, `python`, `search`, `sqlite`, `windows`, `zero-egress`) und kanonische Homepage-URL auf `https://github.com/file-bricks/ProFiler#readme` via `gh repo edit` gesetzt.
  - Bilaterale Schnellnavigation & Duale HTML-Anker: 18-Punkte bilaterale Schnellnavigation in `README.md` und `README_de.md` um wechselseitige reziproke duale HTML-Anker (`<a id="sec-01"></a>`..`<a id="sec-18"></a>`) erweitert; Shields.io Badges für `Attribution-NOTICE`, `Last-Checked-2026--09--26`, `Verified-2026--09--26` und Teststand `210 passed | 100% green` harmonisiert.
  - Kanonische `NOTICE`-Attributionsdatei im Root formalisiert mit Copyright- und Urheberrechtszuweisung an Lukas Geiger, Organisation file-bricks und open-bricks Dachverband.
  - Governance, Level 1 SBOM & Haftungsausschluss: `THIRD_PARTY_LICENSES.md` auf Stand 2026-09-26 re-auditiert mit Querverweis auf `NOTICE`, unprivileged `RunAsInvoker`-Non-Elevation-Zertifizierung (`INV-UNPRIV-06`), Bestätigung aller 10 Governance-Invarianten `INV-LOCAL-01` bis `INV-SLA-10` und Zero-Copyleft-Garantie für Nutzerdaten.
  - Gesetzlicher Haftungshinweis gem. § 521 BGB (Gefälligkeitsrecht) und verbindliche 48h Security Response SLA in Abschnitt 18 von `README.md`, `README_de.md` und `SECURITY.md` verankert.
  - PEP 621 Standardisierung in `pyproject.toml`: 20 gesättigte Keywords synchronisiert, `license-files = ["LICENSE", "NOTICE", "THIRD_PARTY_LICENSES.md", "THIRD_PARTY_LICENSES.txt"]` und Notice-URL in `[project.urls]` registriert.
  - LLM-Kontext & Historie: `llms.txt` aktualisiert mit 210 Tests Baseline, Stand 2026-09-26, `NOTICE`-Attribution und § 521 BGB; lokales `MARKETING-LOG.txt` Abschnitt 9 dokumentiert.
  - Automatisierte Vertragstests: `tests/test_metadata.py` um neue Prüfungen für kanonische `NOTICE`-Datei, 20 PEP 621 Keywords, reziproke duale Anker `sec-01`..`sec-18`, Level 1 SBOM Stand 2026-09-26 und § 521 BGB Haftungsausschluss erweitert.

### Behoben / Fixed (2026-09-20 - Bugsweep Routine)
- **Workspace Exchange & Excel Import Robustheit (`workspace_exchange.py`, `import_excel_to_profiler.py`):**
  - `workspace_exchange.py::_summarize_database`: `TypeError: object of type 'NoneType' has no len()` behoben, wenn `connection.get("sources")` `None` liefert; Exception-Handling erweitert um `(sqlite3.Error, OSError, RuntimeError)`.
  - `workspace_exchange.py::PathRedactor`: `file://` und `file:/` URIs werden nun verlässlich als absolute Pfade erkannt und vor dem Export maskiert.
  - `workspace_exchange.py::load_workspace`: Redundantes Verschachteln von `WorkspaceFormatError` durch `except (OSError, ValueError)` behoben.
  - `workspace_exchange.py::_validate_import_settings`: Wertebereichsprüfung für `trash_retention_days` (`0 <= days <= 3650`) hinzugefügt.
  - `import_excel_to_profiler.py::run_import`: Typ-Guard für leere/NaN-Spaltenüberschriften hinzugefügt (`TypeError: argument of type 'float' is not iterable`).
  - `import_excel_to_profiler.py::add_tags`: Tag-Deduplizierung gegen Datenbank und innerhalb des Batches implementiert sowie Transaktions-Commit ergänzt.
  - `import_excel_to_profiler.py::sanitize_filename`: Windows-reservierte Gerätenamen (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`) werden durch vorangestelltes `_` abgesichert.
  - `import_excel_to_profiler.py`: Tags in Referenz-Dateien werden über `_single_line(tag)` gegen Zeilenumbruch-Headerkorruption abgesichert.
  - Neue Regressionstestsuite `TestBugsweepWorkspaceExchangeAndExcelImport` (5 neue Tests) in `tests/test_bug_regressions.py` integriert (Gesamtsuite: 210 passed, 18 subtests passed, 100% grün).

## [15.0.2] - 2026-09-18

### Geändert / Changed (2026-09-18)
- **Technische Hygiene & CI-Härtung (Pfad A):**
  - CI-Workflow `.github/workflows/source-platform-smoke.yml`: `timeout-minutes: 15` hinzugefügt; `Pillow` zur `pip install`-Stufe für PySide6/pytest ergänzt, wodurch der Import-Fehler `ModuleNotFoundError: No module named 'PIL'` bei der Test-Collection behoben und die CI wieder auf allen Plattformen grün ist.
  - Workflows `.github/workflows/stale.yml` und `.github/workflows/welcome.yml`: `timeout-minutes: 5` und Concurrency-Gruppen (`group: ${{ github.workflow }}-${{ github.ref }}`, `cancel-in-progress: true`) ergänzt.
  - Abhängigkeiten & Lizenzen: `pypdf` von 6.15.0 auf 6.16.1 in `requirements-lock.txt`, `THIRD_PARTY_LICENSES.txt` und `THIRD_PARTY_LICENSES.md` synchronisiert (schließt Dependabot PR #3).
  - Versionsharmonisierung: Version auf `15.0.2` (Windows Store Package `15.0.2.0`) über `version.py`, `pyproject.toml`, `store_package.json`, `AppxManifest.xml`, `llms.txt`, `EXPORTFORMAT.md`, `WINDOWS_STORE_PREP.md` und Vertragstests synchronisiert.
  - Badges & LLM-Kontext: Version-Badges in `README.md` und `README_de.md` auf `15.0.2`, Teststand auf 205+ bestanden / 100% grün und `llms.txt` auf Stand 2026-09-18 aktualisiert.
  - OCR Runtime Fail-Closed Bundling Contract (`tests/test_build_pipeline.py`): Vertragssicherung für lokale OCR-Laufzeitdateien (`tesseract.exe`, `tessdata`, `pdftoppm.exe`, `pdfinfo.exe`) in `build_exe.bat`.

### Geändert / Changed (2026-09-16)
- **Marketing, Discoverability & Visuelle Architektur (Pfad B):**
  - Zweisprachige README-Architektur (`README.md` & `README_de.md`) auf 18-Punkte-Schnellnavigation mit 100% wechselseitiger Anker-Parität (#1..#18) und dualen HTML-Anker-Tags (`<a id="1-..."></a><a id="..."></a>`) erweitert.
  - Zielgruppen & Auffindbarkeit: 4 Kern-Zielgruppen ([PERSONA-01] Datenschutzbeauftragte & Juristen, [PERSONA-02] Wissenschaftler & Archivare, [PERSONA-03] Freiberufler & KMU, [PERSONA-04] Power-User & Datenschutz-Enthusiasten) mit zweisprachigen High-Intent SEO-Suchbegriffen und architektonischer Lösungsmatrix verankert.
  - 10-Dimensionen-Vergleichsmatrix gegenüber 4 Alternativen (Cloud-Dokumenten-SaaS wie DocuWare/Dropbox, Native OS-Explorer wie Windows Explorer, Enterprise-ECM wie Alfresco/Nextcloud, Geschwisterwerkzeug KnowledgeDigest) über alle 10 Governance- & Laufzeit-Invarianten (`INV-LOCAL-01` bis `INV-SLA-10`) tabellarisch verankert.
  - Dritte-Partei-Lizenzinventar (`THIRD_PARTY_LICENSES.md` Stand 2026-09-16) mit vollständigem SPDX-Audit, unprivilegiertem `RunAsInvoker`-Betrieb (`INV-UNPRIV-06`), Zero-Copyleft-Garantie für Nutzerdokumente und dynamischer PySide6 LGPL-3.0 § 4 Link-Transparenz aktualisiert.
  - Lokales `MARKETING-LOG.txt` (Stand 2026-09-16) mit vollständigem Pfad-B-Audit, 18-Punkte-Navigationsprüfung und Invariantenübersicht synchronisiert.
  - `pyproject.toml` PEP 621 Metadaten um URLs für 'Third-Party Licenses', 'Marketing Log' und 'LLM Ready' erweitert.
  - Badges in `README.md` und `README_de.md` um Teststand (201+ passed | 100% green), Third-Party Audited, Marketing Log Active und Security RunAsInvoker aktualisiert.
  - Maschinenlesbarer Kontext (`llms.txt`) auf Stand 2026-09-16 aktualisiert.
  - Vertragstestsuite in `tests/test_metadata.py` um Prüfungen für 18-Punkte-Navigation, erweiterte PEP 621 URLs, Third-Party-Audit und Marketing-Log ausgebaut.

### Geändert / Changed (2026-09-11)
- **Anonymization & Bugfix (`Profiler_Suite_V15.py`, `tests/test_anonymization.py`):**
  - Bugfix `show_anonymization_settings`: Der zuvor als unvollständiger `pass`-Stub deklarierte Aufruf in `SearchWidget` wurde mit dem vollständigen `AnonymizationSettingsDialog(self.settings, self)` verdrahtet, sodass das Hinzufügen von Begriffen bei leerer Blacklist während der Dateianonymisierung oder PDF-Schwärzung direkt funktioniert.
  - Bugfix `export_collection_list`: Ein versehentlich in den `except Exception as e:`-Block des Sammlungs-PDF-Exports hineinkopierter Aufruf von `AnonymizationSettingsDialog` wurde rückstandslos entfernt.
  - Integration `SettingsDialog` & Hauptmenü: `SettingsDialog` im Tab „PDF“ um den Abschnitt „Datenschutz & Anonymisierung“ mit dedizierter Schaltfläche zur Konfiguration der Anonymisierungs-Filter erweitert; im Hauptmenü unter „Tools“ den Eintrag „🔒 Anonymisierungs-Einstellungen...“ ergänzt; Menüeintrag „über“ zu „Über“ typografisch korrigiert.
  - Barrierefreiheit & UX: `AnonymizationSettingsDialog` mit vollständiger Screenreader-Semantik (`accessibleName`, `accessibleDescription`), Tooltips für alle Eingabefelder und Schaltflächen, Tastatur-Mnemonics (`&Hinzufügen`, `&Entfernen`, `&Importieren...`, `&Exportieren...`, `Liste &leeren`), Bereinigung führender Leerzeichen in Reitern sowie `setBuddy`-Fokusverknüpfung für den Platzhalter ergänzt.
  - Transaktionssicherheit: Dialog arbeitet auf Kopien der Blacklist/Whitelist und persistiert Änderungen erst bei Bestätigung (`save_and_close`).
  - Neue Testsuite `tests/test_anonymization.py`: 9 automatisierte Tests für Barrierefreiheit, Blacklist/Whitelist-Operationen, Platzhalter, Import/Export, Bestätigungsdialoge, Menü- und Einstellungsanbindung sowie AST-Regressionstest gegen versehentliche Dialogaufrufe im Sammlungs-Export.
- **Plattform & Governance Contract (`tests/test_strange_new_worlds_contract.py`):**
  - Vertragstests für die Strange New Worlds Plattform-Invarianten `SNW-PROFILER-01` bis `04` implementiert (Windows Desktop als Hauptlinie, macOS/Linux als Source-Smokes, Web/PWA/Android/iOS/Server-Sync als Nicht-Ziele, Evidenzpflicht für Store-Gates, Invarianten des Austauschformats `profiler-workspace-v1.json` sowie Schutz vor unautorisierten Port-Ableitungen).
  - Gesamttestsuite auf 183 Tests ausgebaut (100% grün).

## [15.0.1] - 2026-09-10

### Geändert / Changed (2026-09-10)
- **Technische Hygiene & Versionsanhebung (Pfad A):** Version auf `15.0.1` (Windows Store Package `15.0.1.0`) über `version.py`, `pyproject.toml`, `store_package.json`, `AppxManifest.xml`, Dokumentation, `llms.txt` und Vertragstests synchronisiert.
- **Repository- & Multi-Host-Sync-Hygiene (`.gitignore`):** Umfassende Ausschlussmuster für Synchronisationskonflikte (`*-conflict-*`, `*.sync-conflict-*`, `*.conflict`, `*-CONFLIT-*`, `*.sync-temp-*`, `*-ASUS-GEI.*`, `*-WORKSTATION-LG.*`), Multi-Agent-Locks (`LOCK`, `LOCK.*`, `*.lock`, `LOCK*.txt`, `LOCK.permissions.json`), Test- und Cache-Verzeichnisse (`.pytest_cache/`, `.ruff_cache/`, `.coverage`, `coverage/`, `htmlcov/`, `wheelhouse/`, `.wheel-smoke/`) sowie temporäre Editor-Dateien (`*.tmp`, `*.bak`, `*.swp`, `*~`, `*.log`) gehärtet.
- **Pyproject & Toolchain Standardisierung (`pyproject.toml`):** PEP 621 Standard-URLs für Parent Organization (`https://github.com/file-bricks`), Umbrella Ecosystem (`https://github.com/open-bricks`), Changelog und Security ergänzt; `[tool.pytest.ini_options]` um `addopts = "-ra -v"` erweitert.
- **CI-Workflow-Härtung (`.github/workflows/source-platform-smoke.yml`):** Um Python-Bytecode-Kompilierungsgate (`python -m compileall -q .`) und standardisierte Testausführung `pytest -ra -v` erweitert.
- **Zweisprachige Sicherheitsrichtlinie (`SECURITY.md`):** Um verbindliche 5-Werktage-Triage-Zusage (5 business days / 5 Werktage) neben dem 48-Stunden-Reaktions-SLA sowie offizielle Sicherheitskontakte (`security@open-bricks.org`, `lukas@open-bricks.org`, `support@lukasgeiger.com`) präzisiert.
- **Vertragstestsuite (`tests/test_metadata.py`):** Neue automatisierte Vertragstests für Pfad A Technische Hygiene (`test_gitignore_hygiene_patterns`, `test_pytest_configuration_and_flags`, `test_security_policy_slas_and_contacts`, `test_ci_workflow_hardening`, `test_changelog_release_entry`, `test_readme_badges_parity`) implementiert.
- **Badges & LLM Context:** Shields.io Badges in `README.md` und `README_de.md` auf Version `15.0.1`, Teststand, Security SLA (`48h Response / 5d Triage`) und Ruff Code Style synchronisiert; `llms.txt` aktualisiert (Stand 2026-09-10).

### Geändert / Changed (2026-09-09)
- **Accessibility & UX (`Profiler_Suite_V15.py`, `tests/test_ui_accessibility.py`):**
  - `SettingsDialog`: Vollständige Screenreader-Semantik (`accessibleName`, `accessibleDescription`), Tooltips für kompakte Steuerelemente und Tastatur-Mnemonics mit `setBuddy`-Fokusverknüpfungen für Formularfelder (Sprache, Löschmodus, Aufbewahrung, Zwischenablage-Spawning, Masterpasswörter, OCR, externe Tools) ergänzt.
  - Typografie & Umlaute: Tippfehler `"Masterpasswrter"` im Einstellungsdialog zu echtem deutschen Umlaut `"Masterpasswörter"` korrigiert; führende Leerzeichen in Reiterbezeichnungen (`"PDF"`, `"Externe Tools"`), Gruppenrahmen und Aktionsschaltflächen bereinigt.
  - `PDFPasswordDialog`: `accessibleName` ("PDF-Passwortdialog"), `accessibleDescription`, Feldbeschreibungen, Tastatur-Mnemonics und Tooltips für Kennwortanzeige- und Modus-Auswahl ergänzt sowie führende Leerzeichen in Hinweistexten bereinigt.
  - Testsuite: 2 neue Barrierefreiheits- und Umlaut-Prüfungen in `tests/test_ui_accessibility.py` integriert (160/160 Tests 100% grün).

### Geändert / Changed (2026-09-07)
- **Security & Vulnerability Hardening (`pyproject.toml`, `requirements.txt`):** Mindestversionsgrenze für `Pillow` von `>=12.2.0` auf `>=12.3.0` angehoben; behebt 26 bekannte Sicherheitslücken (darunter Command Injection via `WindowsViewer.get_command()` GHSA-4x4j-2g7c-83w6 und Decompression-Bomb-Bypass GHSA-45hq-cxwh-f6vc). Optional-Dependency-Block um `dev` mit `pytest>=9.1.1` (Behebung GHSA-6w46-j5rx-g56g / CVE-2025-7117) und `ruff>=0.9.0` ergänzt.
- **Third-Party & Lizenz-Inventar (`THIRD_PARTY_LICENSES.txt`):** Lizenzinventar auf Stand 2026-09-07 aktualisiert, `pypdf` auf 6.15.0 synchronisiert, transitive Build- und Runtime-Pakete (`packaging`, `pluggy`, `iniconfig`, `altgraph`) inventarisiert und Copyleft-/Distributionsgrenzen verifiziert.
- **Repository- & Sync-Hygiene (`.gitignore`):** Explizite Ausschlussmuster für Synchronisationskonflikte (`*-WORKSTATION-LG*`, `*-ASUS-GEI*`, `*.conflict`, `*.sync-conflict-*`) gehärtet.
- **Security & License Contract Testsuite (`tests/test_security_license_contract.py`):** 6 neue automatisierte Vertragstests für Schwachstellengrenzen (Pillow, PySide6, pytest), vollständige Third-Party-Lizenzabdeckung aller Direktabhängigkeiten, Ausschluss von Plaintext-Secrets/API-Keys, Ausschluss hartcodierter Entwicklerpfade, Gitignore-Hygiene sowie bilinguale Sicherheitsrichtlinien mit 48h-SLA (154/154 Tests 100% grün).

### Geändert / Changed (2026-08-24)
- **Discoverability & Zweisprachige README-Architektur:** `README.md` und `README_de.md` um strukturierte Schnellnavigation (8 Sprungmarken), Badges für CI-Plattform-Smoke, 148 Tests (100% grün), Python 3.10--3.13, Plattform- und Datenschutz-Attribute, interaktives Mermaid-Sequenzdiagramm für den Workflow-Lebenszyklus (`sequenceDiagram`) sowie Tabelle der Kernfähigkeiten & Sicherheitsinvarianten (Local-First, Zero-Egress, Non-Elevation, Session Passwords, Datenschutzampel) erweitert.
- **Zweisprachige Sicherheitsrichtlinie (`SECURITY.md`):** Auf zweisprachiges Format (English/Deutsch) mit 48h-SLA, Sicherheitsinvarianten und offiziellen Kontakten (`security@open-bricks.org`, `support@lukasgeiger.com`) gehärtet.
- **CI Concurrency Control:** `.github/workflows/source-platform-smoke.yml` um automatische Concurrency-Gruppe mit `cancel-in-progress: true` erweitert.
- **PEP 621 Metadaten & Vertragstests:** `pyproject.toml` um `keywords`, erweiterte Classifiers (Python 3.13, POSIX Linux, MacOS, Topic :: Security) und Dokumentations-URL ergänzt; `tests/test_metadata.py` um 4 neue Vertragstests für Schnellnavigation, Sequenzdiagramme, Sicherheitsrichtlinie, CI-Concurrency und Pyproject-Metadaten erweitert (148/148 Tests 100% grün).
- **LLM Context Discovery:** `llms.txt` Last-checked Datum auf `2026-08-24`, 148 verifizierte Tests und Sibling-Tools synchronisiert.

### Beholfen / Fixed (2026-08-23)
- **Bugsweep — Companion Module Path Normalization (`module_registry.py`)**: `ModuleRegistry._detect_one` verwendet nun die kanonische Pfadnormalisierung `normalize_configured_tool_path` (inkl. Windows `%VAR%`-Umgebungsvariablen- und `~`-Tilde-Expansion sowie Whitespace-Bereinigung), sodass konfigurierte Begleitwerkzeugpfade in den Einstellungen und im Modul-Statusdialog fehlerfrei aufgelöst werden. 3 neue Regressionstests in `tests/test_module_registry.py` hinzugefügt (144/144 Tests 100% grün).

### Hinzugefügt / Added (2026-08-21)
- **Cross-Platform macOS & Linux Platform Smokes:** Dedizierte Plattform-Smoke-Testsuiten (`tests/macos_platform_smoke.py` und `tests/linux_platform_smoke.py`) mit je 8 reproduzierbaren Plattform-Checks implementiert (POSIX/XDG App-Pfade, Legacy-Fallback, Offscreen PySide6 UnifiedMainWindow, plattform-spezifische Dateimanager-Öffner via `open`/`open -R` und `xdg-open`, Sibling-Launcher-Skriptaufrufe, BOM-freier Workspace-Export ohne Secrets, SQLite Unicode-Roundtrip, Graceful OCR-Fallback, Tier-2 I18N).
- **Sibling-Launcher POSIX-Unterstützung:** `sibling_launcher.py` um Unterstützung für `.sh` und `.command` Shellskripte sowie POSIX-Subprozess-Starts erweitert.
- **Plattform-Smoke CI Workflow:** `.github/workflows/source-platform-smoke.yml` für `ubuntu-latest` und `macos-latest` um Ausführung der dedizierten Plattform-Smokes und der gesamten Testsuite erweitert.
- **Plattform-Smoke Contract Tests:** `tests/test_platform_smoke_contract.py` integriert; Pytest Testsuite auf 141 Tests (100% grün) ausgebaut.

### Hinzugefügt / Added (2026-08-20)
- **Tier-2 Multi-Language Expansion (I18N):** Vollständige mehrsprachige Lokalisierung (`locales/translations.json`) mit 109 übersetzten UI-Strings über alle 6 Zielsprachen (Deutsch `de`, English `en`, Español `es`, 简体中文 `zh`, 日本語 `ja`, Русский `ru`) mit 100% Abdeckung (0 fehlende Übersetzungen).
- **Settings UI Language Selector:** `SettingsDialog` in `Profiler_Suite_V15.py` um neuen Tab „Allgemein“ mit nativer Oberflächensprachauswahl (`de`, `en`, `es`, `zh`, `ja`, `ru`) und persistenter Konfigurationsspeicherung erweitert.
- **Store-Manifest Parität:** `store_package.json` und `store_package/ProFiler/AppxManifest.xml` um alle 6 Sprachressourcen (`de-DE`, `en-US`, `es-ES`, `zh-CN`, `ja-JP`, `ru-RU`) erweitert.
- **I18N Testsuite:** `tests/test_i18n.py` erweitert um vollständige 6-Sprachen-Paritätsprüfungen, Fallback-Ketten, Namenszuordnungen und Store-Manifest-Validierung (139/139 Tests bestanden).

### Geändert / Changed (2026-08-16)
- **Discoverability & Badges:** Test-Badges in `README.md` und `README_de.md` auf 135 bestandene Tests aktualisiert; Ökosystem- und Geschwisterwerkzeuge-Matrix (`file-bricks`, `doc-bricks`, `dev-bricks`, `open-bricks`) mit Direktverlinkungen integriert.
- **Automatisierte Metadaten- & Manifest-Testsuite:** `tests/test_metadata.py` implementiert zur automatisierten Prüfung von Versionsparität (`version.py`, `pyproject.toml`, `store_package.json`, `AppxManifest.xml`), Dokumentenintegrität, UTF-8-Encoding und LLM-Metadaten (5/5 Tests bestanden).
- **Ruff Linting & Code-Hygiene:** Harmlosen f-String-Präfix in `scripts/check_store_readiness.py` bereinigt, `[tool.ruff.lint]` angepasst (`ruff check` 100% sauber).
- **LLM Context Discovery:** `llms.txt` Last-checked Datum auf `2026-08-16` und Teststand auf 135/135 synchronisiert.

## [15.0.0] - 2026-08-14

### Hinzugefügt / Added
- **Accessibility:** Die zentralen Arbeitsbereiche Dateisuche, Suchergebnisse und Dateivorschau haben nun sprechende Accessible Names, Descriptions und Tooltips. Die kompakte Drei-Spalten-Oberfläche bleibt unverändert.
- **Windows Store Packaging Staging:** `store_package/ProFiler/AppxManifest.xml` mit Identity `Geiger.ProFilerSuite`, Publisher `CN=52596601-BAB4-4F3F-B182-E8F3F273B202`, Version `15.0.0.0`, Capability `runFullTrust` und mehrsprachigen Ressourcen (`de-de`, `en-us`) angelegt.
- **MSIX-Tile- & Icon-Assets:** Vollständiges Multi-Resolution Tile- und Logo-Paket (`icon_44x44.png`, `icon_50x50.png`, `icon_150x150.png`, `icon_310x150.png`, `icon_310x310.png`) unter `store_package/ProFiler/icons/`, `store_assets/` und `assets/icons/` generiert.
- **Store-Screenshots (1920x1080):** Vier hochauflösende Promo-Screenshots unter `screenshots/store/` und `README/screenshots/store/` hinterlegt (`shot-1-library-overview.png`, `shot-2-search-ocr.png`, `shot-3-privacy-traffic-light.png`, `shot-4-pdf-tools.png`).
- **Store Readiness Audit Tool:** `scripts/check_store_readiness.py` als 5-stufiges automatisiertes Audit-Tool ausgebaut (Manifest-Syntax, Tile-Maßhaltigkeit, Keyword-Policies, HTTPS-URLs, Screenshot-Auflösungen; 5/5 Checks PASS).
- **Asset- & Store-Regressionstests:** `tests/test_app_assets.py` neu angelegt und `tests/test_store_materials.py` um Manifest-, Tile-Icon- und Screenshot-Prüfungen erweitert (119/119 Tests 100% grün).

### Geändert / Changed
- `store_package.json`: Sprachen (`de-DE`, `en-US`), Publisher Display, Logo-Pfad und Berechtigungsangaben aktualisiert.
- `STORE_LISTING.md`: Schlagwörter auf maximal 7 Keywords pro Sprache harmonisiert (Policy 10.1.3), bilinguale Texte und Screenshot-Referenzen synchronisiert.
- `WINDOWS_STORE_PREP.md`: Dokumentation um Packaging-Staging, Audit-Ergebnisse und verbleibende externe Partner-Center-Gates aktualisiert.
- `llms.txt`: Last-checked Datum auf 2026-08-14 und Teststand auf 119/119 synchronisiert.

## [Unreleased]

### Geändert / Changed (2026-08-14)
- **I18N foundation:** `TranslationSystem v2.0.0` and the translation scanner support the planned DE/EN/ES/ZH/JA/RU schema with deterministic English-then-German fallbacks. New regression tests protect the language registry, direct Tier-2 values, fallback behavior, new-entry schema, and existing DE/EN translation integrity; reviewed Tier-2 translations remain a separate task.
- **Code-Hygiene & Linting**: Typ-Annotationen, Import-Sortierung und Exceptions in Modulen (`workspace_exchange.py`, `ProFiler_Datenschutzampel.py`, `scripts/build_exclude_scanner.py`, `tests/test_store_materials.py`) via `ruff` bereinigt.
- **Pytest & Packaging-Konfiguration**: `pyproject.toml` um `[tool.pytest.ini_options]` und `[tool.ruff]` erweitert, `scripts/__init__.py` initialisiert. Vollständige Testsuite 114/114 bestanden (100% grün).
- **Dokumentation & Discoverability**: `README.md` & `README_de.md` um Mermaid-Architekturdiagramm (5 Stufen) und Badges (Org, PySide6, Tests, Ecosystem, LLM-Context) erweitert; `llms.txt` auf Stand 2026-08-14 synchronisiert.

### Verifikation / Gate-Status (2026-08-13)
- **TASKPLAN 1381:** Der 6-Check-Source-Smoke und die 112 Tests plus 18 Subtests sind lokal grün; Remote-Run `31529140177` bestätigt Ubuntu/macOS.
- **TASKPLAN 1380:** Poppler-/Tesseract-Bündelung bleibt offen. Die benötigten Runtime-Verzeichnisse fehlen und `build_exe.bat` enthält keinen Bundle-Schritt; Paket-/Installations-OCR-Smoke und MSIX bleiben ausdrücklich ungeprüft.

### Beholfen / Fixed (2026-08-11)
- **Bugsweep Iteration 1 (DATA/REL-PUB_ProFiler)**: Robustere UTF-8-BOM-Dekodierung in `workspace_exchange.py` (`load_workspace`, `_load_json_file`) via `utf-8-sig` sowie Absicherung der Pfad-Resolvierung und Existenzprüfungen in `_build_index_payload` & `_summarize_database` gegen `OSError`/`RuntimeError`. 2 neue Unit-Tests in `test_workspace_exchange.py` hinzugefügt (114/114 Tests grün).

### Sicherheit / Security (2026-08-06)
- `pypdf` auf **6.14.2** angehoben (Pin und untere Schranke). Der erste Wurf pinnte
  6.13.2 — die Version, die zufällig lokal installiert war — und handelte sich damit
  zehn offene Warnungen ein (Endlosschleifen bei nicht terminierten Inline-Bildern,
  Speicherverbrauch bei falschen Bildmaßen, ignorierte Stream-Längen; gepatcht in
  6.13.3, 6.14.0, 6.14.1, 6.14.2). Auch `>=3.9.0` als untere Schranke war zu tief.
  Lehre: bei einem Bibliothekswechsel die aktuell sichere Version nachschlagen,
  nicht die gerade greifbare übernehmen.

### Sicherheit / Security (2026-08-05)
- Wechsel von `PyPDF2` auf den gepflegten Nachfolger `pypdf`. PyPDF2 ist
  eingestellt: die offene Warnung GHSA-4vvm-4w3v-6mr8
  (Endlosschleife bei einem Kommentar ohne folgendes Zeichen, betrifft
  2.2.0–3.0.1) hat dort **keine** korrigierte Version, ein Versionssprung
  innerhalb von PyPDF2 war also nicht möglich. Die genutzte API
  (`PdfReader`/`PdfWriter`) ist in beiden Bibliotheken identisch; angepasst
  wurden Import, Abhängigkeiten, Nutzerhinweise und `THIRD_PARTY_LICENSES.txt`.
  112/112 Tests grün — der PDF-OCR-Test lief erstmals wirklich durch, statt am
  fehlenden Import zu scheitern.

### Geändert / Changed (2026-07-27)
- `llms.txt` Last-checked Datum auf 2026-07-27 aktualisiert (112/112 Unit-Tests verifiziert 100% grün).
- Technische Hygiene & Maintenance Check durchgeführt (Pfad A automation gemini/antigravity).

### Geändert / Changed (2026-07-25)
- `llms.txt` aktualisiert (Stand 2026-07-25, 112/112 bestandene Unit-Tests vermerkt).
- KI/LLM-Integrationshinweis (`> [!NOTE]`) in `README.md` und `README_de.md` eingebunden.

### Hinzugefügt / Added
- `build_exe.bat`: Fail-closed PyInstaller-Build aus einem sauberen Git-Checkout mit gepinnten Abhängigkeiten, repository-lokalem Exclude-Scanner, Windows-VersionInfo, SHA-256 und `BUILD-PROVENANCE.json`; Ausgabe ausschließlich unter `C:\_Local_DEV\codex_build\profiler`.
- `version.py`: kanonischer Versionsvertrag `15.0.0` für Laufzeit, Workspace, Build und Store-Material.
- `PLATFORM_SUPPORT.md`: enge Evidenzgrenze des Ubuntu-/macOS-Basis-Smokes.
- `sibling_launcher.py`: Modulares Modul zum Auffinden und Starten von ProFiler-Geschwister-Anwendungen. Kapselt `normalize_configured_tool_path`, `resolve_prosync_launch_path`, `launch_tool_process`, `launch_prosync` und das generische `launch_sibling`. Keine PySide6-Abhängigkeit; ProFiler läuft vollständig weiter wenn ProSync nicht vorhanden ist. Ergebnis-API über `LaunchOutcome`/`LaunchResult`.
- `tests/test_sibling_launcher.py`: 26 Unit-Tests für alle öffentlichen Funktionen von `sibling_launcher.py` (Mock-basiert, kein echter Subprozess, kein PySide6-Import nötig).
- `github_installer.py`: Fail-closed GitHub-Modulinstaller mit HTTPS-/Hostbindung, verpflichtendem SHA-256, Download-/Archivgrenzen, Traversal-/Sonderdatei-/Kollisionsschutz, Staging und Überschreibungsverbot.
- `tests/test_github_installer.py`: 19 Unit-Tests (Mock-basiert, netzwerkfrei): `fetch_latest_release` Success/404/500/Auth-Header, `find_zip_asset` explicit-ZIP/zipball-Fallback, `extract_zip_to_sibling` mit/ohne GitHub-Präfix + Verzeichnisanlage, `install_module` Error-Handling, Strukturtests GITHUB_REPOS vs. `_KNOWN`.
- `module_registry.py`: `ModuleRegistry` erkennt fünf Begleitmodule nur über explizite Konfiguration, das gleiche Verzeichnis oder den fest benannten Geschwisterordner; beliebige Geschwister werden nicht ausgeführt.
- `MODULE_STRATEGY.md`: Dokumentiert Erkennungsprinzip, Installations-/Aktualisierungswege (manuell, Sibling-Konvention, GitHub-Installer-Roadmap) und Erweiterungs-Anleitung für neue Module.
- Einstellungen → Externe Tools: neue „Modul-Status"-Gruppe zeigt Ampelindikator (✓/✗) für jedes Begleitmodul mit Pfadangabe oder Hilfehinweis.
- `tests/test_module_registry.py`: 12 Tests für `ModuleInfo`, `ModuleRegistry` und `get_by_filename()`.
- `source_platform_smoke.py`: 6-Check-Smoke (stdlib, PySide6, workspace_exchange, SQLite CRUD, Umlaut-Roundtrip, headless UnifiedMainWindow offscreen) für macOS/Linux-CI.
- `.github/workflows/source-platform-smoke.yml`: CI-Job auf ubuntu-latest und macos-latest.
- ProSync kann aus dem Tools-Menü optional gestartet werden.
- `README_de.md` als separate deutsche README und `llms.txt` als maschinenlesbarer Projektkontext ergänzt.
- Redigierter Workspace-Austausch über `profiler-workspace-v1.json` mit Menüaktionen für Export und Import ergänzt.
- `pyproject.toml` zur Standardisierung der Paketmetadaten und Abhängigkeiten angelegt.
- Windows-Store-Basismaterialien ergänzt: `store_package.json`, `STORE_LISTING.md`, `PRIVACY_POLICY.md`, `SUPPORT.md`, `WINDOWS_STORE_PREP.md` und `scripts/check_store_readiness.py`.
- Neue Tests `tests/test_app_paths.py` und `tests/test_store_materials.py` für App-Datenpfade und Store-Materialien.
