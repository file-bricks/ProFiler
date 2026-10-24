# Contributing to ProFiler Suite / Mitwirken an ProFiler Suite

[English](#english) | [Deutsch](#deutsch)

---

<a id="english"></a>
## English

Thank you for contributing to ProFiler Suite, a PySide6 desktop application for local file indexing, search, OCR, PDF workflows, and review of possible sensitive terms.

### Development principles

- Keep core file processing and indexes local by default. The optional module installer contacts GitHub when explicitly invoked; the application is not a network-egress filter.
- Treat privacy matching as a pattern-based aid, not a complete personal-data detector or a GDPR/compliance assessment.
- Preserve the documented workspace schema and inspect exports for unintended data before sharing. Schema filtering is not a claim that every export is anonymous or risk-free.
- Do not require administrator elevation for standard workflows. The application runs with the invoking user's permissions; do not describe this as process sandboxing.
- Keep PDF password settings out of persisted settings. Regression tests cover the current behavior for the two master-password settings; do not add real credentials to tests, logs, or fixtures.
- Keep version `15.0.2` frozen unless the maintainer changes the version-freeze instruction. Record unreleased maintenance changes under `## [Unreleased]` in `CHANGELOG.md`.

### Set up and test

Use Python 3.11 or newer, a local Git checkout, and a virtual environment. From the repository root:

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
python -m pytest -ra -v
ruff check .
python -m compileall -q .
git diff --check
```

The optional Excel workflows also need the `excel` extra. Some OCR/PDF workflows call host-installed Tesseract or Poppler tools; those external tools are not supplied by the Python test extra. Do not run tests against a user's real documents, settings, clipboard, keychain, or network services. Use disposable fixtures and temporary application-data paths.

Check the CI result for the exact commit before describing a change as passing. A local test result does not imply that all platforms or native package contents were tested.

### Licensing and security reports

The project license is in [LICENSE](LICENSE). [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) lists declared dependencies and upstream references; it is not a complete transitive inventory or a legal compatibility opinion. Review the actual components and terms before redistributing a binary.

Report suspected security issues privately as described in [SECURITY.md](SECURITY.md). No response or fix deadline is promised. Do not put credentials, private documents, or personal records in public issues or pull requests.

---

<a id="deutsch"></a>
## Deutsch

Vielen Dank für Beiträge zur ProFiler Suite, einer PySide6-Desktopanwendung für lokale Dateiindizierung und -suche, OCR, PDF-Arbeitsabläufe und Hinweise auf mögliche sensible Begriffe.

### Entwicklungsgrundsätze

- Die Kernabläufe zur Dateiverarbeitung und die Suchindizes bleiben standardmäßig lokal. Der optionale Modulinstaller kontaktiert GitHub, wenn er ausdrücklich gestartet wird; die Anwendung ist kein Filter für ausgehenden Netzwerkverkehr.
- Die Datenschutzampel ist eine regelbasierte Hilfe, kein vollständiger Detektor personenbezogener Daten und keine DSGVO- oder Compliance-Prüfung.
- Bewahren Sie das dokumentierte Workspace-Schema und prüfen Sie Exporte vor einer Weitergabe auf unbeabsichtigte Daten. Die Schemafilterung ist keine Garantie, dass jeder Export anonym oder risikofrei ist.
- Standardabläufe sollen keine Administratorrechte erfordern. Die Anwendung läuft mit den Berechtigungen des aufrufenden Benutzerkontos; dies bedeutet keine Prozess-Sandbox.
- PDF-Passwörter müssen aus den dauerhaft gespeicherten Einstellungen ausgeschlossen bleiben. Regressionstests prüfen das aktuelle Verhalten der beiden Masterpasswort-Einstellungen. Verwenden Sie keine echten Zugangsdaten in Tests, Protokollen oder Fixtures.
- Version `15.0.2` bleibt eingefroren, sofern der Maintainer die Versionssperre nicht ändert. Noch nicht veröffentlichte Pflege kommt unter `## [Unreleased]` in die `CHANGELOG.md`.

### Einrichten und testen

Verwenden Sie Python 3.11 oder neuer, einen lokalen Git-Klon und eine virtuelle Umgebung. Im Repository-Stammverzeichnis:

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
python -m pytest -ra -v
ruff check .
python -m compileall -q .
git diff --check
```

Die optionalen Excel-Abläufe benötigen zusätzlich das Extra `excel`. Einige OCR- und PDF-Abläufe starten Tesseract oder Poppler auf dem Host; diese externen Programme sind nicht im Python-Test-Extra enthalten. Führen Sie Tests nicht mit echten Nutzerdateien, Einstellungen, der Zwischenablage, einem Schlüsselbund oder Netzwerkdiensten aus. Verwenden Sie Wegwerf-Fixtures und temporäre Anwendungspfade.

Prüfen Sie das CI-Ergebnis des konkreten Commits, bevor Sie eine Änderung als bestanden bezeichnen. Ein lokales Testergebnis belegt keine Prüfung aller Plattformen oder nativen Paketbestandteile.

### Lizenzen und Sicherheitsmeldungen

Die Projektlizenz steht in [LICENSE](LICENSE). [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) führt deklarierte Abhängigkeiten und Upstream-Verweise auf; es ist weder ein vollständiges transitives Verzeichnis noch eine rechtliche Kompatibilitätsbewertung. Prüfen Sie vor einer Weitergabe als Binärdatei die tatsächlich enthaltenen Komponenten und Bedingungen.

Melden Sie vermutete Sicherheitsprobleme vertraulich wie in [SECURITY.md](SECURITY.md) beschrieben. Es wird keine Antwort- oder Behebungsfrist zugesagt. Veröffentlichen Sie keine Zugangsdaten, privaten Dokumente oder persönlichen Unterlagen in Issues oder Pull Requests.
