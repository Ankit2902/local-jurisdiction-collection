# Standalone acquisition matrix — 15 October 2026

These are the 24 previously CUA-dependent jurisdictions, not a new database backlog count. Four bounded standalone pilots passed, one standalone pilot is partial, five manual publisher-export/local-import pilots passed, and 14 primary standalone paths remain unqualified. No whole jurisdiction is qualified complete.

Municipal.codes full inventories are retained earlier CUA evidence; fresh standalone inventory acquisition is still a gap. Everett has an actual selected-section download but no fresh repeated endcheck. Bellingham has an actual initial legal capture but a later 429 prevents the endcheck and completion of its live job.

| Jurisdiction | Publisher | Best verified result | Primary sample records | Runbook |
|---|---|---|---:|---|
| Flagstaff, AZ | codepublishing | Manual publisher export + local importer passed | 5 | [Runbook](codepublishing/README.md) |
| Berkeley, CA | municipal-codes | Bounded standalone acquisition/export passed | 10 | [Runbook](municipal-codes/README.md) |
| Burlingame, CA | ecode360 | Primary standalone path unqualified | 0 | [Runbook](ecode360/README.md) |
| Emeryville, CA | ecode360 | Primary standalone path unqualified | 0 | [Runbook](ecode360/README.md) |
| Foster City, CA | ecode360 | Primary standalone path unqualified | 0 | [Runbook](ecode360/README.md) |
| Fremont, CA | codepublishing | Manual publisher export + local importer passed | 21 | [Runbook](codepublishing/README.md) |
| Half Moon Bay, CA | ecode360 | Primary standalone path unqualified | 0 | [Runbook](ecode360/README.md) |
| Malibu, CA | ecode360 | Primary standalone path unqualified | 0 | [Runbook](ecode360/README.md) |
| Petaluma, CA | municipal-codes | Bounded standalone acquisition/export passed | 10 | [Runbook](municipal-codes/README.md) |
| San Carlos, CA | codepublishing | Manual publisher export + local importer passed | 10 | [Runbook](codepublishing/README.md) |
| San Leandro, CA | ecode360 | Primary standalone path unqualified | 0 | [Runbook](ecode360/README.md) |
| Santa Clara, CA | ecode360 | Primary standalone path unqualified | 0 | [Runbook](ecode360/README.md) |
| Santa Monica, CA | ecode360 | Primary standalone path unqualified | 0 | [Runbook](ecode360/README.md) |
| Santa Rosa, CA | ecode360 | Primary standalone path unqualified | 0 | [Runbook](ecode360/README.md) |
| Sonoma, CA | municipal-codes | Bounded standalone acquisition/export passed | 10 | [Runbook](municipal-codes/README.md) |
| South San Francisco, CA | ecode360 | Primary standalone path unqualified | 0 | [Runbook](ecode360/README.md) |
| Sunnyvale, CA | ecode360 | Primary standalone path unqualified | 0 | [Runbook](ecode360/README.md) |
| West Hollywood, CA | ecode360 | Primary standalone path unqualified | 0 | [Runbook](ecode360/README.md) |
| Bellingham, WA | municipal-codes | Partial standalone; final check missing | 13 | [Runbook](municipal-codes/README.md) |
| Burien, WA | codepublishing | Manual publisher export + local importer passed | 6 | [Runbook](codepublishing/README.md) |
| Everett, WA | municipal-codes | Bounded standalone acquisition/export passed | 1 | [Runbook](municipal-codes/README.md) |
| Renton, WA | codepublishing | Manual publisher export + local importer passed | 1 | [Runbook](codepublishing/README.md) |
| SeaTac, WA | ecode360 | Primary standalone path unqualified | 0 | [Runbook](ecode360/README.md) |
| Tukwila, WA | ecode360 | Primary standalone path unqualified | 0 | [Runbook](ecode360/README.md) |

## Per-jurisdiction evidence and next action

Source versions below are publisher notices or historical evidence, not a guarantee that all uncodified amendments are included. The JSON matrix retains the full baseline discovery record alongside the new qualification and official-alternative findings.

### Flagstaff, AZ

**Manual publisher export + local importer passed**. Primary sample records: 5.

Primary publication: [https://www.codepublishing.com/AZ/Flagstaff/](https://www.codepublishing.com/AZ/Flagstaff/). Tested route: [https://www.codepublishing.com/AZ/Flagstaff/cgi/menuCompile.pl](https://www.codepublishing.com/AZ/Flagstaff/cgi/menuCompile.pl).

Evidence: [codepublishing/STANDALONE-VALIDATION.json](codepublishing/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `flagstaff-az` entry.

Next action: Operator opens ordinary publisher page, selects scope, Print/SaveSelections→HTML→Save, registers unchanged file with actual time/source URL, then runs local importer with explicit expected currency and1–3 observed chapter numbers. For unattended fresh acquisition, obtain a normal supported environment or documented sanctioned publisher integration.

Remaining limits: Fresh unattended export acquisition is challenged in this environment; no unattended network success established.; Only listed bounded chapters are parsed/qualified; other titles/families, unlinked status nodes, uncodified updates, images and incorporated PDFs remain outside scope.

Official alternative discovery: Official Procurement Code Manual is a partial publication. Former 1991 Land Development Code is explicitly repealed. Neither replaces current complete City Code/Charter.

Alternative currentness: Web tool read manual revisions through June 3, 2024; direct page/download requests returned404. Current transport not qualified.

### Berkeley, CA

**Bounded standalone acquisition/export passed**. Primary sample records: 10.

Primary publication: [https://berkeley.municipal.codes/BMC](https://berkeley.municipal.codes/BMC). Tested route: [https://berkeley.municipal.codes/BMC/1.01.010](https://berkeley.municipal.codes/BMC/1.01.010).

Evidence: [municipal-codes/STANDALONE-VALIDATION.json](municipal-codes/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `berkeley-ca` entry.

Next action: Use ordinary headed legal capture or publisher Save UI on an approved bounded plan; stop on429/challenge and respect Retry-After. Reacquire independent inventories through a qualified transport before full collection.

Remaining limits: Whole corpus unvalidated; prior CUA independent inventory remains separate from standalone body acquisition; Additional publication-family scope, images/attachments and full disposition reconciliation pending

Official alternative discovery: City clerk page delegates current code to municipal.codes and lists pending ordinances. No city-hosted complete export verified. Publisher TOC entry called FullCodePDF was investigated by family agent and renders an ordinance table; not counted as a PDF.

Alternative currentness: Actual city page200; current-through code currency must come from publisher, not city-page HTTP timestamp.

### Burlingame, CA

**Primary standalone path unqualified**. Primary sample records: 0.

Primary publication: [https://ecode360.com/44587767](https://ecode360.com/44587767). Tested route: [https://ecode360.com/44507298](https://ecode360.com/44507298).

Evidence: [ecode360/STANDALONE-VALIDATION.json](ecode360/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `burlingame-ca` entry.

Next action: Respect host stop and publisher access prerequisites. After authorized resumption, test one normal headed/passive browser or authorized publisher export; preserve fresh acquisition/selection/currentness evidence before parsing. Do not replay CUA bytes as standalone acquisition.

Remaining limits: Initial HTTP 403 challenge/access response; stopped before legal content. Passive/headed completion not tested.; Publisher PDF/Word availability varies by publication and login; documented credentialed API untested

Official alternative discovery: Official Codes & Regulations search result delegates MunicipalCode, Title18 and Title25. Current complete city-hosted export not verified; direct discovered city route404.

Alternative currentness: Search-indexed primary page only; live standalone route404 prevents current-route verification.

### Emeryville, CA

**Primary standalone path unqualified**. Primary sample records: 0.

Primary publication: [https://ecode360.com/47056325](https://ecode360.com/47056325). Tested route: [https://ecode360.com/46989352](https://ecode360.com/46989352).

Evidence: [ecode360/STANDALONE-VALIDATION.json](ecode360/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `emeryville-ca` entry.

Next action: Respect host stop and publisher access prerequisites. After authorized resumption, test one normal headed/passive browser or authorized publisher export; preserve fresh acquisition/selection/currentness evidence before parsing. Do not replay CUA bytes as standalone acquisition.

Remaining limits: Initial HTTP 403 challenge/access response; stopped before legal content. Passive/headed completion not tested.; Publisher PDF/Word availability varies by publication and login; documented credentialed API untested

Official alternative discovery: First-party page embeds complete eight-section Charter in four articles; standalone bounded two-section export succeeds. BuildingDivision Title8PDF is historical ordinance22-013, not current Title8 or complete code.

Alternative currentness: Charter page states November4,2014 adoption without current-through amendment marker. Historical Title8PDF adopted November15,2022; current BuildingDivision notice says 2025codes effective January1,2026, so PDF must not be treated current merely because still linked.

Separate partial publication: `{"scope": "City Charter only; primary Municipal Code gap remains", "source_url": "https://www.emeryville.org/Government/About-Emeryville/Charter-City", "report_path": "../official-alternatives/final-emeryville-charter/E2E-VALIDATION.json", "records": 2, "outside_codex_accepted_bytes": true, "municipal_code_gap_closed": false, "note": "Verified by companion official-source agent, not rerun/duplicated here"}`

### Foster City, CA

**Primary standalone path unqualified**. Primary sample records: 0.

Primary publication: [https://ecode360.com/FO4449](https://ecode360.com/FO4449). Tested route: [https://ecode360.com/51404426](https://ecode360.com/51404426).

Evidence: [ecode360/STANDALONE-VALIDATION.json](ecode360/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `foster-city-ca` entry.

Next action: Respect host stop and publisher access prerequisites. After authorized resumption, test one normal headed/passive browser or authorized publisher export; preserve fresh acquisition/selection/currentness evidence before parsing. Do not replay CUA bytes as standalone acquisition.

Remaining limits: New headed probe deferred by host429stop. Prior-phase headless403 retained as baseline. Fresh Foster metadata requires login for PDF; no publisher export acquired.; Publisher PDF/Word availability varies by publication and login; documented credentialed API untested

Official alternative discovery: Actual official homepage200 still links legacy CodePublishing/FosterCity. No complete city-hosted export verified. Legacy link requires migration/redirect reconciliation with current eCode source.

Alternative currentness: City link observed live; does not establish current publisher content/version or current eCode designation.

### Fremont, CA

**Manual publisher export + local importer passed**. Primary sample records: 21.

Primary publication: [https://www.codepublishing.com/CA/Fremont/](https://www.codepublishing.com/CA/Fremont/). Tested route: [https://www.codepublishing.com/CA/Fremont/cgi/menuCompile.pl](https://www.codepublishing.com/CA/Fremont/cgi/menuCompile.pl).

Evidence: [codepublishing/STANDALONE-VALIDATION.json](codepublishing/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `fremont-ca` entry.

Next action: Operator opens ordinary publisher page, selects scope, Print/SaveSelections→HTML→Save, registers unchanged file with actual time/source URL, then runs local importer with explicit expected currency and1–3 observed chapter numbers. For unattended fresh acquisition, obtain a normal supported environment or documented sanctioned publisher integration.

Remaining limits: Fresh unattended export acquisition is challenged in this environment; no unattended network success established.; Only listed bounded chapters are parsed/qualified; other titles/families, unlinked status nodes, uncodified updates, images and incorporated PDFs remain outside scope.

Official alternative discovery: City municipal-code page delegates electronic code; official CharterCityInitiative describes proposed change from general-law status. Proposed Charter and comparable-city Charter packets are not current Fremont Charter/code exports.

Alternative currentness: Primary search excerpts concern November2026 proposal; direct city requests403. No adopted current Charter inferred.

### Half Moon Bay, CA

**Primary standalone path unqualified**. Primary sample records: 0.

Primary publication: [https://ecode360.com/HA4470](https://ecode360.com/HA4470). Tested route: [https://ecode360.com/47025425](https://ecode360.com/47025425).

Evidence: [ecode360/STANDALONE-VALIDATION.json](ecode360/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `half-moon-bay-ca` entry.

Next action: Respect host stop and publisher access prerequisites. After authorized resumption, test one normal headed/passive browser or authorized publisher export; preserve fresh acquisition/selection/currentness evidence before parsing. Do not replay CUA bytes as standalone acquisition.

Remaining limits: Initial HTTP 403 challenge/access response; stopped before legal content. Passive/headed completion not tested.; Publisher PDF/Word availability varies by publication and login; documented credentialed API untested

Official alternative discovery: Official page offers entire municipal code link, not a verified city-hosted downloadable copy. Individual ordinance PDFs are partial and can be historical/draft.

Alternative currentness: Live discovered city route404; search-indexed primary page insufficient for renewed transport/currentness.

### Malibu, CA

**Primary standalone path unqualified**. Primary sample records: 0.

Primary publication: [https://ecode360.com/44342329](https://ecode360.com/44342329). Tested route: [https://ecode360.com/44331146](https://ecode360.com/44331146).

Evidence: [ecode360/STANDALONE-VALIDATION.json](ecode360/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `malibu-ca` entry.

Next action: Respect host stop and publisher access prerequisites. After authorized resumption, test one normal headed/passive browser or authorized publisher export; preserve fresh acquisition/selection/currentness evidence before parsing. Do not replay CUA bytes as standalone acquisition.

Remaining limits: Initial HTTP 403 challenge/access response; stopped before legal content. Passive/headed completion not tested.; Publisher PDF/Word availability varies by publication and login; documented credentialed API untested

Official alternative discovery: City council documents page delegates codified ordinances to Municipal Code and advises checking uncodified ordinances separately. No complete current alternate export verified.

Alternative currentness: Discovered official route404 in standalone request; search-indexed delegation does not qualify current export.

### Petaluma, CA

**Bounded standalone acquisition/export passed**. Primary sample records: 10.

Primary publication: [https://petaluma.municipal.codes/Code](https://petaluma.municipal.codes/Code). Tested route: [https://petaluma.municipal.codes/Code/1.01.010](https://petaluma.municipal.codes/Code/1.01.010).

Evidence: [municipal-codes/STANDALONE-VALIDATION.json](municipal-codes/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `petaluma-ca` entry.

Next action: Use ordinary headed legal capture or publisher Save UI on an approved bounded plan; stop on429/challenge and respect Retry-After. Reacquire independent inventories through a qualified transport before full collection.

Remaining limits: Whole corpus unvalidated; prior CUA independent inventory remains separate from standalone body acquisition; Additional publication-family scope, images/attachments and full disposition reconciliation pending

Official alternative discovery: Official BuildingDivision CityCode link found. Search surfaced third-party civicmined list of eighteen original titlePDFs, but third-party summaries are not accepted as official designation; no independent complete official export verified.

Alternative currentness: Official page standalone403. Third-party advertised2025currency is unverified and not adopted.

### San Carlos, CA

**Manual publisher export + local importer passed**. Primary sample records: 10.

Primary publication: [https://www.codepublishing.com/CA/SanCarlos/](https://www.codepublishing.com/CA/SanCarlos/). Tested route: [https://www.codepublishing.com/CA/SanCarlos/cgi/menuCompile.pl](https://www.codepublishing.com/CA/SanCarlos/cgi/menuCompile.pl).

Evidence: [codepublishing/STANDALONE-VALIDATION.json](codepublishing/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `san-carlos-ca` entry.

Next action: Operator opens ordinary publisher page, selects scope, Print/SaveSelections→HTML→Save, registers unchanged file with actual time/source URL, then runs local importer with explicit expected currency and1–3 observed chapter numbers. For unattended fresh acquisition, obtain a normal supported environment or documented sanctioned publisher integration.

Remaining limits: Fresh unattended export acquisition is challenged in this environment; no unattended network success established.; Only listed bounded chapters are parsed/qualified; other titles/families, unlinked status nodes, uncodified updates, images and incorporated PDFs remain outside scope.

Official alternative discovery: Official CityHall page200 links CodePublishing/SanCarlos. No complete city-hosted current code download observed in bounded primary-page check.

Alternative currentness: Observed designation is live; actual current-through publisher marker not rechecked in this alternatives task.

### San Leandro, CA

**Primary standalone path unqualified**. Primary sample records: 0.

Primary publication: [https://ecode360.com/44065746](https://ecode360.com/44065746). Tested route: [https://ecode360.com/44065748](https://ecode360.com/44065748).

Evidence: [ecode360/STANDALONE-VALIDATION.json](ecode360/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `san-leandro-ca` entry.

Next action: Respect host stop and publisher access prerequisites. After authorized resumption, test one normal headed/passive browser or authorized publisher export; preserve fresh acquisition/selection/currentness evidence before parsing. Do not replay CUA bytes as standalone acquisition.

Remaining limits: Initial HTTP 403 challenge/access response; stopped before legal content. Passive/headed completion not tested.; Publisher PDF/Word availability varies by publication and login; documented credentialed API untested

Official alternative discovery: Official Government page links MunicipalCode; ballot-measure PDFs are proposed/amending instruments rather than complete code/Charter exports. No complete alternate qualified.

Alternative currentness: Standalone city page403; no currency inferred from search result or proposed measure.

### Santa Clara, CA

**Primary standalone path unqualified**. Primary sample records: 0.

Primary publication: [https://ecode360.com/47578663](https://ecode360.com/47578663). Tested route: [https://ecode360.com/47543489](https://ecode360.com/47543489).

Evidence: [ecode360/STANDALONE-VALIDATION.json](ecode360/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `santa-clara-ca` entry.

Next action: Respect host stop and publisher access prerequisites. After authorized resumption, test one normal headed/passive browser or authorized publisher export; preserve fresh acquisition/selection/currentness evidence before parsing. Do not replay CUA bytes as standalone acquisition.

Remaining limits: Initial HTTP 403 challenge/access response; stopped before legal content. Passive/headed completion not tested.; Publisher PDF/Word availability varies by publication and login; documented credentialed API untested

Official alternative discovery: Official Legistar item26-660 separately labels current Charter and proposed revisions. Current attachment downloaded200/29pages; visual first/last pages show TitleCHA through ArticleXVIII. PDF is raster-only on sampled pages and requires OCR; MunicipalCode remains separate.

Alternative currentness: Official item June9,2026 labels this current; first rendered page prints FridayJune5,2026. This is a dated current-labelled snapshot, not an independent October15 legal-currentness certificate.

Separate partial publication: `{"scope": "City Charter only; primary Municipal Code gap remains", "source_url": "https://santaclara.legistar.com/View.ashx?GUID=9FDBDA24-1C91-4A58-859B-2516966A0809&ID=15562338&M=F", "fresh_source_acquisition": "ordinary HTTP200 by companion official-source agent during this phase; copied with exact receipt/hash/origin, not prior CUA source", "source": {"path": "standalone-live/official-alternatives/santa-clara/santa-clara-current-charter.pdf", "sha256": "c732ecd755150ea472f927ab6d4aa61862f6708ffde96183a679d3288961934c", "bytes": 10200857}, "receipt": {"path": "standalone-live/official-alternatives/santa-clara/santa-clara-current-charter.pdf.receipt.json", "sha256": "12a3e3ca6464c783dc4ab9d501b4f71ed8a5a93f51ac1808d23425d782ab1e77", "bytes": 601}, "render": {"path": "standalone-live/official-alternatives/santa-clara/vision-page1/page.png", "sha256": "98ef0d64533c322e7c34dc46310a86ef2538f0ea873a3785651972368e46bf30", "bytes": 496366}, "ocr": {"path": "standalone-live/official-alternatives/santa-clara/vision-page1/ocr.json", "sha256": "4a88fb10879ae653366f7b54f203cf31aa0ace5a03ac58a49e84b1a76377a451", "bytes": 8625}, "visual_review": {"path": "standalone-live/official-alternatives/santa-clara/VISUAL-REVIEW.json", "sha256": "58bb26b405844009fa34ee707a658a602e3b3c4b34f98c72bff14c036ffce184", "bytes": 789}, "report": {"path": "standalone-live/official-alternatives/santa-clara/final-ocr-review-exports/report.json", "sha256": "2f1847f36f2c734b33bf8c731a6bff8592aef7d082c208c2bf265c0d49afcdbc", "bytes": 1301}, "json": {"path": "standalone-live/official-alternatives/santa-clara/final-ocr-review-exports/fulltext.json", "sha256": "68b7f2ba07d978bfedae5a991b6477ba2170288bcdb5b6d1e165cdbe54fb0251", "bytes": 4772}, "csv": {"path": "standalone-live/official-alternatives/santa-clara/final-ocr-review-exports/fulltext.csv", "sha256": "8e6669f3afc45f11aab1f7828fd4a1abe76adf51199cb4d2d0de4be7870300f1", "bytes": 2944}, "provenance": {"path": "standalone-live/official-alternatives/santa-clara/final-ocr-review-exports/provenance.jsonl", "sha256": "8d7cc783f58e38a94e849df60bd7621530419c48cf7a98435caac85a39017d62", "bytes": 4900}, "records": 5, "headers": 6, "unresolved_boundary_headers": 1, "pages_processed": [1], "total_pdf_pages": 29, "runtime": "native macOS PDFKit/Vision via Swift6.3.3 withSDK26.5; no cloud/Codex OCR", "outside_codex_accepted_bytes": true, "municipal_code_gap_closed": false, "whole_charter_parsed": false}`

### Santa Monica, CA

**Primary standalone path unqualified**. Primary sample records: 0.

Primary publication: [https://ecode360.com/42781804](https://ecode360.com/42781804). Tested route: [https://ecode360.com/42718485](https://ecode360.com/42718485).

Evidence: [ecode360/STANDALONE-VALIDATION.json](ecode360/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `santa-monica-ca` entry.

Next action: Respect host stop and publisher access prerequisites. After authorized resumption, test one normal headed/passive browser or authorized publisher export; preserve fresh acquisition/selection/currentness evidence before parsing. Do not replay CUA bytes as standalone acquisition.

Remaining limits: Initial HTTP 403 challenge/access response; stopped before legal content. Passive/headed completion not tested.; Publisher PDF/Word availability varies by publication and login; documented credentialed API untested

Official alternative discovery: Actual official homepage200 links eCodeSA5008. Search surfaced city-hosted litigation exhibits of older Charters/code excerpts; these historical/partial exhibits are not a current complete-code substitute.

Alternative currentness: Homepage designation current observation only.1941/1948Charter exhibit is historical, not downloaded as current code.

### Santa Rosa, CA

**Primary standalone path unqualified**. Primary sample records: 0.

Primary publication: [https://ecode360.com/42952195](https://ecode360.com/42952195). Tested route: [https://ecode360.com/42952196](https://ecode360.com/42952196).

Evidence: [ecode360/STANDALONE-VALIDATION.json](ecode360/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `santa-rosa-ca` entry.

Next action: Respect host stop and publisher access prerequisites. After authorized resumption, test one normal headed/passive browser or authorized publisher export; preserve fresh acquisition/selection/currentness evidence before parsing. Do not replay CUA bytes as standalone acquisition.

Remaining limits: Initial HTTP 429 challenge/access response; stopped before legal content. Passive/headed completion not tested.; Publisher PDF/Word availability varies by publication and login; documented credentialed API untested

Official alternative discovery: Official /152/City-Charter presents full CharterHTML. Standalone HTTP403 blocks qualification here; web tool can read it. Separate full municipal-code alternative not verified.

Alternative currentness: Primary page prints RevisedNovember2022, latest listed amendment effectiveJuly25,2023. No unlisted later amendment inference.

### Sonoma, CA

**Bounded standalone acquisition/export passed**. Primary sample records: 10.

Primary publication: [https://sonoma.municipal.codes/SMC](https://sonoma.municipal.codes/SMC). Tested route: [https://sonoma.municipal.codes/SMC/1.01.010](https://sonoma.municipal.codes/SMC/1.01.010).

Evidence: [municipal-codes/STANDALONE-VALIDATION.json](municipal-codes/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `sonoma-ca` entry.

Next action: Use ordinary headed legal capture or publisher Save UI on an approved bounded plan; stop on429/challenge and respect Retry-After. Reacquire independent inventories through a qualified transport before full collection.

Remaining limits: Whole corpus unvalidated; prior CUA independent inventory remains separate from standalone body acquisition; Additional publication-family scope, images/attachments and full disposition reconciliation pending

Official alternative discovery: Actual official CivicWeb MunicipalCode page200 still delegates to legacy CodePublishing/Sonoma. No complete city-hosted current export observed.

Alternative currentness: Legacy city link observed live; migration/current publisher redirect and currency remain for family collector.

### South San Francisco, CA

**Primary standalone path unqualified**. Primary sample records: 0.

Primary publication: [https://ecode360.com/43423521](https://ecode360.com/43423521). Tested route: [https://ecode360.com/43423522](https://ecode360.com/43423522).

Evidence: [ecode360/STANDALONE-VALIDATION.json](ecode360/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `south-san-francisco-ca` entry.

Next action: Respect host stop and publisher access prerequisites. After authorized resumption, test one normal headed/passive browser or authorized publisher export; preserve fresh acquisition/selection/currentness evidence before parsing. Do not replay CUA bytes as standalone acquisition.

Remaining limits: Initial HTTP 403 challenge/access response; stopped before legal content. Passive/headed completion not tested.; Publisher PDF/Word availability varies by publication and login; documented credentialed API untested

Official alternative discovery: Actual city MunicipalCode page200 designates eCodeSO5016 and separately links new laws. It states electronic version informational and official legislation definitive. No complete alternate city-hosted download verified.

Alternative currentness: City delegation current observation; no October15 legal-currentness guarantee or printed-code parity claim.

### Sunnyvale, CA

**Primary standalone path unqualified**. Primary sample records: 0.

Primary publication: [https://ecode360.com/SU5020](https://ecode360.com/SU5020). Tested route: [https://ecode360.com/42709867](https://ecode360.com/42709867).

Evidence: [ecode360/STANDALONE-VALIDATION.json](ecode360/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `sunnyvale-ca` entry.

Next action: Respect host stop and publisher access prerequisites. After authorized resumption, test one normal headed/passive browser or authorized publisher export; preserve fresh acquisition/selection/currentness evidence before parsing. Do not replay CUA bytes as standalone acquisition.

Remaining limits: Initial HTTP 403 challenge/access response; stopped before legal content. Passive/headed completion not tested.; Publisher PDF/Word availability varies by publication and login; documented credentialed API untested

Official alternative discovery: Official CharterReview page lists CityCharter and proposed2026ballot materials. No standalone city-hosted complete code/Charter download verified.

Alternative currentness: Primary search excerpts concern November2026proposed measures; current Charter must not be replaced with proposed ballot text. Standalone403.

### West Hollywood, CA

**Primary standalone path unqualified**. Primary sample records: 0.

Primary publication: [https://ecode360.com/43902431](https://ecode360.com/43902431). Tested route: [https://ecode360.com/43902463](https://ecode360.com/43902463).

Evidence: [ecode360/STANDALONE-VALIDATION.json](ecode360/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `west-hollywood-ca` entry.

Next action: Respect host stop and publisher access prerequisites. After authorized resumption, test one normal headed/passive browser or authorized publisher export; preserve fresh acquisition/selection/currentness evidence before parsing. Do not replay CUA bytes as standalone acquisition.

Remaining limits: Initial HTTP 403 challenge/access response; stopped before legal content. Passive/headed completion not tested.; Publisher PDF/Word availability varies by publication and login; documented credentialed API untested

Official alternative discovery: Official CityClerk page offers real-time MunicipalCode access; general DownloadDocuments contains hearing notices and individual documents, not verified full current code export.

Alternative currentness: Standalone city page403; search-indexed access description does not qualify independent complete download.

### Bellingham, WA

**Partial standalone; final check missing**. Primary sample records: 13.

Primary publication: [https://bellingham.municipal.codes/BMC](https://bellingham.municipal.codes/BMC). Tested route: [https://bellingham.municipal.codes/BMC/1.01.010](https://bellingham.municipal.codes/BMC/1.01.010).

Evidence: [municipal-codes/STANDALONE-VALIDATION.json](municipal-codes/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `bellingham-wa` entry.

Next action: Use ordinary headed legal capture or publisher Save UI on an approved bounded plan; stop on429/challenge and respect Retry-After. Reacquire independent inventories through a qualified transport before full collection.

Remaining limits: Initial legalstage200+expectednode+savedDOM parsed successfully; export429 and laterlegal429 make overall live job/endcheck incomplete. No further Bellingham requests performed.; Whole corpus unvalidated; prior CUA independent inventory remains separate from standalone body acquisition; Additional publication-family scope, images/attachments and full disposition reconciliation pending

Official alternative discovery: Official RulesAndRegulations links Charter, MunicipalCode and ordinances to municipal.codes. No independent city-hosted complete code/Charter copy verified.

Alternative currentness: Primary web read confirms publisher delegation; standalone official page403. Publisher export qualification remains separate family work.

### Burien, WA

**Manual publisher export + local importer passed**. Primary sample records: 6.

Primary publication: [https://www.codepublishing.com/WA/Burien/](https://www.codepublishing.com/WA/Burien/). Tested route: [https://www.codepublishing.com/WA/Burien/cgi/menuCompile.pl](https://www.codepublishing.com/WA/Burien/cgi/menuCompile.pl).

Evidence: [codepublishing/STANDALONE-VALIDATION.json](codepublishing/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `burien-wa` entry.

Next action: Operator opens ordinary publisher page, selects scope, Print/SaveSelections→HTML→Save, registers unchanged file with actual time/source URL, then runs local importer with explicit expected currency and1–3 observed chapter numbers. For unattended fresh acquisition, obtain a normal supported environment or documented sanctioned publisher integration.

Remaining limits: Fresh unattended export acquisition is challenged in this environment; no unattended network success established.; Only listed bounded chapters are parsed/qualified; other titles/families, unlinked status nodes, uncodified updates, images and incorporated PDFs remain outside scope.

Official alternative discovery: Official ConstructionCodes page offers individual code/amendment resources; no complete current municipal-code city-hosted export verified.

Alternative currentness: Standalone city page403; building-code lists/manuals not equivalent to complete municipal code.

### Everett, WA

**Bounded standalone acquisition/export passed**. Primary sample records: 1.

Primary publication: [https://everett.municipal.codes/EMC](https://everett.municipal.codes/EMC). Tested route: [https://everett.municipal.codes/EMC/1.01.010](https://everett.municipal.codes/EMC/1.01.010).

Evidence: [municipal-codes/STANDALONE-VALIDATION.json](municipal-codes/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `everett-wa` entry.

Next action: Use ordinary headed legal capture or publisher Save UI on an approved bounded plan; stop on429/challenge and respect Retry-After. Reacquire independent inventories through a qualified transport before full collection.

Remaining limits: Whole corpus unvalidated; prior CUA independent inventory remains separate from standalone body acquisition; Additional publication-family scope, images/attachments and full disposition reconciliation pending

Official alternative discovery: Official CharterReview quicklinks designates everett.municipal.codes Charter; committee PDFs are reports/proposals, not current complete Charter replacement.

Alternative currentness: Primary web read sees current Charter link but standalone403.2016committee reports are not inferred current text.

### Renton, WA

**Manual publisher export + local importer passed**. Primary sample records: 1.

Primary publication: [https://www.codepublishing.com/WA/Renton/](https://www.codepublishing.com/WA/Renton/). Tested route: [https://www.codepublishing.com/WA/Renton/cgi/menuCompile.pl](https://www.codepublishing.com/WA/Renton/cgi/menuCompile.pl).

Evidence: [codepublishing/STANDALONE-VALIDATION.json](codepublishing/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `renton-wa` entry.

Next action: Operator opens ordinary publisher page, selects scope, Print/SaveSelections→HTML→Save, registers unchanged file with actual time/source URL, then runs local importer with explicit expected currency and1–3 observed chapter numbers. For unattended fresh acquisition, obtain a normal supported environment or documented sanctioned publisher integration.

Remaining limits: Fresh unattended export acquisition is challenged in this environment; no unattended network success established.; Only listed bounded chapters are parsed/qualified; other titles/families, unlinked status nodes, uncodified updates, images and incorporated PDFs remain outside scope.

Official alternative discovery: Actual official PermitServices page200 delegates code to CodePublishing. MunicipalCode city route redirects to publisher403; no independent city-hosted complete export verified.

Alternative currentness: Observed city delegation current; labor-rules PDFs/individual amendments are partial and not complete code.

### SeaTac, WA

**Primary standalone path unqualified**. Primary sample records: 0.

Primary publication: [https://ecode360.com/SE4633](https://ecode360.com/SE4633). Tested route: [https://ecode360.com/51196398](https://ecode360.com/51196398).

Evidence: [ecode360/STANDALONE-VALIDATION.json](ecode360/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `seatac-wa` entry.

Next action: Respect host stop and publisher access prerequisites. After authorized resumption, test one normal headed/passive browser or authorized publisher export; preserve fresh acquisition/selection/currentness evidence before parsing. Do not replay CUA bytes as standalone acquisition.

Remaining limits: Initial HTTP 403 challenge/access response; stopped before legal content. Passive/headed completion not tested.; Publisher PDF/Word availability varies by publication and login; documented credentialed API untested

Official alternative discovery: Official court code link remains legacy CodePublishing; a city-hosted SeaTacMunicipalCode PDF search result covers Chapter15.105definitions only. Not a full-code substitute.

Alternative currentness: PartialPDF search excerpt labels adoptedOrd25-1008; not downloaded/qualified current. Standalone city link403.

### Tukwila, WA

**Primary standalone path unqualified**. Primary sample records: 0.

Primary publication: [https://ecode360.com/TU6948](https://ecode360.com/TU6948). Tested route: [https://ecode360.com/47209490](https://ecode360.com/47209490).

Evidence: [ecode360/STANDALONE-VALIDATION.json](ecode360/STANDALONE-VALIDATION.json); exact receipts, hashes, scope and currentness are in the `tukwila-wa` entry.

Next action: Respect host stop and publisher access prerequisites. After authorized resumption, test one normal headed/passive browser or authorized publisher export; preserve fresh acquisition/selection/currentness evidence before parsing. Do not replay CUA bytes as standalone acquisition.

Remaining limits: Initial HTTP 403 challenge/access response; stopped before legal content. Passive/headed completion not tested.; Publisher PDF/Word availability varies by publication and login; documented credentialed API untested

Official alternative discovery: Official city page delegates new code. CityRecords has explicitly old CompleteTukwilaMunicipalCode updatedFebruary2024. Direct oldPDF request returnedHTTP200withzero bytes; repeat after validator correction fails as empty source. Not usable current alternative.

Alternative currentness: Search source explicitly oldversion; December2025recodification means historical numbering must not be silently substituted for2026code. No current complete alternative qualified.

The separate Charter pilots add two Emeryville records and five Santa Clara records. They do not close either primary municipal-code gap. The official-alternatives package reports the Santa Clara download stage; the later eCode360 companion report adds the first-page OCR pilot.
