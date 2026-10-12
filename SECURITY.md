# Security Policy / Sicherheitsrichtlinie

[English](#english) | [Deutsch](#deutsch)

---

<a name="english"></a>
## English

### Reporting a security issue

Please report suspected vulnerabilities privately through [GitHub Security Advisories](https://github.com/file-bricks/ProFiler/security/advisories/new). If that channel is unavailable, use one of the contact addresses listed below. Do not include real personal records, credentials, or private documents in a public issue.

No response, triage, or remediation deadline is promised. Work depends on reproducibility, impact, and maintainer availability. Reports are reviewed for this source project; this policy does not create a support commitment for a particular release or deployment.

- `security@file-bricks.org`
- `security@open-bricks.org`
- `lukas@open-bricks.org`
- `security@ellmos.ai`
- `support@lukasgeiger.com`

### Scope and limits

ProFiler's default workflows process selected local folders and store application settings and search indexes on the user's device. The optional module installer can contact GitHub when a user invokes it. ProFiler does not block network traffic, sandbox external programs, or control the behavior of the operating system and third-party libraries. User-configured tools and integrations can have separate data flows.

The project has not published an independent security certification or a guarantee that every deployment is secure. The pattern-based privacy review and workspace exchange are aids; inspect results and exported files before sharing them.

The Windows application runs with the invoking user's permissions and does not require administrator elevation for its standard workflows. External programs inherit their own behavior and may require separate permissions.

### Current source status

The repository version is frozen at `15.0.2` while maintenance work continues. A source version does not by itself mean that a binary release, security-support window, or Store package is available.

---

<a name="deutsch"></a>
## Deutsch

### Sicherheitsproblem melden

Bitte melden Sie vermutete Sicherheitslücken vertraulich über [GitHub Security Advisories](https://github.com/file-bricks/ProFiler/security/advisories/new). Falls dieser Kanal nicht verfügbar ist, können Sie eine der folgenden Kontaktadressen verwenden. Bitte senden Sie keine echten personenbezogenen Unterlagen, Zugangsdaten oder privaten Dokumente in öffentlichen Issues.

Es werden keine Antwort-, Triage- oder Behebungsfristen zugesagt. Die Bearbeitung hängt von Reproduzierbarkeit, Auswirkungen und verfügbarer Maintainer-Zeit ab. Meldungen beziehen sich auf dieses Quellcodeprojekt; diese Richtlinie begründet keine Supportzusage für eine bestimmte Version oder Bereitstellung.

- `security@file-bricks.org`
- `security@open-bricks.org`
- `lukas@open-bricks.org`
- `security@ellmos.ai`
- `support@lukasgeiger.com`

### Umfang und Grenzen

Die Standardabläufe von ProFiler verarbeiten ausgewählte lokale Ordner und speichern Programmeinstellungen sowie Suchindizes auf dem Gerät. Der optionale Modulinstaller kann GitHub kontaktieren, wenn eine Person ihn startet. ProFiler blockiert keinen Netzwerkverkehr, kapselt externe Programme nicht ab und kontrolliert weder das Betriebssystem noch Drittanbieterbibliotheken. Vom Nutzer konfigurierte Werkzeuge und Integrationen können eigene Datenflüsse haben.

Das Projekt behauptet keine unabhängige Sicherheitszertifizierung und garantiert nicht, dass jede Bereitstellung sicher ist. Die regelbasierte Datenschutzprüfung und der Workspace-Austausch sind Hilfsmittel; prüfen Sie Treffer und exportierte Dateien vor einer Weitergabe.

Die Windows-Anwendung läuft mit den Berechtigungen des aufrufenden Benutzerkontos und benötigt für ihre Standardabläufe keine Administratorrechte. Externe Programme behalten ihr eigenes Verhalten und können gesonderte Berechtigungen benötigen.

### Aktueller Quellstand

Die Repository-Version bleibt während der laufenden Pflege auf `15.0.2` eingefroren. Eine Quellversion belegt weder eine verfügbare Binärveröffentlichung noch einen Supportzeitraum oder ein Store-Paket.
