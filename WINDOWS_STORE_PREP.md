# Windows Store Preparation - ProFiler Suite

## Current status (2026-10-12)

**NOT CLEARED for release or Store submission.** The source version remains frozen at `15.0.2`. The reviewed checkout does not contain the Tesseract/Poppler files required by `build_exe.bat`, so a native executable build cannot currently proceed. No signed MSIX, current WACK run on a built package, or Partner Center submission is evidenced.

The tracked `wack_preflight_20261001.xml` and JSON are synthetic outputs from the former `scripts/run_windows_wack.py --preflight` implementation; they were generated without a package or WACK run. They are not a certification report and must not be used as evidence of Windows App Certification Kit results. The current option writes only a static `NOT_RUN` JSON status and does not create WACK XML.

The current `AppxManifest.xml` declares `runFullTrust`. That manifest value is staging data, not proof that a package meets Store requirements or has been accepted.

## Historical staging record (2026-10-01)

The repository contains Store listing drafts, package metadata, a manifest, screenshot references, icons, and an earlier synthetic preflight file. These files record preparation work only. Their presence does not establish that the current source builds, that runtime components are bundled, or that any package was tested, signed, submitted, or approved.

## Gates before any future submission

1. Identify and review the exact Tesseract and Poppler binaries, data files, and redistribution terms required by the application.
2. Produce a native build from the exact reviewed source after the required bundle is present; preserve the actual build and artifact hashes.
3. Inspect the executable and assembled MSIX contents, package metadata, and included license notices.
4. Sign the exact MSIX and run the real WACK tool against that package. Record the actual tool, package hash, host, result, and report.
5. Complete Partner Center review and approval before describing the app as available through the Store.

No gate above is marked complete by this document. The source release gate remains closed until the actual build and external submission requirements are satisfied.
