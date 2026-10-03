# Exportformat - ProFiler Suite

Stand: 2026-07-22

## Zweck

`profiler-workspace-v1.json` ist ein redigiertes Austauschformat für ProFiler. Es dient der Übergabe zwischen Desktop-Installationen, der Vorbereitung von macOS-/Linux-Smokes und sicheren Review-Situationen. Es ist kein Rohdokument-Archiv und kein Synchronisationsprotokoll.

## Grundsätze

- keine Rohdokumente
- keine Secrets, Tokens, Passwörter oder OAuth-Daten
- keine ungefragten absoluten Benutzerpfade
- Indexe nur als Zusammenfassung mit redigierten Wurzelreferenzen
- Datenschutzampel nur als Regel-/Status-Zusammenfassung
- sichere Einstellungen dürfen importiert werden; lokale Pfade bewusst nicht

## Sichere Dateiausgabe

Export und Import-Vorschau verwenden exklusiv erzeugte eigene temporäre Dateien
im Zielverzeichnis. Erst nach vollständigem Schreiben, Synchronisieren und
Schließen wird das Ziel ersetzt. Eine vorhandene Ausgabe bleibt bei Fehlern
erhalten; fremde temporäre Dateien werden weder überschrieben noch entfernt.
Gleichzeitige Schreibvorgänge besitzen getrennte temporäre Dateien; der letzte
erfolgreiche vollständige Schreibvorgang bestimmt die Ausgabe.

Der Export schützt die bekannten Indexdatenbanken, deren Standardbegleitdateien
`-wal`, `-shm`, `-journal` und bekannte Konfigurationspfade einschließlich der
verwendeten Legacy-Pfade und konkreter Managerpfade. Pfad- und Dateialiase werden
vor dem Schreiben und vor der Veröffentlichung geprüft. Mehrdeutige Windows-
Dateinamen mit abschließendem Punkt oder Leerzeichen werden abgewiesen.

Eine Import-Vorschau darf die ursprüngliche Austauschdatei oder bekannte
Einstellungsdateien nicht ersetzen. Die Vorschau wird vollständig gespeichert,
bevor sichere Einstellungen übernommen werden. Ein Vorschaufehler verändert
deshalb keine Einstellungen. Ein anschließender Fehler beim Speichern der
Einstellungen kann weiterhin einen Teilimport hinterlassen: mehrere einzelne
Einstellungsschreibvorgänge und Vorschau bilden keine gemeinsame Transaktion.

Der Schutz umfasst keine beliebigen Rohdokumente, unbekannten Indexdatenbanken
des Importaufrufs, besonderen VFS-/Superjournal-Dateien, externen Dateisystemrennen
nach letzter Prüfung oder Stromausfall-Dauerhaftigkeit. Andere Persistenzhelfer,
insbesondere der separate Settings-Schreiber, sind damit nicht freigegeben.

## Aktuelle Struktur

```json
{
  "schema": "profiler-workspace-v1",
  "schema_version": 1,
  "exported_at": "2026-06-03T12:00:00Z",
  "app": {
    "name": "ProFiler Suite",
    "version": "15.0.2"
  },
  "workspace": {
    "name": "ProFiler Workspace (2 Verbindungen)",
    "notes": "Redigierter Export ohne Rohdokumente und ohne lokale Benutzerpfade.",
    "connection_count": 2,
    "enabled_connection_count": 2
  },
  "settings": {
    "theme": "dark",
    "delete_mode": "soft",
    "ocr_enabled": true,
    "ocr_language": "deu",
    "ocr_languages": ["deu"]
  },
  "indexes": [
    {
      "id": "local-docs",
      "label": "Dokumente",
      "file_count": 1240,
      "redacted_root": "[source-root-1]",
      "formats": ["docx", "pdf", "txt"],
      "enabled": true,
      "sources_count": 1,
      "status": "ready"
    }
  ],
  "privacy_summary": {
    "status": "rules_configured",
    "sensitive_hit_count": 0,
    "categories": [],
    "blacklist_terms_count": 12,
    "whitelist_terms_count": 4,
    "clipboard_lock": true,
    "whole_words": true,
    "case_sensitive": false
  },
  "tool_links": {
    "prosync": {
      "enabled": true,
      "configured": false
    },
    "sqlite_viewer": {
      "configured": false
    },
    "formconstructor": {
      "configured": false
    },
    "datenschutzampel": {
      "configured": true
    }
  },
  "redactions": {
    "paths": true,
    "secrets": true,
    "raw_documents": false
  }
}
```

## Importverhalten

- übernommen werden nur sichere Einstellungen wie OCR-Sprache, Löschmodus oder UI-bezogene Optionen
- nicht übernommen werden lokale Datenbankpfade, Companion-Pfade, PDF-Masterpasswörter und sonstige Secrets
- der importierte Snapshot wird lokal als Vorschau gespeichert, damit Review-Daten sichtbar bleiben, ohne produktive Indexe umzubiegen
- vor jeder Einstellungsmutation werden Dateigröße, Schema-Version, Container,
  Werttypen, erlaubte Settings und der vollständige Payload auf absolute Pfade
  sowie Secret-Feldnamen geprüft
- zu große, zu tiefe oder nicht vollständig redigierte Dateien werden
  fail-closed abgelehnt

## Abgrenzung

Das Format ersetzt keine Datenbankmigration und keine Dateisynchronisation. Für echte Dokumentübertragung nutzt der Anwender normale Dateiwege wie lokale Kopie, Backup, USB, Netzlaufwerk oder bewusst gewählte Cloud-Ordner.
