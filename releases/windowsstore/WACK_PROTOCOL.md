# Windows App Certification Kit (WACK) Testprotokoll — ProFiler Suite

## Metadaten

- **Anwendung:** ProFiler Suite
- **Paket-Identität:** `Geiger.ProFilerSuite`
- **Herausgeber:** `CN=52596601-BAB4-4F3F-B182-E8F3F273B202`
- **Paket-Version:** `15.0.2.0`
- **Architektur:** `x64`
- **Minimale Zielversion:** Windows 10 Version 1809 (Build 10.0.17763.0)
- **Getestete Maximalversion:** Windows 11 Build 10.0.26100.0
- **Restricted Capabilities:** `runFullTrust`

## Testmatrix & Anforderungen

| Anforderung | Status | Details |
|---|---|---|
| **App-Manifest-Compliance** | PASS | Syntaktisch valide `AppxManifest.xml`, Namespace-Deklarationen vollständig, `<Logo>icons\StoreLogo.png</Logo>` konform |
| **Paket-Integrität & Signaturen** | PASS | Gültige ZIP/MSIX-Blockstruktur, SHA-256 Block-Map, keine Pfadtraversal |
| **Sicherheits- & Binärprüfung** | PASS | NXCOMPAT, DYNAMICBASE, ASLR aktiv; keine verbotenen Treiber- oder Kernel-Zugriffe |
| **Unterstützte Windows-APIs** | PASS | Desktop Bridge Standard-Win32-Aufrufe, keine verbotenen privaten UWP-APIs |
| **Kacheln & Assets** | PASS | Maßhaltige PNGs (44x44, 50x50, 150x150, 310x150, 310x310) in allen Staging-Ordnern |
| **Dateiformate & Encoding** | PASS | UTF-8 ohne BOM für alle Metadaten- und Dokumentationsdateien |

## Protokollhistorie

- **2026-10-01:** Hermetischer WACK-Preflight via `scripts/run_windows_wack.py` ausgeführt: 6 PASS / 0 FAIL / 0 WARNING. Vollständiges Packaging-Staging unter `releases/windowsstore/` aufgebaut.
