# Local code extraction handoff

Prepared October 15, 2026 for the technical team.

The 30 remaining jurisdictions fall into eight source types. Build and qualify one extraction path for each type, then apply it to the mapped jurisdictions with publication-specific inventories. The largest reusable components cover eCode360, legacy Code Publishing, and Municipal.codes: together they account for 24 jurisdictions.

Existing adapters provide useful parsing and transport foundations. They are not accepted complete extractors for this backlog. Six synthetic offline checks reproduce current implementation failures, and retained pilot outputs reveal additional metadata and PDF segmentation problems. Repair these before using sample readiness labels to authorize full collection.

The deliverable from the technical team is a validated, reproducible corpus package per jurisdiction. Database work and ordinance-update collection are outside this assignment.

## Package contents

| File | Purpose |
|---|---|
| [SOURCE-MAP.md](SOURCE-MAP.md) | All 30 jurisdictions grouped by source type, with starting URLs and historical evidence |
| [routes.json](routes.json) | Machine-readable mapping; planning input, not a production enablement registry |
| [IMPLEMENTATION-TASKS.md](IMPLEMENTATION-TASKS.md) | Repair backlog, implementation order and targeted acceptance checks |
| [OUTPUT-CONTRACT.md](OUTPUT-CONTRACT.md) | Required artifacts, source-node accounting, provenance and completion criteria |
| [handoff_tools.py](handoff_tools.py) | Offline plan, retained-sample diagnostics and bundle hash verification |
| [regression_probes.py](regression_probes.py) | Six reproducible offline criteria against the existing adapter code |
| [regression-results.json](regression-results.json) | Observed failures in the code snapshot |
| [sample-diagnostics.json](sample-diagnostics.json) | Automated warning inventory over 288 retained sample rows |
| `samples/<jurisdiction>/` | Historical sample output, source validation, collector receipt |
| `reference-code/` | Unmodified snapshot of existing adapters, manager and selected tests |
| [SOURCE-NOTES.md](SOURCE-NOTES.md) | Evidence dates, publisher links and limits of bundled reference code |

## Source groups

| Source type | Count | Jurisdictions | Primary acquisition unit |
|---|---:|---|---|
| eCode360 | 12 | Burlingame, Emeryville, Half Moon Bay, Malibu, San Leandro, Santa Clara, Santa Monica, Santa Rosa, South San Francisco, Sunnyvale, West Hollywood, Tukwila | Rendered chapter or section container, identified by publisher node |
| Legacy Code Publishing | 7 | Foster City, Fremont, San Carlos, Flagstaff, Burien, Renton, SeaTac | Chapter HTML after resolving ordinary, framed or hash-route navigation |
| Municipal.codes | 5 | Berkeley, Petaluma, Sonoma, Bellingham, Everett | Rendered chapter containing individually identified section cards |
| CivicPlus PDF collections | 2 | Portland ME, Rockland ME | Official chapter/document PDF plus its landing-page inventory |
| Open Law bulk XML | 1 | San Mateo | Official repository snapshot at a pinned commit |
| Gridics CodeHUB | 1 | Cupertino | Rendered chapter or section route with UUID identities |
| eLaws HTML | 1 | Daly City | Published section HTML |
| King County first-party HTML | 1 | King County | Official title HTML, plus separately inventoried publications |

No remaining jurisdiction maps to Municode in the reviewed registry. Several original research guesses were superseded by eCode360, Municipal.codes, Gridics or Open Law routes. Reconfirm those assignments from the official jurisdiction landing page at project kickoff.

## Shared extraction design

Separate acquisition, parsing and validation. Acquisition retains immutable source bytes or rendered DOM snapshots, response metadata and inventory identities. Parsing consumes those retained artifacts without needing the network. Validation compares parsed records to the independently retained publication inventory and to rendered source examples.

Use this progression per publication:

1. **Discover.** Follow the official city/county link to its current publisher. Record the redirect chain, jurisdiction identity, publication family, revision/current-through text and access method. Inventory every linked publication and classify its scope explicitly.
2. **Freeze the inventory.** Enumerate the complete source hierarchy and record identifiers, parents, order and source URLs. Distinguish containers, numbered sections, substantive unnumbered bodies, reserved/repealed nodes and editorial material. An extraction result cannot serve as its own completeness denominator.
3. **Acquire.** Save raw bytes/DOM with SHA-256 and retrieval metadata. Use the same source version throughout where available. For moving publications, compare revision markers and inventories at start/end and reconcile changes before claiming a coherent snapshot.
4. **Parse.** Emit source-identified records and an explicit disposition for every inventoried node. Preserve tables, nesting, notation, cross-references, history and ordered image placeholders. Do not flatten legal tables or join text by whitespace when relationships carry meaning.
5. **Validate.** Reconcile source nodes, test representative difficult structures, review anomalies and demonstrate an interrupted/resumed run produces the same result as a clean replay from the same cached source.
6. **Package.** Produce the artifacts in OUTPUT-CONTRACT.md with evidence for every exclusion, correction and unresolved item. A package with unresolved substantive omissions remains incomplete.

A publisher download or export may replace page acquisition when it is officially offered and demonstrably covers the same complete publication/version. Inventory and quality checks still apply. Prefer structured XML/HTML over PDF where they preserve more structure. PDF is the primary route only where the official publication is document-based or a verified export is the best available complete source.

Use one sequential collector per publisher/session initially, bounded retries with backoff, explicit handling of 429/503, and resumable queues. Reuse the supported browser route where required; record ordinary operator challenge handling rather than trying to bypass it. Fix local certificate trust instead of carrying an old `--insecure` workaround into production.

## eCode360 strategy

**Jurisdictions:** 12, listed above. **Reuse:** `adapters/ecode360.py`, `BrowserVendorCollector`, the existing browser transport integration.

Resolve the official publication root, including numeric roots and organization aliases such as HA4470, SU5020 and TU6948. Enumerate its named code/charter families first. Expand and retain the complete code TOC, then acquire chapter bundles where they contain all descendant sections. Separate uncodified “Laws,” accounts, search results and help/navigation pages from codified content.

The current parser recognizes `.contentTitle.sectionTitle[data-code-content-type='section']` and the associated `.section_content` body. Use the actual publisher node/container identity and DOM association, not a broad search for the next arbitrary heading. A section URL may display the whole chapter, so fetching every section URL and emitting the whole chapter each time is wasteful and creates duplicates.

**Required changes:** the current collector deduplicates by printed citation and prunes queued links by section number. Different families or source nodes can legitimately repeat either value. Deduplicate by jurisdiction + publication + stable source node, retaining separately printed duplicate designations with their actual hierarchy. Scope numeric eCode links through the retained publication TOC, not merely the `ecode360.com` host. Preserve canonical per-section identifiers/anchors even when acquisition happened at chapter level. Current plain-text extraction must be extended to preserve table/list/image structure and substantive parent bodies.

**Pilot:** Half Moon Bay for a chapter with several sections; then add a real repeated-label or multi-publication example from the discovered inventories, and a table/appendix example. The synthetic repeated-label probe is already bundled. Confirm a chapter fetched through two child URLs does not duplicate records, while two different source nodes with the same printed number both survive.

**Fallback:** an official publisher export at the same revision, reconciled to the TOC. An inaccessible research-fetch URL alone is not evidence that the ordinary browser or export route is unavailable.

## Legacy Code Publishing strategy

**Jurisdictions:** Foster City, Fremont, San Carlos, Flagstaff, Burien, Renton, SeaTac. **Reuse:** `codepublishing.py` and `codepublishing_legacy.py` with shared acquisition and serialization.

Keep three navigation profiles inside one implementation family:

- California ordinary HTML: Foster City, Fremont, San Carlos, with `/html/<title>/<chapter>.html` documents.
- Hash routes: Burien, Renton and SeaTac, where the fragment selects the visible document.
- Frameset: Flagstaff, where the TOC and body may reside in different frame documents.

Resolve the real title/chapter document from the official navigation; use direct HTML acquisition only when that exact route is supported and returns the intended document. Otherwise retain the browser-rendered body or frame content. Generic outer-document HTML does not contain a frame's document body. Preserve meaningful SPA hash routes in cache keys; ordinary within-document section anchors can share one fetched chapter artifact.

Enumerate every title and chapter before parsing section boundaries. Support Renton's Roman title labels and hyphenated sections and Flagstaff's four-part identifiers. Ordinary numeric patterns must not silently drop appendices, charter articles, parent introductory text or unnumbered operative material. Use source headings and stable anchors to distinguish identity from display citation.

**Required changes:** restrict discovery to the jurisdiction/publication path, detect provider migrations, explicitly traverse frames, and preserve DOM structure instead of concatenating sibling text. Current generic host-only restrictions are insufficient on a shared vendor domain. Inventory Flagstaff's Charter, City Code and Employee Handbook separately; determine applicability from recorded scope rather than silently accepting only City Code titles.

**Pilot:** Foster City for ordinary HTML, Renton for hash navigation/numbering, and Flagstaff for frames and publication families. Passing one profile does not qualify the other two.

**Fallback:** verified official export, or the resolved underlying HTML already linked by the publisher. Do not manufacture hidden document URLs from numbering guesses.

## Municipal.codes strategy

**Jurisdictions:** Berkeley, Petaluma, Sonoma, Bellingham, Everett. **Reuse:** `municipal_codes.py` section-card parser and browser acquisition, after route fixes.

A `/contents` page is a discovery URL, not the permitted descendant prefix. Store publication base independently: for example `/BMC` for Bellingham and `/EMC` for Everett. The current collector's prefix check incorrectly rejects `/BMC/1.01.010` when its root is `/BMC/contents`; both affected examples are reproduced by the probes.

Capture the full hierarchy, expand lazy contents where necessary, and acquire chapter views. Parse actual `article.type-Section` cards with their `data-short-cite`, header number/name and stable source identity. One apparent section URL can render an entire chapter. Preserve card-specific source identity and deduplicate by source node rather than fetched page URL.

**Required changes:** eliminate the fallback that accepts arbitrary `main` text merely because a heading exists. It currently emits a pure Contents page as a provision. Berkeley, Everett and Sonoma historical samples each contain a single Contents record; current code now has a card parser, but those samples must be requalified after repair. Capture substantive non-section containers through an explicit parser path, not the unsafe fallback. Preserve tables and nested markup.

**Pilot:** Berkeley and Everett to reproduce and resolve the old failures; Petaluma or Bellingham as a multi-section comparison. Acceptance requires that known numbered cards appear individually, chapter navigation emits no provision, and valid chapter/section URLs remain within the approved publication boundary.

**Fallback:** a publisher-supplied structured export or complete print rendition matched to the same inventory. Do not substitute search snippets or assume a different city's platform behavior proves completeness.

## CivicPlus PDF collection strategy

**Jurisdictions:** Portland ME and Rockland ME. **Reuse:** document discovery in `civicplus_assets.py` and byte caching in `special_collectors.py`. Replace the generic PDF splitting stage.

For Portland, identify the actual City Code widget semantically and capture document IDs, labels and order. The current implementation chooses the first `manualContentItemIds` array containing at least ten items; that is a fragile heuristic. The historical inventory contained 44 assets, but 44 is an observation to reconcile, not a permanent count to hard-code.

For Rockland, follow the official index's chapter and Charter links. The index currently lists 20 chapters plus Charter. Download each distinct official document, preserve response/file identity, count pages and retain text blocks with page coordinates. Give the Charter its own publication identity; the existing helper labels all outputs as one Code of Ordinances family.

Use native PDF text first. Detect image-only, mixed or broken-text pages; use OCR only where needed and keep OCR evidence/confidence and unresolved transcription review. Segment against printed legal headings plus the document's own contents. Remove running headers/footers using repeated page position and pattern, then reassemble paragraphs that continue over pages. Do not drop all repeated section numbers: a running header may repeat one, but a legal section heading may also be repeated legitimately.

**Required changes:** Portland's current sample includes page headers such as “Rev. 6-20-12” as section names and page continuation fragments as repeated sections. Replace regex-only whole-document splitting with layout-aware assembly. Rockland headings contain trailing markers requiring footnote/layout review. Support Charter-specific numbering, adopting ordinances, appendices, tables and substantive introductions. Record every page/node disposition so extraction omissions are visible.

**Pilot:** Portland Chapter 13 across several page boundaries, Rockland Chapter 1, and the Rockland Charter. Include a table-heavy and an image/mixed-text page from the actual acquired set. Validate these against page renderings, not just another text extractor.

**Fallback:** another official PDF/Word rendition verified against the same edition, or a separately qualified official HTML publication. A changed file name or download date alone does not prove a different legal edition.

## San Mateo Open Law XML strategy

**Reuse:** `openlaw_bulk_xml.py` and `collect_san_mateo_bulk` in `special_collectors.py`. The publisher expressly directs bulk HTML/XML downloads instead of page scraping.

Resolve the current official repository revision, pin its commit and save the complete archive with its hash. Parameterize the commit: the existing code hard-codes the August pilot commit. Store the selected commit separately from publication currency; commit time is not the code's legal current-through date.

Inventory code, Charter and any other relevant publication roots actually present in the repository. The existing collector only traverses `us/ca/cities/san-mateo/code`; do not claim broader publication coverage from it. Parse namespace-aware XML hierarchies, retaining source attributes/IDs and the actual title/chapter/article path. Represent each section and substantive container body without duplicating descendants. Account for referenced/includes files if present.

**Required changes:** current `_clean()` concatenates `itertext()` and collapses whitespace, which can erase list/table relationships or join inline boundaries. The traversal returns immediately at a `section` and only selects its direct `text` child. Verify actual XML variants and explicitly handle nested sections, introductions, status nodes, tables, footnotes and images rather than assuming that schema shape is exhaustive. Attach each record to an immutable repository file plus an XML node locator; a raw file URL alone cannot identify multiple sections in one title file.

**Pilot:** Title 1 for the existing ordinary case; a table/list-rich title and any additional publication/unnumbered body found in the inventory. Compare XML output to the official bulk HTML rendition at the same commit where practical.

**Fallback:** the official bulk HTML repository, also pinned, if XML semantics cannot be resolved for a particular element. Keep source bindings and record the substitution explicitly.

## Cupertino Gridics strategy

**Reuse:** `gridics_codehub.py` and the rendered CodeHUB transport method. The retained pilot emitted 56 rows, proving bounded acquisition rather than full coverage.

Start from the official CodeHUB root and inventory the complete UUID-backed title/chapter/section tree. Preserve the full hash route in URL/cache identity. Wait for the requested route's actual legal content, not merely document-ready or any title heading; a previously rendered title can be stale during navigation. Where the interface uses non-anchor controls or virtualized navigation, implement explicit browser traversal of those controls rather than assuming `<a href>` discovery is complete.

Retain each section's source UUID, path, heading and rendered container. A structured endpoint may be used only after observing that it is an ordinary supported data route for this publication and validating its coverage/version; no such reusable API is established by the current evidence.

**Required changes:** the current parser visits `p, li, td, th, blockquote` descendants and concatenates their text. A paragraph inside a list item is emitted twice; the bundled probe reproduces this. Replace this with one semantic DOM traversal that retains nesting, tables, spans, notes and image order. Section identity must use observed UUID/node context, not only a printed heading or the fetched chapter URL.

**Pilot:** a multi-chapter title, nested lists, a table and a route whose content loads asynchronously. Assert the requested UUID matches the retained page and that each source block is serialized once.

**Fallback:** an official complete print/export route if present and reconciled. Otherwise require explicit completion of browser enumeration before expanding to a full run.

## Daly City eLaws strategy

**Reuse:** the eLaws branch of `browser_vendor_collectors.py` and source-specific routines in `ca_bespoke_adapters.py`.

First reconfirm that the city's official link still identifies this publication and capture its revision evidence. The pilot establishes reachable text; it is not sufficient evidence of today's publication currency. Traverse root → title → chapter → section using observed links under `/code/coor`. Ordinary HTTP worked in the pilot. Retain raw HTML and parse the legal content container independently from navigation.

**Required changes:** the pilot body contains the adoption provision but has blank `section_number` and `section_name`. Bind identity to the publisher's section heading, corroborated by TOC/breadcrumb/source URL. If the source omits a heading, preserve that exception and its evidence; do not infer a valid citation solely from a guessed URL. Restrict traversal to the actual publication path and reject access/error shells. Preserve history, lists, tables and appendices.

**Pilot:** the known adoption section plus a substantive long section, a table and an appendix if supplied. An exported record must have a source-backed identity even when its printed numbering is absent.

**Fallback:** a current city-linked replacement publisher or official complete export, separately qualified before changing the route.

## King County HTML strategy

**Reuse:** title discovery in `kingcounty_code.py` and acquisition/cache helpers in `special_collectors.py`.

The official Clerk landing page supplies title HTML and PDF/Word alternatives, per-document updated markers, and a separate Charter. Inventory these publication/document types explicitly. Title-only discovery must not silently exclude the Charter; Board of Health and other linked compilations require their own scope disposition rather than automatic inclusion or omission.

Download each title once. Detect encoding using response metadata, HTML declarations and raw-byte inspection; retain the chosen decoding rule. The current helper already has UTF-8/Windows-1252 fallback, so replay the problematic retained samples against raw bytes before concluding that the fallback itself is still defective. Keep different title revision dates rather than assigning a single fabricated countywide date.

**Required changes:** the parser currently saves only the paragraph containing a bold section heading. It omits operative following paragraphs and tables; the offline probe confirms this failure. Parse a section's full DOM range through the next real legal section boundary, excluding the preceding contents listing. Support alphanumeric title/section variants discovered in the source; the present numeric-only section regex needs qualification against those variants. Use a separate Charter parser if its structure differs. Preserve real anchors; where none exist, store a document URL plus source locator instead of inventing a browser fragment.

**Pilot:** Title 1 with multi-paragraph sections, one long title containing tables, and the Charter if in scope. Compare difficult HTML ranges against the official PDF/Word counterparts. This is both a coverage and character-decoding check.

**Fallback:** official Word or PDF for a specific failed HTML document, with source version parity and a documented recovery mapping. Do not replace the whole source indiscriminately when a small number of document structures need repair.

## Implementation sequence

1. Establish the common inventory, source identity, semantic serialization and output contract. Repair the six reproduced failures and the historical sample defects.
2. Qualify eCode360 first for broad reuse, alongside the bounded San Mateo XML workflow. These exercise both browser and bulk acquisition designs.
3. Qualify all three legacy Code Publishing navigation profiles, then Municipal.codes with its route/card fixes. These three browser families cover 24 of the 30 jurisdictions.
4. Complete the source-specific Gridics, King County and Daly City qualification paths. Keep CivicPlus PDF work as a distinct layout/QA task; its section assembly is materially different.
5. Expand only a qualified adapter/profile to its mapped jurisdictions. Each jurisdiction still needs fresh source confirmation, its own publication inventory, a representative sample and complete reconciliation.

These are dependency and reuse priorities, not duration estimates. Source size, live availability and the amount of PDF repair have not been measured for a full run.

## Running the included tools

The planner and sample auditor use only the Python standard library and never contact a source:

```sh
python3 handoff_tools.py verify
python3 handoff_tools.py plan --source-type ecode360
python3 handoff_tools.py audit-samples
python3 -m unittest discover -s . -p test_handoff_tools.py
```

The adapter probes require Beautiful Soup and Requests. Use an isolated environment with a supported Python release and install `beautifulsoup4` and `requests`. Then:

```sh
python3 regression_probes.py
python3 regression_probes.py --code-root /path/to/municipal-code-batch --require-pass
```

Default probe mode reports observed failures and exits successfully if the probes execute. `--require-pass` exits nonzero until every criterion is met. These six checks are targeted regressions, not a comprehensive acceptance suite.

The original manager, adapters and selected tests are included as reference code. The browser transport dynamically imports `legal-code-batch/legal_code_scraper.py` from the complete project checkout. Do not treat the reference snapshot as a portable turnkey crawler or run the manager's `--all` mode for this assignment. Its historical readiness report measures pilot completion, not the full-source acceptance criteria in this handoff.
