# PORTIERUNGSPLAN - ProFiler Suite

Stand: 2026-08-24
Workflow: SOFTWARE STRANGE NEW WORLDS, Pfad B

## Entscheidung

ProFiler bleibt eine Windows-Desktop-Vollanwendung und Windows-Store-Kandidat. macOS und Linux bleiben belegte Source-Smoke-Ziele derselben Codebasis, aber keine eigenständigen Paketlinien. Android, iOS, Web/PWA, native Mobile-Apps und direkte Server-Synchronisierung sind Nicht-Ziele ohne neuen dokumentierten Nutzer-Usecase.

## Features der am besten ausgebauten Version

- lokale Dokumenten- und Dateiindexierung mit SQLite, Volltextsuche und Metadaten
- OCR-Workflows für gescannte PDFs und Bilder über Tesseract und Poppler/PDF-Tooling
- PDF-Werkzeuge für Verschlüsselung, Entschlüsselung, Seitenauszüge, Schwärzung, OCR und Export
- Duplikat- und Versionsprüfung über SHA-256-Fingerprints
- Datenschutzampel, Clipboard-/Weitergabeprüfung und redigierte Workspace-Exporte
- lokale PySide6-Oberfläche mit Vorschau, Filterung, System-Tray und optionalen Geschwisterwerkzeug-Starts
- `profiler-workspace-v1.json` als redigiertes Austauschformat ohne Rohdokumente, Secrets oder ungefragte absolute Benutzerpfade

## Usecases

Aus den Features ergeben sich diese Hauptusecases:

- private oder berufliche Dokumentenbestände lokal durchsuchen, ordnen und prüfen
- gescannte Unterlagen per OCR in eine lokale Such- und Review-Struktur bringen
- PDF- und Dokumentpakete vor Weitergabe datenschutzseitig kontrollieren
- lokale Ordner, OneDrive-Platzhalter und Dokumentversionen ohne Cloud-Upload verwalten
- einen redigierten Arbeitsstand für Review, Übergabe oder Plattform-Smoke exportieren
- optionale Desktop-Geschwisterwerkzeuge wie ProSync oder SQLiteViewer aus demselben lokalen Arbeitsplatz heraus starten

## Usecase-Settings

| Setting | Nutzergruppe | Situation | Plattformfolge |
| --- | --- | --- | --- |
| Dokumenten-Arbeitsplatz | Power-User, kleine Büros, private Archivnutzer | Viele lokale Dateien, OCR/PDF-Werkzeuge, Datenschutzprüfung und Vorschau werden in längeren Arbeitssitzungen gebraucht | Windows-Desktop ist Hauptlinie; Windows Store ist Komfort-Vertrieb |
| Plattform-Smoke und Entwicklerbetrieb | Entwickler, Maintainer, technisch versierte Nutzer | Source-Start, POSIX-Pfade, redigierter Workspace und PySide6-Grundverhalten müssen auf Linux/macOS prüfbar bleiben | macOS/Linux nur Source-Smokes, keine Paket-/Store-Ziele |
| Review-/Übergabe-Situation | Maintainer, Support, andere Agenten | Es sollen Einstellungen und Indexzusammenfassungen geteilt werden, aber keine Rohdokumente oder Secrets | `profiler-workspace-v1.json` als dateibasierter Austausch; keine Live-Synchronisierung |

## Plattformentscheidung

| Plattform | Status | Begründung |
| --- | --- | --- |
| Windows Desktop | Hauptlinie | Der Kernusecase braucht lokale Dateisystem-, OCR-, PDF-, Tray- und Vorschau-Workflows. |
| Windows Store | Kandidat, extern gegatet | Store-Materialien und Packaging-Staging sind vorbereitet; offen bleiben signiertes MSIX, WACK, Partner-Center-Upload und Tesseract-/Poppler-Bündelung mit Installations-Smoke. |
| macOS | Source-Smoke, keine Paketlinie | Belegte Smokes prüfen Pfade, PySide6, Exportformat, SQLite, i18n und graceful OCR/PDF-Fallbacks; native App-Bundles sind nicht belegt. |
| Linux | Source-Smoke, keine Paketlinie | Belegte Smokes prüfen XDG/POSIX-Basis, PySide6, Exportformat, SQLite, i18n und Fallbacks; `.deb`, AppImage oder Flatpak sind nicht belegt. |
| Web/PWA | Nicht-Ziel | Der Vollusecase braucht lokale Rohdateien, OCR/PDF-Werkzeuge, Dateisystemzugriff und Desktop-Vorschau; ein read-only Statusbild hätte keinen eigenständigen Aktionsnutzen. |
| Android/iOS | Nicht-Ziel | Smartphone- oder Tablet-Usecases würden keine lokale Vollversion mit denselben Datei-, OCR-, PDF- und Datenschutzfunktionen tragen; ohne neuen mobilen Aktionsnutzen keine native App. |
| Server-Sync | Nicht-Ziel | Der Usecase ist local-first und zero-egress; das vorhandene Austauschformat ist bewusst dateibasiert und redigiert. |

## Entscheidungslogik

- Regel e2 greift für den Hauptusecase: Desktop bleibt klar primär, Mobile bringt ohne neue Zielgruppe keinen Mehrwert.
- Regel f ist mit `profiler-workspace-v1.json` nur als redigierter Wechsel-/Review-Vertrag erfüllt, nicht als Rohdatenmigration.
- Regel g greift nicht: Der ProFiler-Usecase erfordert keine direkte Synchronisierung; Rohdokumente bleiben außerhalb des Austauschformats.
- Companion-Logik c/d wird nicht aktiviert: ProSync und SQLiteViewer sind optionale lokale Geschwisterwerkzeuge, keine ProFiler-Mobile- oder Web-Companions.

## Umsetzungsstatus

- Belegt: Windows-Desktop-Quellstart, lokale Runtime-Dokumentation, Store-Materialien, Store-Readiness-Audit, `profiler-workspace-v1.json`, Linux-/macOS-Source-Smokes.
- Offen: signiertes MSIX, WACK-Readback, Partner-Center-Upload, Store-Status-Readback, Tesseract-/Poppler-Bündelung, realer installierter Store-Paket-Smoke.
- Nicht beginnen: Web/PWA-, Android-, iOS-, Server-Sync- oder read-only Companion-Linie ohne neuen, hier dokumentierten Nutzer-Usecase.

## Guard

`mobile_icons`, Store-Assets, Source-Smokes oder ein redigierter Workspace-Export sind keine Belege für eine Mobile-, Web- oder Sync-Produktlinie. Künftige Icon-, i18n-, Store- oder Plattform-Automationen dürfen daraus keinen Companion oder Port ableiten.
