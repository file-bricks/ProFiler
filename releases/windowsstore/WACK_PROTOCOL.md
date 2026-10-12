# Windows App Certification Kit (WACK) – Prüfprotokoll

## Aktueller Stand (2026-10-12)

| Prüfschritt | Beleglage | Status |
|---|---|---|
| Native Windows-EXE | Die von build_exe.bat verlangten Tesseract- und Poppler-Dateien fehlen im geprüften Checkout. | BLOCKIERT |
| Aktuelles MSIX-Paket | Kein aktuelles Paket aus dem geprüften Quellstand belegt. | NICHT AUSGEFÜHRT |
| WACK | Kein echter WACK-Lauf auf einem aktuellen Paket belegt. | NICHT AUSGEFÜHRT |
| Signatur und Store-Einreichung | Keine Signatur oder Einreichung belegt. | NICHT AUSGEFÜHRT |

Die Werte für Identität, Herausgeber, Version und Capabilities in AppxManifest.xml und store_package.json sind Staging-Metadaten. Sie belegen nicht, dass ein Paket gebaut, signiert, getestet, eingereicht oder genehmigt wurde.

## Historische Preflight-Dateien

Die versionierten Dateien wack_preflight_20261001.xml und wack_preflight_20261001.json stammen aus der früheren Option --preflight. Diese erzeugte sechs synthetische PASS-Werte, ohne ein Paket zu prüfen oder das Windows App Certification Kit aufzurufen. Die Dateien sind ausdrücklich als SYNTHETIC NOT WACK markiert; sie sind keine Zertifizierungsberichte.

Die aktuelle Option --preflight schreibt ausschließlich einen JSON-Vorbereitungsstatus mit status NOT_RUN und wack_executed false. Sie erzeugt keine XML-Datei und keine WACK-Ergebnisse. Der Parser weist historische wack_preflight_-Dateien und ausdrücklich markierte synthetische XML-Dateien zurück.

## Echter WACK-Lauf

Ein echter Lauf setzt ein gebautes MSIX sowie das installierte Windows App Certification Kit voraus. Der Lauf muss auf genau dem zu prüfenden Paket mit dem tatsächlichen App-Cert-Programm erfolgen:

    python scripts\run_windows_wack.py --msix <Pfad-zum-MSIX>

Der resultierende Report und das Log müssen zusammen mit Paket-Hash, App-Cert-Version, Host, Zeitpunkt und tatsächlichem Exitcode dokumentiert werden. Ein statischer Dateikonsistenzcheck oder die Anwesenheit von Staging-Dateien ersetzt diese Prüfung nicht.
