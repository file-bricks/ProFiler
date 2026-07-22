# Beitragsrichtlinie / Contributing Guide

## Deutsch

Vielen Dank für Ihr Interesse an ProFiler Suite.

### Beiträge

1. Melden Sie Fehler als GitHub-Issue mit reproduzierbaren Schritten.
2. Diskutieren Sie größere Funktionsänderungen vorab in einem Issue.
3. Erstellen Sie für Codeänderungen einen kleinen Feature-Branch und Pull Request.
4. Fügen Sie passende Regressionstests hinzu und dokumentieren Sie sichtbare Änderungen.

### Lokaler Einstieg

```bash
git clone https://github.com/file-bricks/ProFiler.git
cd ProFiler
python -m pip install -r requirements.txt
python -m pytest -q
python Profiler_Suite_V15.py
```

### Regeln

- Python 3.10 oder neuer, UTF-8 und PEP-8-orientierter Stil
- keine fest codierten Benutzerpfade, Tokens, Passwörter oder privaten Fixtures
- sichtbare deutsche Texte mit echten Umlauten
- keine Release-, Store- oder Plattformbehauptung ohne reproduzierbaren Nachweis
- Beiträge werden unter der bestehenden AGPL-3.0-only-Lizenz eingereicht

---

## English

Thank you for your interest in ProFiler Suite.

### Contributions

1. Report bugs as GitHub issues with reproducible steps.
2. Discuss larger feature changes in an issue first.
3. Use a focused feature branch and pull request for code changes.
4. Add regression tests and document user-visible changes.

### Local setup

```bash
git clone https://github.com/file-bricks/ProFiler.git
cd ProFiler
python -m pip install -r requirements.txt
python -m pytest -q
python Profiler_Suite_V15.py
```

### Rules

- Python 3.10 or newer, UTF-8, and PEP-8-oriented style
- no hard-coded user paths, tokens, passwords, or private fixtures
- no release, Store, or platform claim without reproducible evidence
- contributions are submitted under the existing AGPL-3.0-only license
