# Technical implementation tasks

Use these as work items for the technical team. Priorities describe prerequisites for this extraction assignment, not incidents in the imported corpus. No current production code was changed in preparing the handoff.

## Common work

| ID | Priority | Work item | Completion evidence |
|---|---|---|---|
| C01 | P1 | Implement publication inventory, source-node identities and explicit scope/dispositions | Full independently enumerated source tree reconciles to output; parent bodies and repeated printed locators survive |
| C02 | P1 | Implement a semantic HTML/XML serializer | Tables/spans, nesting, notes, notation and image order survive; each source block appears once |
| C03 | P1 | Separate acquisition from replayable parsing; bind checkpoints to jurisdiction, family, version and parser/config identity | Interrupted and clean replay agree; old-version checkpoint cannot silently mix with a new snapshot |
| C04 | P1 | Record source revision/currency and raw artifacts with hashes | Complete raw-to-record lineage and no unexplained version changes |
| C05 | P1 | Deliver OUTPUT-CONTRACT.md artifacts and independent validation | Per-source-node coverage, deterministic exports and evidence-backed exception decisions |

The current browser checkpoint validates only jurisdiction slug on load. Cache keys are primarily URLs, which can serve different publication revisions over time. Add explicit run/version binding rather than treating an old cache as a current publication snapshot.

## Reproduced current code failures

All six observations are reproduced in `regression-results.json` by `regression_probes.py`. They use synthetic fixtures or exact configured route patterns; they are not claims that every source has the same DOM shape.

| ID | Affected source | Observed behavior | Required repair and regression criterion |
|---|---|---|---|
| R01 | Municipal.codes Bellingham | `/BMC/contents` root rejects a valid `/BMC/1.01.010` descendant | Store discovery URL and publication boundary separately; allow valid BMC nodes and reject other publications |
| R02 | Municipal.codes Everett | `/EMC/contents` root rejects a valid `/EMC/1.01.010` descendant | Same boundary repair, exercised against Everett configuration |
| R03 | Municipal.codes | A pure Contents page with a main heading emits one full-text record | Remove permissive main-text fallback; section cards or explicit substantive-body evidence must control emission |
| R04 | eCode360 | Two different publication/source nodes with identical printed labels collapse to one record | Use publication + source node identity; remove number-only queue suppression that can skip distinct nodes |
| R05 | King County | Heading paragraph is retained but following body paragraph/table is dropped | Parse the complete section DOM range through the next true legal section boundary |
| R06 | Gridics | A paragraph nested in a list item is output twice | Serialize the semantic container once, preserving nesting without descendant double counting |

Relevant implementation anchors: `BrowserVendorCollector._allowed`, `_sections`, `_add`, `collect`; `kingcounty_code.parse_title_sections`; `gridics_codehub.parse_sections_html`.

## Additional source-specific work

| ID | Source type | Work item | Required test coverage |
|---|---|---|---|
| E01 | eCode360 | Return actual section IDs/URLs from parser; constrain crawl to publication TOC membership | Same chapter from multiple URLs, repeated printed locators in different families, substantive parent/appendix bodies |
| L01 | Code Publishing | Explicit frame traversal and hash-route handling; enforce jurisdiction path boundary | Foster City ordinary HTML, Renton hash/Roman numbering, Flagstaff frames/four-part numbers |
| L02 | Code Publishing | Broaden legal body detection beyond narrow numeric headings | Charter/handbook families, unnumbered intro, appendix, table; disposition for empty/reserved nodes |
| M01 | Municipal.codes | Requalify Berkeley, Everett, Sonoma samples using current card parser after route/fallback fixes | Individual section cards emitted, contents excluded, canonical identities stable across chapter/section routes |
| P01 | Portland PDFs | Replace first-large-widget heuristic with identified City Code collection discovery | Widget reordering and changing membership do not select unrelated documents; preserve labels and source URLs |
| P02 | CivicPlus PDFs | Layout-aware PDF segmentation, header/footer removal and page-continuation assembly | Portland Chapter 13 repeated revision headings; Rockland heading markers; tables, mixed/OCR pages |
| P03 | Rockland | Charter family and parser profile | Charter provisions accounted independently of chapter-section regex; zero parsed records cannot pass |
| X01 | San Mateo XML | Parameterize repository commit and inventory publication roots | Code plus any in-scope additional roots; commit/date distinction; complete archive membership |
| X02 | San Mateo XML | Preserve XML structure and inspect nonstandard/nested content | Lists/tables/notes, nested section structures if present, substantive containers, includes/references if present |
| G01 | Gridics | Complete UUID inventory, route-specific readiness and navigation controls | Non-anchor/virtualized tree branches, stale prior route, section identity, nested lists and tables |
| D01 | Daly City | Source-backed number/name and official current publisher confirmation | Adoption section with nonblank source-backed identity; long section/table/appendix and error-shell rejection |
| K01 | King County | Decode original bytes and confirm current fallback fixes retained anomalies | Windows-1252 punctuation and UTF-8; no silent replacement/control characters |
| K02 | King County | Include Charter inventory and qualify alphanumeric section variants | Separate Charter parser/profile; actual title/section patterns and source-backed anchors |

## Pilot sequence and release criteria

Start C01–C04 before expanding any collector. R01–R06 are concrete first repair tasks with bundled reproductions. Implementing one fix does not establish the rest of that family's completeness.

Use Half Moon Bay for eCode360 ordinary sections; discover a real repeated-identity/multi-family case for identity validation. Use San Mateo's ordinary XML title plus structurally difficult material. Qualify all three Code Publishing navigation profiles separately. Use Berkeley/Everett plus a known multi-card Municipal.codes sample. Use Cupertino's nested/async cases. Use King County's multi-paragraph sections and Charter. Use Daly City's missing-identity example. Use Portland Chapter 13 and Rockland's Charter and a table-heavy document for PDF qualification.

For each pilot the tech team should provide the raw inventory, raw acquisition, parsed output, node reconciliation, failure list and comparison evidence. After acceptance, repeat source discovery and representative checks for every mapped jurisdiction before a full collection. The shared adapter saves implementation work; it does not remove per-jurisdiction scope and coverage validation.

## Evidence interpretation

- Historical sample failures describe retained August exports; some parser code has since evolved. Reproduce against current raw source before attributing every historical failure to current code.
- The six probes target current code behavior. Their desired outcomes are acceptance criteria the repair should satisfy.
- Static code review identified additional risks such as flattened XML and narrow heading patterns. Those require source-specific fixtures; they are not asserted counts of missing live provisions.
- The diagnostic auditor flags possible anomalies. Repeated numbers and unnumbered bodies may be legitimate and must be adjudicated, never automatically deleted.
