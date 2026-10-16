# Current source and validation matrix — October15,2026

30 outstanding jurisdictions in reviewed project handoff inventory; no current database audit. Live method qualification does not remove a jurisdiction from the collection backlog.

All30 have a bounded live acquisition → parser → export path. None is a completed jurisdiction corpus. Runtime results below apply to observed samples and environments, not a guarantee of future access.

| Jurisdiction | Current source | Tested records | Qualified path | Evidence |
|---|---|---:|---|---|
| Portland (ME) | [civicplus_pdf](https://portlandmaine.gov/city-code) | 13 | Verified Chrome/CUA index → HTTP PDF → parser → integrity verification | [Report](civicplus/E2E-VALIDATION.json) |
| Rockland (ME) | [civicplus_pdf](https://www.rocklandmaine.gov/288/Charter-Code-Ordinances) | 92 | HTTP official index → PDF bytes → parser → integrity verification | [Report](civicplus/E2E-VALIDATION.json) |
| Burien (WA) | [codepublishing](https://www.codepublishing.com/WA/Burien/) | 6 | CUA script → resolved chapter/frame DOM → acquisition CLI → clean/resumed parser exports | [Report](codepublishing/E2E-VALIDATION.json) |
| Flagstaff (AZ) | [codepublishing](https://www.codepublishing.com/AZ/Flagstaff/) | 5 | CUA script → resolved chapter/frame DOM → acquisition CLI → clean/resumed parser exports | [Report](codepublishing/E2E-VALIDATION.json) |
| Fremont (CA) | [codepublishing](https://www.codepublishing.com/CA/Fremont/) | 55 | CUA script → resolved chapter/frame DOM → acquisition CLI → clean/resumed parser exports | [Report](codepublishing/E2E-VALIDATION.json) |
| Renton (WA) | [codepublishing](https://www.codepublishing.com/WA/Renton/) | 1 | CUA script → resolved chapter/frame DOM → acquisition CLI → clean/resumed parser exports | [Report](codepublishing/E2E-VALIDATION.json) |
| San Carlos (CA) | [codepublishing](https://www.codepublishing.com/CA/SanCarlos/) | 10 | CUA script → resolved chapter/frame DOM → acquisition CLI → clean/resumed parser exports | [Report](codepublishing/E2E-VALIDATION.json) |
| Burlingame (CA) | [ecode360](https://ecode360.com/44587767) | 1 | CUA script → exact DOM source → importer → parser → verified JSON/CSV | [Report](ecode360/E2E-VALIDATION.json) |
| Emeryville (CA) | [ecode360](https://ecode360.com/47056325) | 7 | CUA script → exact DOM source → importer → parser → verified JSON/CSV | [Report](ecode360/E2E-VALIDATION.json) |
| Foster City (CA) | [ecode360](https://ecode360.com/FO4449) | 7 | CUA script → exact DOM source → importer → parser → verified JSON/CSV | [Report](ecode360/E2E-VALIDATION.json) |
| Half Moon Bay (CA) | [ecode360](https://ecode360.com/HA4470) | 10 | CUA script → exact DOM source → importer → parser → verified JSON/CSV | [Report](ecode360/E2E-VALIDATION.json) |
| Malibu (CA) | [ecode360](https://ecode360.com/44342329) | 28 | CUA script → exact DOM source → importer → parser → verified JSON/CSV | [Report](ecode360/E2E-VALIDATION.json) |
| San Leandro (CA) | [ecode360](https://ecode360.com/44065746) | 1 | CUA script → exact DOM source → importer → parser → verified JSON/CSV | [Report](ecode360/E2E-VALIDATION.json) |
| Santa Clara (CA) | [ecode360](https://ecode360.com/47578663) | 4 | CUA script → exact DOM source → importer → parser → verified JSON/CSV | [Report](ecode360/E2E-VALIDATION.json) |
| Santa Monica (CA) | [ecode360](https://ecode360.com/42781804) | 9 | CUA script → exact DOM source → importer → parser → verified JSON/CSV | [Report](ecode360/E2E-VALIDATION.json) |
| Santa Rosa (CA) | [ecode360](https://ecode360.com/42952195) | 13 | CUA script → exact DOM source → importer → parser → verified JSON/CSV | [Report](ecode360/E2E-VALIDATION.json) |
| SeaTac (WA) | [ecode360](https://ecode360.com/SE4633) | 12 | CUA script → exact DOM source → importer → parser → verified JSON/CSV | [Report](ecode360/E2E-VALIDATION.json) |
| South San Francisco (CA) | [ecode360](https://ecode360.com/43423521) | 8 | CUA script → exact DOM source → importer → parser → verified JSON/CSV | [Report](ecode360/E2E-VALIDATION.json) |
| Sunnyvale (CA) | [ecode360](https://ecode360.com/SU5020) | 8 | CUA script → exact DOM source → importer → parser → verified JSON/CSV | [Report](ecode360/E2E-VALIDATION.json) |
| Tukwila (WA) | [ecode360](https://ecode360.com/TU6948) | 16 | CUA script → exact DOM source → importer → parser → verified JSON/CSV | [Report](ecode360/E2E-VALIDATION.json) |
| West Hollywood (CA) | [ecode360](https://ecode360.com/43902431) | 10 | CUA script → exact DOM source → importer → parser → verified JSON/CSV | [Report](ecode360/E2E-VALIDATION.json) |
| Cupertino (CA) | [gridics](https://codehub.gridics.com/us/ca/cupertino#/90d493fe-25f4-4aef-a519-710b1e0055c6) | 59 | Standalone Playwright or CUA → UUID DOM → resumable parser → verified exports | [Report](gridics/E2E-VALIDATION.json) |
| King County (WA) | [king_county_html](https://kingcounty.gov/en/dept/council/governance-leadership/county-legislation-codes/king-county-code) | 261 | Fresh CUA landing discovery → standalone HTTP original HTML/Word bytes →3 document parser runs | [Report](bulk-and-official-html/E2E-VALIDATION.json) |
| Bellingham (WA) | [municipal_codes](https://bellingham.municipal.codes/BMC) | 18 | CUA script → Contents and chapter DOM → stable section-card parser → verified exports | [Report](municipal-codes/E2E-VALIDATION.json) |
| Berkeley (CA) | [municipal_codes](https://berkeley.municipal.codes/BMC) | 25 | CUA script → Contents and chapter DOM → stable section-card parser → verified exports | [Report](municipal-codes/E2E-VALIDATION.json) |
| Everett (WA) | [municipal_codes](https://everett.municipal.codes/EMC) | 33 | CUA script → Contents and chapter DOM → stable section-card parser → verified exports | [Report](municipal-codes/E2E-VALIDATION.json) |
| Petaluma (CA) | [municipal_codes](https://petaluma.municipal.codes/Code) | 10 | CUA script → Contents and chapter DOM → stable section-card parser → verified exports | [Report](municipal-codes/E2E-VALIDATION.json) |
| Sonoma (CA) | [municipal_codes](https://sonoma.municipal.codes/SMC) | 39 | CUA script → Contents and chapter DOM → stable section-card parser → verified exports | [Report](municipal-codes/E2E-VALIDATION.json) |
| Daly City (CA) | [municode](https://library.municode.com/ca/daly_city/codes/code_of_ordinances) | 3 | Live client/publication API discovery → TOC →3 exact content requests → parser; CUA and standalone adoption-body comparison | [Report](bulk-and-official-html/E2E-VALIDATION.json) |
| San Mateo (CA) | [openlaw_xml](https://law.cityofsanmateo.org/) | 135 | Resolve repository HEAD → pinned archive → Git blob verification → bounded actual XInclude traversal → XML parser | [Report](bulk-and-official-html/E2E-VALIDATION.json) |

## Bellingham (WA)

2,846 primary navigation nodes; 18 current records including difficult samples; primary inventory, displayed currency and chapter bodies equal before/after.

**Runtime status:** cua: pass; direct http: blocked_http_403; standalone browser: blocked_http_403.

**Remaining:** Full inventory node classification, including substantive parent bodies, attachments, editorial/reference scope; Extra publication-family substantive collection and source/version closure; Full corpus acquisition, deduplication and disposition reconciliation; no full extraction performed; Official city route confirmation limitations remain as recorded in baseline report; Charter Contents challenge retained; primary inventory postcheck recovered in distinct accepted attempt; Map/image readable text has not been independently transcribed or OCR-validated; placeholder and alt/source retention do not qualify image text completeness

[Runnable package](municipal-codes/README.md) · [Evidence report](municipal-codes/E2E-VALIDATION.json)

**Observed source marker:** The Bellingham Municipal Code is current through Ordinance 2026-08-022, passed August 24, 2026.

Additional observed publication families (scope unresolved):

- [family-charter](https://bellingham.municipal.codes/Charter/contents): capture not accepted; unknown navigation nodes.

## Berkeley (CA)

5,238 primary navigation nodes; 25 current records including difficult samples; primary inventory, displayed currency and chapter bodies equal before/after.

**Runtime status:** cua: pass; direct http: blocked_http_403; standalone browser: blocked_http_403.

**Remaining:** Full inventory node classification, including substantive parent bodies, attachments, editorial/reference scope; Extra publication-family substantive collection and source/version closure; Full corpus acquisition, deduplication and disposition reconciliation; no full extraction performed; Official city route confirmation limitations remain as recorded in baseline report; Map/image readable text has not been independently transcribed or OCR-validated; placeholder and alt/source retention do not qualify image text completeness

[Runnable package](municipal-codes/README.md) · [Evidence report](municipal-codes/E2E-VALIDATION.json)

**Observed source marker:** The Berkeley Municipal Code is current through Ordinance 8031-NS, passed July 28, 2026.

Additional observed publication families (scope unresolved):

- [family-charter](https://berkeley.municipal.codes/Charter/contents): capture accepted; 139 navigation nodes.

## Burien (WA)

6 current records; source currency equal before/after; clean/resumed exports and CSV/JSON agree.

**Runtime status:** cua: pass; standalone browser: blocked_http_403.

**Remaining:** Complete publication/family inventory and whole-corpus version coherence; standalone transport blocked; broader images/spans/incorporated PDFs.

[Runnable package](codepublishing/README.md) · [Evidence report](codepublishing/E2E-VALIDATION.json)

**Observed source marker:** The Burien Municipal Code is current through Ordinance 905, and legislation passed through July 27, 2026.

## Burlingame (CA)

Current chapter sample: 1 records; requested identity, retained source hashes and all source-text comparisons pass.

**Runtime status:** cua: pass; direct http: blocked; standalone browser: not_run.

**Remaining:** Complete publication/family inventory and whole-run edition reconciliation; broader real tables/images/appendices and visual semantic review; standalone browser Foster blocked, other13 not run.

[Runnable package](ecode360/README.md) · [Evidence report](ecode360/E2E-VALIDATION.json)

[Exact tested source](https://ecode360.com/44507298)

**Observed source marker:** {"code_id": "332192", "currency_raw": "2026-04-20", "customer_id": "BU4910"}

## Cupertino (CA)

Three standalone routes HTTP200; intentional acquisition resume;65 Title1 source fingerprints equal CUA;59 records/66 rendered nodes;2,687 observed navigation identities;2,621 bodies unresolved.

**Runtime status:** cua: pass; standalone browser: pass.

**Remaining:** Legal current-through unknown; no independent publisher total or exhaustive route validity.35 compound/descendant routes unqualified;2,621 bodies unacquired. Full observed tree expansion does not mean complete legal corpus.

[Runnable package](gridics/README.md) · [Evidence report](gridics/E2E-VALIDATION.json)

## Daly City (CA)

2,506-node TOC;3 provisions including table and appendix; publication/tree stable before/after; adoption body equals both browser runtimes.

**Runtime status:** direct api: pass; standalone browser: adoption-body parity pass; cua: official-route and adoption-body parity pass.

**Remaining:** Full-node acquisition/reconciliation; rendered parity for table/appendix samples; uncodified ordinances separately inventoried; whole-publication acceptance.

[Runnable package](bulk-and-official-html/README.md) · [Evidence report](bulk-and-official-html/E2E-VALIDATION.json)

Original registry source superseded by current publisher; use current source and package above.

## Emeryville (CA)

Current chapter sample: 7 records; requested identity, retained source hashes and all source-text comparisons pass.

**Runtime status:** cua: pass; direct http: blocked; standalone browser: not_run.

**Remaining:** Complete publication/family inventory and whole-run edition reconciliation; broader real tables/images/appendices and visual semantic review; standalone browser Foster blocked, other13 not run.

[Runnable package](ecode360/README.md) · [Evidence report](ecode360/E2E-VALIDATION.json)

[Exact tested source](https://ecode360.com/46989352)

**Observed source marker:** {"code_id": "336039", "currency_raw": "2026-06-02", "customer_id": "EM4426"}

## Everett (WA)

3,742 primary navigation nodes; 33 current records including difficult samples; primary inventory, displayed currency and chapter bodies equal before/after.

**Runtime status:** cua: pass; direct http: blocked_http_403; standalone browser: blocked_http_403.

**Remaining:** Full inventory node classification, including substantive parent bodies, attachments, editorial/reference scope; Extra publication-family substantive collection and source/version closure; Full corpus acquisition, deduplication and disposition reconciliation; no full extraction performed; Official city route confirmation limitations remain as recorded in baseline report; Map/image readable text has not been independently transcribed or OCR-validated; placeholder and alt/source retention do not qualify image text completeness

[Runnable package](municipal-codes/README.md) · [Evidence report](municipal-codes/E2E-VALIDATION.json)

**Observed source marker:** 1 For statutory provisions authorizing cities to codify their ordinances, see RCW 35.21.500 — 35.21.570 . For the Charter provisions requiring the mayor to cause the annual codification of ordinances, see § 15.6 .

Additional observed publication families (scope unresolved):

- [family-charter](https://everett.municipal.codes/Charter/contents): capture accepted; 131 navigation nodes.

## Flagstaff (AZ)

5 current records; source currency equal before/after; clean/resumed exports and CSV/JSON agree.

**Runtime status:** cua: pass; standalone browser: blocked_http_403.

**Remaining:** Complete publication/family inventory and whole-corpus version coherence; standalone transport blocked; broader images/spans/incorporated PDFs.

[Runnable package](codepublishing/README.md) · [Evidence report](codepublishing/E2E-VALIDATION.json)

**Observed source marker:** The Flagstaff City Charter and City Code are current through Ordinance 2026-19, passed August 25, 2026.

## Foster City (CA)

Current chapter sample: 7 records; requested identity, retained source hashes and all source-text comparisons pass.

**Runtime status:** cua: pass; direct http: blocked; standalone browser: blocked.

**Remaining:** Complete publication/family inventory and whole-run edition reconciliation; broader real tables/images/appendices and visual semantic review; standalone browser Foster blocked, other13 not run. Separately resolve Estero Municipal Improvement District Code scope.

[Runnable package](ecode360/README.md) · [Evidence report](ecode360/E2E-VALIDATION.json)

[Exact tested source](https://ecode360.com/51404426)

Original registry source superseded by current publisher; use current source and package above.

**Observed source marker:** {"code_id": "337727", "currency_raw": "2026-01-26", "customer_id": "FO4449"}

## Fremont (CA)

55 current records; source currency equal before/after; clean/resumed exports and CSV/JSON agree.

**Runtime status:** cua: pass; standalone browser: blocked_http_403.

**Remaining:** Complete publication/family inventory and whole-corpus version coherence; standalone transport blocked; broader images/spans/incorporated PDFs.

[Runnable package](codepublishing/README.md) · [Evidence report](codepublishing/E2E-VALIDATION.json)

**Observed source marker:** The Fremont Municipal Code is current through Ordinance 02-2026, passed May 5, 2026.

## Half Moon Bay (CA)

Current chapter sample: 10 records; requested identity, retained source hashes and all source-text comparisons pass.

**Runtime status:** cua: pass; direct http: blocked; standalone browser: not_run.

**Remaining:** Complete publication/family inventory and whole-run edition reconciliation; broader real tables/images/appendices and visual semantic review; standalone browser Foster blocked, other13 not run.

[Runnable package](ecode360/README.md) · [Evidence report](ecode360/E2E-VALIDATION.json)

[Exact tested source](https://ecode360.com/47025425)

**Observed source marker:** {"code_id": "336191", "currency_raw": "2026-05-05", "customer_id": "HA4470"}

## King County (WA)

121 Title1 +20 Title2A +120 Charter records. Original CP1252 bytes preserved; Word corroborates source numbering/date discrepancies.

**Runtime status:** direct http: pass after CUA discovery capture; cua: official landing discovery pass; standalone browser: full discovery not qualified.

**Remaining:** Resolve publisher numbering/date conflicts; Title21A issues and broader Word/HTML paragraph parity remain; full discovery is hybrid CUA+HTTP, not wholly unattended.

[Runnable package](bulk-and-official-html/README.md) · [Evidence report](bulk-and-official-html/E2E-VALIDATION.json)

## Malibu (CA)

Current chapter sample: 28 records; requested identity, retained source hashes and all source-text comparisons pass.

**Runtime status:** cua: pass; direct http: blocked; standalone browser: not_run.

**Remaining:** Complete publication/family inventory and whole-run edition reconciliation; broader real tables/images/appendices and visual semantic review; standalone browser Foster blocked, other13 not run.

[Runnable package](ecode360/README.md) · [Evidence report](ecode360/E2E-VALIDATION.json)

[Exact tested source](https://ecode360.com/44331146)

**Observed source marker:** {"code_id": "336335", "currency_raw": "2026-06-22", "customer_id": "MA5043"}

## Petaluma (CA)

2,860 primary navigation nodes; 10 current records including difficult samples; primary inventory, displayed currency and chapter bodies equal before/after.

**Runtime status:** cua: pass; direct http: blocked_http_403; standalone browser: blocked_http_403.

**Remaining:** Full inventory node classification, including substantive parent bodies, attachments, editorial/reference scope; Extra publication-family substantive collection and source/version closure; Full corpus acquisition, deduplication and disposition reconciliation; no full extraction performed; Official city route confirmation limitations remain as recorded in baseline report; Map/image readable text has not been independently transcribed or OCR-validated; placeholder and alt/source retention do not qualify image text completeness

[Runnable package](municipal-codes/README.md) · [Evidence report](municipal-codes/E2E-VALIDATION.json)

**Observed source marker:** The Petaluma Municipal Code is current through Ordinance 2931 NCS, passed July 6, 2026.

Additional observed publication families (scope unresolved):

- [family-charter](https://petaluma.municipal.codes/Charter/contents): capture accepted; 100 navigation nodes.

- [family-smartcode](https://petaluma.municipal.codes/SmartCode/contents): capture accepted; 127 navigation nodes.

- [family-zoningords](https://petaluma.municipal.codes/ZoningOrds/contents): capture accepted; 328 navigation nodes.

## Portland (ME)

44 labelled assets;13 Chapter13 records; standalone/CUA ordered provisions equal; source-bound table and line recoveries.

**Runtime status:** cua: pass; standalone browser: pass; direct http: PDF pass; index certificate-chain failure.

**Remaining:** Unreadable symbol, other PDF tables/layouts and unacquired documents; integrity PASS does not establish semantic completeness.

[Runnable package](civicplus/README.md) · [Evidence report](civicplus/E2E-VALIDATION.json)

## Renton (WA)

1 current records; source currency equal before/after; clean/resumed exports and CSV/JSON agree.

**Runtime status:** cua: pass; standalone browser: blocked_http_403.

**Remaining:** Complete publication/family inventory and whole-corpus version coherence; standalone transport blocked; broader images/spans/incorporated PDFs.

[Runnable package](codepublishing/README.md) · [Evidence report](codepublishing/E2E-VALIDATION.json)

**Observed source marker:** The Renton Municipal Code is current through Ordinance 6197, passed August 10, 2026.

## Rockland (ME)

21-document index; fresh Chapter1 and Charter PDFs;92 records; start/end inventory coherent.

**Runtime status:** direct http: pass; cua: not_needed_for_qualified_HTTP_path; standalone browser: not_needed_for_qualified_HTTP_path.

**Remaining:** Obscured Charter text, microscopic markers, unnumbered-body classification and unacquired chapters; integrity PASS does not establish semantic completeness.

[Runnable package](civicplus/README.md) · [Evidence report](civicplus/E2E-VALIDATION.json)

## San Carlos (CA)

10 current records; source currency equal before/after; clean/resumed exports and CSV/JSON agree.

**Runtime status:** cua: pass; standalone browser: blocked_http_403.

**Remaining:** Complete publication/family inventory and whole-corpus version coherence; standalone transport blocked; broader images/spans/incorporated PDFs.

[Runnable package](codepublishing/README.md) · [Evidence report](codepublishing/E2E-VALIDATION.json)

**Observed source marker:** The San Carlos Municipal Code is current through Ordinance 1637, passed June 22, 2026.

## San Leandro (CA)

Current chapter sample: 1 records; requested identity, retained source hashes and all source-text comparisons pass.

**Runtime status:** cua: pass; direct http: blocked; standalone browser: not_run.

**Remaining:** Complete publication/family inventory and whole-run edition reconciliation; broader real tables/images/appendices and visual semantic review; standalone browser Foster blocked, other13 not run.

[Runnable package](ecode360/README.md) · [Evidence report](ecode360/E2E-VALIDATION.json)

[Exact tested source](https://ecode360.com/44065748)

**Observed source marker:** {"code_id": "337882", "currency_raw": "2026-07-20", "customer_id": "SA5044"}

## San Mateo (CA)

All291 archive Git blobs verified;96 Charter +39 Title1 records.

**Runtime status:** direct http archive: pass; cua: not_needed; standalone browser: not_needed.

**Remaining:** Only declared XML include subset parsed; mixed own-body/include files deliberately rejected; commit reproducibility does not establish legal currency.

[Runnable package](bulk-and-official-html/README.md) · [Evidence report](bulk-and-official-html/E2E-VALIDATION.json)

## Santa Clara (CA)

Current chapter sample: 4 records; requested identity, retained source hashes and all source-text comparisons pass.

**Runtime status:** cua: pass; direct http: blocked; standalone browser: not_run.

**Remaining:** Complete publication/family inventory and whole-run edition reconciliation; broader real tables/images/appendices and visual semantic review; standalone browser Foster blocked, other13 not run.

[Runnable package](ecode360/README.md) · [Evidence report](ecode360/E2E-VALIDATION.json)

[Exact tested source](https://ecode360.com/47543489)

**Observed source marker:** {"code_id": "329535", "currency_raw": "2026-01-27", "customer_id": "SA4626"}

## Santa Monica (CA)

Current chapter sample: 9 records; requested identity, retained source hashes and all source-text comparisons pass.

**Runtime status:** cua: pass; direct http: blocked; standalone browser: not_run.

**Remaining:** Complete publication/family inventory and whole-run edition reconciliation; broader real tables/images/appendices and visual semantic review; standalone browser Foster blocked, other13 not run.

[Runnable package](ecode360/README.md) · [Evidence report](ecode360/E2E-VALIDATION.json)

[Exact tested source](https://ecode360.com/42718485)

**Observed source marker:** {"code_id": "336847", "currency_raw": "2026-07-28", "customer_id": "SA5008"}

## Santa Rosa (CA)

Current chapter sample: 13 records; requested identity, retained source hashes and all source-text comparisons pass.

**Runtime status:** cua: pass; direct http: blocked; standalone browser: not_run.

**Remaining:** Complete publication/family inventory and whole-run edition reconciliation; broader real tables/images/appendices and visual semantic review; standalone browser Foster blocked, other13 not run.

[Runnable package](ecode360/README.md) · [Evidence report](ecode360/E2E-VALIDATION.json)

[Exact tested source](https://ecode360.com/42952196)

**Observed source marker:** {"code_id": "337811", "currency_raw": "2026-09-15", "customer_id": "SA5009"}

## SeaTac (WA)

Current chapter sample: 12 records; requested identity, retained source hashes and all source-text comparisons pass.

**Runtime status:** cua: pass; direct http: blocked; standalone browser: not_run.

**Remaining:** Complete publication/family inventory and whole-run edition reconciliation; broader real tables/images/appendices and visual semantic review; standalone browser Foster blocked, other13 not run.

[Runnable package](ecode360/README.md) · [Evidence report](ecode360/E2E-VALIDATION.json)

[Exact tested source](https://ecode360.com/51196398)

Original registry source superseded by current publisher; use current source and package above.

**Observed source marker:** {"code_id": "337588", "currency_raw": "2026-09-30", "customer_id": "SE4633"}

## Sonoma (CA)

2,177 primary navigation nodes; 39 current records including difficult samples; primary inventory, displayed currency and chapter bodies equal before/after.

**Runtime status:** cua: pass; direct http: blocked_http_403; standalone browser: blocked_http_403.

**Remaining:** Full inventory node classification, including substantive parent bodies, attachments, editorial/reference scope; Extra publication-family substantive collection and source/version closure; Full corpus acquisition, deduplication and disposition reconciliation; no full extraction performed; Official city route confirmation limitations remain as recorded in baseline report; Map/image readable text has not been independently transcribed or OCR-validated; placeholder and alt/source retention do not qualify image text completeness

[Runnable package](municipal-codes/README.md) · [Evidence report](municipal-codes/E2E-VALIDATION.json)

**Observed source marker:** The Sonoma Municipal Code is current through Ordinance 13-2025, passed December 3, 2025.

## South San Francisco (CA)

Current chapter sample: 8 records; requested identity, retained source hashes and all source-text comparisons pass.

**Runtime status:** cua: pass; direct http: blocked; standalone browser: not_run.

**Remaining:** Complete publication/family inventory and whole-run edition reconciliation; broader real tables/images/appendices and visual semantic review; standalone browser Foster blocked, other13 not run.

[Runnable package](ecode360/README.md) · [Evidence report](ecode360/E2E-VALIDATION.json)

[Exact tested source](https://ecode360.com/43423522)

**Observed source marker:** {"code_id": "336974", "currency_raw": "2026-09-09", "customer_id": "SO5016"}

## Sunnyvale (CA)

Current chapter sample: 8 records; requested identity, retained source hashes and all source-text comparisons pass.

**Runtime status:** cua: pass; direct http: blocked; standalone browser: not_run.

**Remaining:** Complete publication/family inventory and whole-run edition reconciliation; broader real tables/images/appendices and visual semantic review; standalone browser Foster blocked, other13 not run.

[Runnable package](ecode360/README.md) · [Evidence report](ecode360/E2E-VALIDATION.json)

[Exact tested source](https://ecode360.com/42709867)

**Observed source marker:** {"code_id": "337833", "currency_raw": "2026-08-11", "customer_id": "SU5020"}

## Tukwila (WA)

Current chapter sample: 16 records; requested identity, retained source hashes and all source-text comparisons pass.

**Runtime status:** cua: pass; direct http: blocked; standalone browser: not_run.

**Remaining:** Complete publication/family inventory and whole-run edition reconciliation; broader real tables/images/appendices and visual semantic review; standalone browser Foster blocked, other13 not run.

[Runnable package](ecode360/README.md) · [Evidence report](ecode360/E2E-VALIDATION.json)

[Exact tested source](https://ecode360.com/47209490)

**Observed source marker:** {"code_id": "332495", "currency_raw": "2026-05-18", "customer_id": "TU6948"}

## West Hollywood (CA)

Current chapter sample: 10 records; requested identity, retained source hashes and all source-text comparisons pass.

**Runtime status:** cua: pass; direct http: blocked; standalone browser: not_run.

**Remaining:** Complete publication/family inventory and whole-run edition reconciliation; broader real tables/images/appendices and visual semantic review; standalone browser Foster blocked, other13 not run.

[Runnable package](ecode360/README.md) · [Evidence report](ecode360/E2E-VALIDATION.json)

[Exact tested source](https://ecode360.com/43902463)

**Observed source marker:** {"code_id": "336663", "currency_raw": "2026-06-29", "customer_id": "WE5031"}
