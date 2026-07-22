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

## Aktuelle Struktur

```json
{
  "schema": "profiler-workspace-v1",
  "schema_version": 1,
  "exported_at": "2026-06-03T12:00:00Z",
  "app": {
    "name": "ProFiler Suite",
    "version": "15.0.0"
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
