# Exportformat - ProFiler Suite

Stand: 2026-06-01

## Zweck

`profiler-workspace-v1.json` ist ein geplantes dateibasiertes Austauschformat für ProFiler. Es dient dem Wechsel zwischen Desktop-Installationen, macOS-/Linux-Smokes und optionalen redigierten Review-Situationen. Es ist kein Synchronisationsprotokoll und kein Rohdokument-Archiv.

## Grundsätze

- keine Rohdokumente
- keine Secrets, Tokens, Passwörter oder OAuth-Daten
- keine ungefragten absoluten Benutzerpfade
- Datenschutzfunde nur als redigierte Zusammenfassung
- Schema-Version immer explizit führen

## Geplante Struktur

```json
{
  "schema": "profiler-workspace-v1",
  "exported_at": "2026-06-01T00:00:00+02:00",
  "app": {
    "name": "ProFiler Suite",
    "version": "15"
  },
  "workspace": {
    "name": "Beispielarchiv",
    "notes": "Redigierter Export ohne Rohdokumente"
  },
  "settings": {
    "ui_language": "de",
    "theme": "dark",
    "ocr_languages": ["deu", "eng"]
  },
  "indexes": [
    {
      "id": "local-documents",
      "label": "Dokumente",
      "file_count": 1240,
      "redacted_root": "[LOCAL_ARCHIVE]",
      "formats": ["pdf", "docx", "txt", "png"]
    }
  ],
  "privacy_summary": {
    "status": "needs_review",
    "sensitive_hit_count": 12,
    "categories": ["personenbezogen", "finanzen"]
  },
  "tool_links": {
    "prosync": {
      "enabled": true,
      "configured": false
    }
  }
}
```

## Abgrenzung

Das Format ersetzt keine Datenbankmigration und keine Dateisynchronisation. Für echte Dokumentübertragung nutzt der Anwender normale Dateiwege wie lokale Kopie, Backup, USB, Netzlaufwerk oder bewusst gewählte Cloud-Ordner.

