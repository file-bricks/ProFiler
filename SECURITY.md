# Security Policy / Sicherheitsrichtlinie

[English](#english) | [Deutsch](#deutsch)

---

<a name="english"></a>
## English

### Supported Versions

| Version | Supported | Status |
| ------- | --------- | ------ |
| `15.0.x` | :white_check_mark: | Active release stream |
| `< 15.0` | :x: | End of Life / Unsupported |

### Security Invariants & Design Principles

1. **100% Local-First & Zero-Egress**: ProFiler operates strictly locally on your workstation. It performs no remote network telemetry, does not upload files to cloud servers, and requires no online account.
2. **Session-Only Secrets**: PDF passwords and temporary decryption credentials are held only in volatile process memory and are never serialized to configuration files or logs.
3. **Redacted Data Exchange**: Exporting workspace snapshots automatically strips host-specific absolute paths, system tokens, and untracked file metadata.
4. **Non-Elevation**: The application operates with standard user privileges under `%LOCALAPPDATA%\ProFilerSuite` (or standard XDG directories on POSIX) without requiring administrative elevation.

### Reporting a Vulnerability

If you discover a security vulnerability, please report it privately:

1. **GitHub Security Advisories**: Navigate to the [Security tab](https://github.com/file-bricks/ProFiler/security/advisories) of this repository and select **Report a vulnerability**.
2. **Direct Contact**: If GitHub reporting is unavailable, contact the security team via `security@open-bricks.org` or `support@lukasgeiger.com`.

**Please do not open public issues for security vulnerabilities.**

We acknowledge receipt of vulnerability reports within **48 hours** and provide regular progress updates until a patch is released.

### Security Updates

Security fixes are released promptly upon confirmation and documented in [CHANGELOG.md](CHANGELOG.md).

---

<a name="deutsch"></a>
## Deutsch

### Unterstützte Versionen

| Version | Unterstützt | Status |
| ------- | ----------- | ------ |
| `15.0.x` | :white_check_mark: | Aktiver Versionszweig |
| `< 15.0` | :x: | Nicht mehr unterstützt (End of Life) |

### Sicherheits-Invarianten & Entwurfsprinzipien

1. **100% Local-First & Zero-Egress**: ProFiler arbeitet ausnahmslos lokal. Keine Netzwerk-Telemetrie, kein Cloud-Upload, kein Online-Konto.
2. **Flüchtige Passwörter (Session-Only)**: PDF-Passwörter und Schlüssel verbleiben ausschließlich im flüchtigen Arbeitsspeicher und werden niemals auf Datenträgern oder in Konfigurationsdateien gespeichert.
3. **Redigierter Datenaustausch**: Der Workspace-Export entfernt automatisch system-spezifische absolute Pfade und vertrauliche Schlüssel.
4. **Unprivilegierter Betrieb (Non-Elevation)**: Die Anwendung läuft mit Standard-Benutzerrechten unter `%LOCALAPPDATA%\ProFilerSuite` (bzw. XDG unter POSIX) und benötigt keine Administratorrechte.

### Melden von Sicherheitslücken

Wenn Sie eine Sicherheitslücke entdecken, melden Sie diese bitte vertraulich:

1. **GitHub Security Advisories**: Über den Reiter [Security](https://github.com/file-bricks/ProFiler/security/advisories) im Repository -> **Report a vulnerability**.
2. **Direktkontakt**: Falls GitHub nicht nutzbar ist, per E-Mail an `security@open-bricks.org` oder `support@lukasgeiger.com`.

**Bitte eröffnen Sie keine öffentlichen Issues für Sicherheitslücken.**

Wir bestätigen den Eingang innerhalb von **48 Stunden** und informieren regelmäßig über den Fortschritt bis zur Veröffentlichung eines Patches.

### Sicherheits-Updates

Sicherheitsupdates werden schnellstmöglich bereitgestellt und im [CHANGELOG.md](CHANGELOG.md) dokumentiert.

