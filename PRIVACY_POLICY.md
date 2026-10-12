# Privacy Notes / Datenschutzhinweise

**Reviewed:** 2026-10-12
**Scope:** ProFiler Suite source workflows; no Store or hosted service is currently claimed.

## Deutsch

ProFiler ist eine Desktopanwendung für lokale Datei- und Dokumentabläufe. Die Anwendung verarbeitet ausgewählte Ordner, Dateinamen, Metadaten und Inhalte für Suche, Vorschau, OCR, PDF-Werkzeuge und Duplikaterkennung. Suchindizes und Einstellungen werden lokal gespeichert; unter Windows nutzt die Anwendung standardmäßig den lokalen Anwendungsdatenordner, unter anderen Plattformen das Benutzerprofil. Ein Legacy-Lesepfad kann zusätzlich berücksichtigt werden.

Die optionale Datenschutzampel kann bei gestarteter Nutzung Text aus der Zwischenablage prüfen. Die Historie wird in dieser Komponente im Arbeitsspeicher gehalten; eine vom Nutzer ausgelöste Konfigurationsspeicherung betrifft Listen und Optionen. Aktivieren Sie keine Zwischenablage- oder Dateiabläufe, wenn die dort enthaltenen Daten nicht geprüft werden sollen.

Die Quellcodepfade für die beiden PDF-Masterpasswort-Einstellungen schließen diese Werte beim Speichern der Programmeinstellungen aus; entsprechende Legacy-Schlüssel werden beim Laden entfernt. Das ist eine konkrete Implementierungseigenschaft und keine allgemeine Zusage zur Speicherung aller Geheimnisse durch Betriebssysteme oder externe Programme.

In den für diese Pflege geprüften First-Party-Pfaden wurde kein automatischer Upload ausgewählter Dokumentinhalte an einen ProFiler-Server und keine Telemetrie gefunden. Der optionale Modulinstaller kann GitHub kontaktieren, wenn er ausdrücklich gestartet wird. ProFiler blockiert keinen ausgehenden Netzwerkverkehr und kontrolliert nicht das Verhalten externer Bibliotheken, OCR-/PDF-Programme oder vom Nutzer gestarteter Geschwisterwerkzeuge.

Vor einer Weitergabe sollten Sie Suchtreffer, Datenschutzampel-Warnungen, Schwärzungen und Workspace-Exporte selbst prüfen. Diese Funktionen sind Hilfsmittel; sie garantieren keine vollständige Erkennung, Anonymisierung oder rechtliche Konformität.

Details zur Sicherheitsmeldung stehen in [SECURITY.md](SECURITY.md), zu Abhängigkeiten in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) und zu Support in [SUPPORT.md](SUPPORT.md).

## English

ProFiler is a desktop application for local file and document workflows. It processes selected folders, filenames, metadata, and contents for search, previews, OCR, PDF utilities, and duplicate detection. Search indexes and settings are stored locally; Windows uses the local application-data directory by default, while other platforms use the user's profile. A legacy read path may also be considered.

When the optional privacy traffic-light tool is launched, it can inspect clipboard text. Its history is held in memory; a user-initiated configuration save stores lists and options. Do not enable clipboard or file workflows for data that should not be inspected.

The source paths for the two PDF master-password settings omit those values when application settings are saved and remove matching legacy keys when loaded. This describes a specific implementation behavior; it is not a general promise about operating-system storage or external programs.

The first-party paths reviewed for this maintenance did not show automatic upload of selected document contents to a ProFiler server or telemetry. The optional module installer can contact GitHub when explicitly invoked. ProFiler does not block outbound network traffic or control third-party libraries, OCR/PDF programs, or separate tools launched by the user.

Before sharing, review search results, privacy-light warnings, redactions, and workspace exports yourself. These features are aids; they do not guarantee complete detection, anonymization, or legal compliance.

See [SECURITY.md](SECURITY.md) for security reports, [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) for dependency notes, and [SUPPORT.md](SUPPORT.md) for support information.
