# CivicPlus PDF collection and bounded validation

This directory is a self-contained Python CLI and an honest qualification package for **Portland, Maine** and **Rockland, Maine**. It does not contain a complete jurisdiction corpus. No database import or ordinance-update collection was performed. Source snapshots, sample outputs, source/page ledgers and validation evidence are separate.

The retained live inventory has 44 Portland PDF assets (including Charter, reference tables/indexes and TOC) and 21 Rockland documents (20 code chapters plus Charter). These are observations from October 15, 2026, not constants in the parser. Only Portland Chapter 13, Rockland Chapter 1 and Rockland Charter were acquired. The same Portland PDF contains actual table examples on pages 36–43 and a mixed text/image example on page 48.

## Install and execute

Use Python 3.10+ in a virtual environment. No repository imports, machine-specific paths or credentials are required by the CLI.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python civicplus.py --help
.venv/bin/python -m unittest -v test_civicplus
.venv/bin/python civicplus.py verify --package samples/portland-me
.venv/bin/python civicplus.py verify --package samples/rockland-me
```

The validation environment used Python 3.12, pdfplumber 0.11.9, requests 2.34.2, BeautifulSoup 4.15.0 and json5 0.17.3. Tests use the retained official PDFs and HTML plus small generated/mocked cases; no network is required. Full replay tests take roughly a minute. Poppler `pdftoppm` is required only for rendering; parsing does not require a browser, OCR service or Poppler.

A zero `verify` exit means package hashes, record identity, source-node accounting and CSV/JSON integrity pass. It does **not** mean corpus completion. Every package/report explicitly carries `corpus_complete: false`. CLI errors return 2; integrity failures return 1.

## Discover the official collection

Discovery consumes fresh HTTP HTML or operator-retained browser DOM. For Portland, HTTP supplies the exact City Code Documents widget data; the rendered widget supplies labels and displayed ordering. The parser identifies the widget by its semantic header and widget ID and checks every member is a PDF asset. It retains both manual selection order and actual column display order, and requires them to reconcile. It does not choose the first large ID array. Unlabelled assets remain unresolved and cannot be acquired until the rendered widget supplies their labels.

For a live Portland run, retain the visible City Code Documents widget's `outerHTML` from the ordinary official page, then:

```sh
python civicplus.py discover --jurisdiction portland-me --out runs/portland-new \
  --rendered-html /path/to/portland-widget.html
```

A fully offline reproduction of the validated inventory is:

```sh
python civicplus.py discover --jurisdiction portland-me --out runs/portland-replay \
  --index-html evidence/portland-index.html \
  --rendered-html evidence/portland-widget-browser.html \
  --retrieved-at 2026-10-15T16:30:00Z
python civicplus.py discover --jurisdiction rockland-me --out runs/rockland-replay \
  --index-html evidence/rockland-index-browser-main.html \
  --transport browser_rendered_dom --retrieved-at 2026-10-15T16:31:07Z
```

Rockland is scoped to the official page's `#page` content container, not arbitrary sitewide chapter links or hidden `data-documentids`. It follows the actual displayed chapter and Charter links. Charter has its own publication identity. Source host differences are recorded; this package does not infer a migration. Both www and apex direct requests returned empty 404 responses here; the apex official page and observed sample links worked in the ordinary Codex in-app browser. The HTTP collector records and stops on that failure. A browser operator must retain the index and download the observed official files, then use the tested import command below. A separate automatic browser transport is **not qualified** by this package.

Use a new output directory when the retained inventory changes; discovery refuses to overwrite a different existing snapshot. The original full-document browser serialization hit the tool's 200 KB return limit; those `*-index-browser.html` files are diagnostics only. The final source containers (`portland-widget-browser.html`, `rockland-index-browser-main.html`) are complete, small captures and are the accepted evidence.

## Acquire a bounded sample or import an official browser download

The CLI requires explicit IDs or `--all`; it never silently downloads all documents. Downloads are sequential, TLS-verified, cached with SHA-256 and receipts, and resumed only from a matching raw hash. It retries 429/503 and transient request errors at most three times with bounded backoff. Permanent HTTP errors retain evidence and fail closed. `--all` is intended for a later, separately authorized full run; it was not used here.

```sh
python civicplus.py acquire --package runs/portland-new \
  --id b4305bca-b7ef-4d12-b84f-5554626b4b81
python civicplus.py import-browser-pdf --package runs/rockland-replay \
  --id document-621 --file '/path/to/Chapter 01 - General Provisions.pdf' \
  --retrieved-at '2026-10-15T16:31:07Z' \
  --note 'Downloaded from observed official Chapter 01 link in ordinary browser.'
python civicplus.py import-browser-pdf --package runs/rockland-replay \
  --id document-620 --file '/path/to/City Charter.pdf' \
  --retrieved-at '2026-10-15T16:31:15Z' \
  --note 'Downloaded from observed official Charter link in ordinary browser.'
python civicplus.py parse --package runs/rockland-replay
python civicplus.py verify --package runs/rockland-replay
```

Browser import is an operator-attested transfer: it binds bytes to an already inventoried document ID, SHA-256, timestamp and note. It does not invent response status, redirect chain, server headers or provenance that the browser did not expose. A user-supplied file must be matched visually to the intended publication before acceptance.

## Parser behavior and package contract

`parse` is entirely offline and checks raw hashes before reading a PDF. It emits the handoff's 16-field UTF-8-BOM CSV and JSON envelopes, compatibility TOCs, aggregate files, publications, run manifest, source nodes, exactly one disposition per node, record provenance, exceptions and a validation report. Source URLs include source-backed PDF page locators. IDs combine jurisdiction, publication, document and actual page/heading occurrence; printed section numbers alone are never deduplication keys.

PDF text is grouped on precise baselines with coordinates and fonts. Position-qualified headers/footers are removed into a ledger; removal never depends on repeated section numbers alone. Portland Ch13 uses actual bold legal-heading typography to avoid wrapped cross-references such as “Sec. 13-9 of this chapter…” becoming provisions. Rockland supports plain Charter numbering and retains its independent printed TOC before the first legal section. Its adopting ordinance introduction is retained. Article headings remain separately retained unnumbered bodies with classification review rather than being silently discarded.

The same logical section contains all its page continuations. Fixed-spacing `<pre>` blocks preserve line indentation and enumeration. Tables are emitted once as HTML tables with cell `rowspan`/`colspan`, fixed-spacing cell text, source rows and full cell geometry. This retains the grouped Weekly/Monthly columns in Portland p37; it does not claim a general semantic table-header inference. Lists and paragraphs retain source layout rather than an inferred fully normalized legal outline. Every record maps to all ordered page/coordinate content blocks.

`layout/<document-id>/pages.json` retains native line coordinates, fonts, removed running matter, image boxes, quality flags and OCR status for every page. `blocks.jsonl` retains ordered content and table cells; `printed-toc.json` is an independently extracted source contents denominator where present. Printed TOC number/count mismatch is unresolved; TOC and body heading text are retained separately for editorial review. The document inventory is independent of output; heading inventory is extracted from the PDF itself and is not represented as proof of complete legal-node coverage.

## Explicit review boundaries

- The two jurisdictions remain incomplete: Portland 43 inventory documents and Rockland 19 inventory documents were not acquired.
- Portland Ch13 page 48 has a tiny image/mask and a visible/native-text mismatch around the property-tax clause. `[IMAGE]` preserves image order but is not a substitute for recovery. OCR/transcription plus source review is required; OCR was not performed or assigned a fabricated confidence.
- Tables on Portland pages 36–43 need semantic and continued-table review. Page 37's grouped columns are preserved with fixed spacing and cell coordinates, but their semantic subcolumn hierarchy and cross-page headers remain a gate.
- Rockland Chapter 1 has microscopic 0.67pt “1” glyphs near headings 1-101/1-103. They remain in content/coordinate evidence and never become part of section names. Their significance requires publisher/source review, not guessed footnote normalization.
- Rockland Charter also contains off-page native locator artifacts, retained in the removal ledger, and has white running-locator boxes that overlap legal body text at several page positions (including visually reviewed page 3). Native baselines recover the underlying text, but the visible source masks it. The package flags the overlap and does not silently call that text visually verified.
- Unnumbered introductory/editorial text is retained and awaits classification. Other Portland documents/Charter layouts, complex multi-column text, mathematical notation, nonstandard appendices and image-only OCR are not qualified by these samples.
- No legal edition/current-through date is inferred from retrieval time, filename or last-modified headers. Official revision labels remain verbatim and publication-level legal currency remains unknown.
- This is a pilot collector, not a full production-release gate. Completing all OUTPUT-CONTRACT criteria requires full inventory acquisition, independent substantive-node reconciliation, resolving exceptions, a coherent source-version review and broader visual checks.

`VALIDATION-REPORT.json` and the jurisdiction copies distinguish automated tests, source visual comparisons, transport status and unresolved conditions. The replay regression interrupts after one Rockland document, resumes with the second, and compares ordered records, source identities, provenance and dispositions to a clean replay from identical bytes.

To reseal the retained validation reports after a successful test run, use `python make_report.py`. This refreshes artifact hashes and includes the existing source visual comparison log; it does not perform a new visual review.
