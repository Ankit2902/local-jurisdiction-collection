# Source-driven extraction plan for the technical team

The scripts in this bundle have been executed on live, bounded sources. Start with the qualified acquisition path for each source family, then expand scope through independently reconciled inventories. A successful sample is the starting point for collection engineering, not an assertion that all source nodes have been acquired.

## 1. Establish the runtime and publication scope

Use [SOURCE-MATRIX.json](SOURCE-MATRIX.json) as a planning input. It is not a production enablement registry. Reconfirm each official jurisdiction link and publisher identity at execution time; review the package report where official-city route confirmation remains limited. Preserve the tested migration evidence for Foster City, SeaTac and Daly City.

For eCode360, Code Publishing and Municipal.codes, the demonstrated transport is a module running in supported Codex CUA. Keep a CUA-backed worker if that runtime is available. Otherwise obtain an authorized export or qualify a standalone path before scheduling collection. Delivered standalone scripts retain access challenges honestly and do not retry around them. Plain HTTP failure does not prove every browser path unavailable, and CUA success does not prove standalone browser success.

Portland needs verified browser index discovery plus ordinary HTTP PDF acquisition. Rockland, San Mateo and Daly City have HTTP/archive/API paths. Cupertino has a tested standalone Playwright path. King County uses a fresh CUA landing capture to discover exact official URLs, followed by original-byte HTTP acquisition. Repeat that discovery step before relying on the listed document routes in a later run.

Inventory each publication separately. Explicitly decide the scope of charters, zoning codes, smart codes, district codes, employee handbooks, supplements, appendix families, uncodified ordinances and incorporated PDFs. Additional observed Municipal.codes families are recorded per jurisdiction in the matrix/report; the Bellingham Charter inventory challenge is unresolved. An unrelated jurisdiction's existing exclusions do not establish scope here.

## 2. Expand one collector per source type

| Source | Runnable foundation | Next implementation increment |
|---|---|---|
| eCode360 | `acquire_cua.mjs`, `ingest_cua.py`, `ecode360.py`; optional `acquire_browser.py` | Enumerate publication-wide source nodes, then acquire unique chapter views. Keep customer/code/node/version checks and exact raw legal-subtree hashes. Retain the explicitly assembled metadata wrapper separately from source bytes. Extend real structural QA beyond current prose/list samples. |
| Code Publishing | `acquire_cua.mjs`, `cp_collect.py`; optional `acquire_playwright.py` | Walk observed root/title/frame links for each publication. Preserve Roman titles, multipart citations, chapter-history bodies and unnumbered tables. Continue source-ID-based deduplication and hidden-UI exclusion. |
| Municipal.codes | `acquire_cua.mjs`, `municipal_codes_cli.py`, `prepare_e2e.py`; optional `browser_capture.mjs` | Acquire unresolved nodes from the primary Contents inventory, classify parent text and appendix structures, then reconcile additional publication families. Reuse stable section-card identity, table/span and image-marker tests. |
| CivicPlus PDF | `run_live.py`, `civicplus.py`, `capture_browser.py`, `capture_cua.mjs` | Acquire all explicitly in-scope inventory assets. Profile additional layouts; render and review uncertain pages. Source-bound recoveries apply only to the exact reviewed bytes and must be rejected when documents change. |
| Gridics | `acquire.py`, `cua_capture.mjs`, `gridics.py` | Verify candidate routes against observed rendered identities before acquisition. Preserve compound navigation namespaces as opaque IDs; do not fabricate URLs. Acquire unresolved bodies in resumable batches, with version checks and table/image review. |
| San Mateo XML | `e2e.py san-mateo`, `san_mateo.py`, `archive_includes.py` | Extend declared include scope after inventory review. Add an explicit own-body profile before accepting mixed parent text/includes; keep path/cycle/membership checks and immutable commit pinning. |
| Daly City API | `e2e.py daly-city`, `daly_city.py` | Acquire every in-scope independent TOC node; retain request/publication identity and start/end tree checks. Add rendered comparison for more table/appendix samples. Track uncodified ordinances separately. |
| King County HTML | `e2e.py king-county`, `king_county.py`, `e2e_cua_bridge.mjs` | Extend the original-byte title acquisition and explicit range parser to the approved scope. Reconcile Title 21A and compare broader Word/HTML paragraphs. Preserve publisher numbering and date conflicts until resolved. |

Entry points above are relative to the relevant package. See each package README for complete installation and invocation syntax. Output contracts include structured full text and TOC, original source artifacts, source-node identities, dispositions, provenance, exceptions and verification results. Large table cells require an increased CSV reader field limit; use the demonstrated verifier settings rather than truncating content.

## 3. Run a staged full acquisition

1. Capture the official discovery evidence, full publication inventory, source identifiers and displayed version/current-through markers. Mark absent currency as unknown. A retrieval timestamp or Git commit does not establish legal currency.
2. Start a new immutable run. Acquire in bounded batches and retain raw bytes/DOM, requested/final URLs, response metadata where available, timestamps and SHA-256. Validate exact requested identity and reject challenges, truncation, DOM mutation or stale adjacent pages.
3. Resume only from a checkpoint bound to the same source inventory, parser and acquisition configuration. Preserve attempts and failures. A stopped run must not be labelled complete merely because a progress-limit exit succeeded.
4. Parse from retained sources. Deduplicate by jurisdiction/publication/source-node identity, not printed citation. Preserve legal hierarchy, subsection labels, source order, parent bodies, tables/spans, superscript/subscript, images/alt references, notes and appendices.
5. Give every independent inventory node an explicit disposition: included, structural, reserved/repealed, scope-excluded with reason, or unresolved. An unresolved node prevents a complete-corpus claim. Reconcile expected attachments separately; an image marker does not mean the image bytes or meaning have been captured.
6. Re-fetch version/inventory markers at the end. Compare source identity, hierarchy and edition markers. Resolve drift; equal markers are evidence of sample/run consistency, not an atomic publisher snapshot guarantee.

## 4. Accept a jurisdiction only after completeness and semantic review

The technical team's final deliverable is a reproducible corpus package whose independent scope inventory is fully accounted for, whose raw inputs are immutable and whose content can be regenerated offline. Compare clean versus resumed outputs, JSON versus CSV, and source-versus-export structure. Review real difficult content visually where semantic meaning depends on layout.

Keep the PDF semantic exception queues open until resolved. Source-hash checks prove identity and transport integrity, not text completeness. Preserve unreadable text explicitly; do not infer missing legal content. Resolve King County's conflicting printed identifiers/date markers with source evidence. Complete legal-version and broader family qualification for Cupertino and the other dynamic publishers.

This handoff is ready for the technical team to reproduce the demonstrated paths and extend them. It does not authorize a production completeness label from the bounded samples, and it does not perform database ingestion.
