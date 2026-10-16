# CivicPlus live E2E collection qualification (phase 2)

This new directory preserves the original validation package and adds **fresh source discovery → acquisition → PDF parsing → verified sample exports**, with command, runtime, timestamp and hash receipts. The original directory under `local-extraction-validation-2026-10-15/civicplus` was not changed. Copied `samples/` and the old `VALIDATION-REPORT.json` are baseline evidence, not proof of a fresh E2E run. The phase-2 authority is `E2E-VALIDATION.json`, which points to the final runs below.

## Live entry points

Python 3.10+ is required. Install `requirements.txt` for HTTP/PDF work. For standalone browser capture install `requirements-browser.txt` as well. `capture_browser.py` explicitly defaults to an installed Chrome (`--channel chrome`); on macOS it checks `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`, and on Linux it checks Chrome on PATH. Pass `--executable-path` for another installation or Windows. To use Playwright's bundled Chromium instead, install it with `python -m playwright install chromium` and select `--channel chromium`. Only installed Chrome on macOS was live-qualified here; no cross-platform success is claimed. The capture receipt records the actual executable, channel, browser version and Playwright version. HTTPS checks remain enabled.

```sh
python -m pip install -r requirements-browser.txt
python run_live.py --jurisdiction rockland-me --runtime http \
  --out runs/rockland-fresh --id document-621 --id document-620
python run_live.py --jurisdiction portland-me --runtime playwright --channel chrome \
  --out runs/portland-fresh --id b4305bca-b7ef-4d12-b84f-5554626b4b81 \
  --review-file reviewed-recoveries.json
python -m unittest -v test_civicplus test_e2e
```

Every run requires a new output directory. This deliberately prevents a retained cache from being mistaken for live acquisition. `run_live.py` invokes the delivered collector commands, captures their output/exit codes and hashes, then reacquires the official inventory after parsing and compares document IDs, labels/revision markers, publication families, scope and order. A membership change blocks coherent-run acceptance even when downloads and parsing succeeded. Raw response hashes are retained separately because unrelated page markup may change. Retrieval time and unchanged membership do not prove a legal current-through date.

Portland's plain `requests` index request failed certificate-chain verification in this environment, including a bounded attempt with the host's existing `/etc/ssl/cert.pem`. No trust check was disabled. Isolated Chrome successfully obtained the same official page with verification enabled; the CLI then downloaded the observed CivicPlus PDF URL over verified HTTPS. Rockland's canonical official index and its sample PDFs now return HTTP200 directly. The earlier empty404 observation remains historical and is not reported as a current blocker.

## Supported CUA runtime

`capture_cua.mjs` is an executable module for the supported `cua_repl` browser tool, not an independent browser connection. It uses an already opened, observed official Portland code tab. It retains the visible widget and its page DOM configuration script, hashes both, and records capture times and explicitly marks browser version/executable as unavailable in the supported CUA DOM API. The standalone Chrome receipt supplies exact executable/version for its own runtime. It does not claim HTTP response bytes or headers that CUA does not expose. Its complete config/widget captures avoid the browser tool's 200 KB full-document serialization limit.

Inside the supported CUA runtime, after opening the official page in an isolated agent tab:

```javascript
const capture = await import('file:///absolute/path/to/civicplus/capture_cua.mjs');
await capture.capturePortland(tab, '/absolute/path/to/new-start-capture');
```

Then execute the portable pipeline:

```sh
python run_live.py --jurisdiction portland-me --runtime cua-files \
  --capture /absolute/path/to/new-start-capture --out runs/portland-cua-fresh \
  --id b4305bca-b7ef-4d12-b84f-5554626b4b81 --review-file reviewed-recoveries.json
```

After that run finishes, execute `capturePortland` again in CUA into a new final-capture directory, then:

```sh
python reconcile_cua.py --run runs/portland-cua-fresh --capture /absolute/path/to/new-final-capture
```

The reconciler requires a final receipt timestamp after acquisition/parse completion, verifies capture hashes, and compares the independent source membership. CUA is intentionally controlled by its supported runtime; the Python job does not open or take over the user's browser. Both this CUA path and the isolated standalone Chrome path were exercised in the final phase-2 runs.

## Selected PDF semantic recoveries

`reviewed-recoveries.json` and `review_pdf.py` add three optional, narrow recoveries to one immutable Portland PDF, with fresh source-rendering SHA-256 bindings and exact expected source cells/locators. A changed PDF, changed cell content, missing/ambiguous locator or changed rendering evidence rejects the recovery. Evidence PNGs are copied into the parsed package and review IDs/source fragments are carried in provenance.

- Page37 rent table now has an explicit two-level header hierarchy: Bedrooms, Unheated Weekly/Monthly, Heated Weekly/Monthly. All five data rows were checked visually.
- The food table beginning on page37 and continuing on page38 is assembled once with its four headers and all household1–8 rows. Both source page/coordinate fragments remain attached. Values are transcribed as printed, including amounts that do not follow a simple arithmetic extrapolation.
- Page48's readable line missing from native extraction is restored as `abatement process under 36 M.R.S.A. [UNREADABLE SYMBOL] 841(2) and through`. The original image placeholder remains ordered in the body. The visible source has a square/missing glyph; its intended character is not guessed, so the symbol remains an explicit unresolved gate. No OCR confidence is fabricated.

Fresh source pages37,38,48 and Rockland Charter page3 were rendered and visually inspected. `live-e2e/qa/reviewed-output.html` and `.png` render the resulting reviewed tables/transcription for comparison. The remaining Portland table pages, the unreadable symbol, Rockland Charter's obscured text/floating locators, microscopic Chapter1 markers, unnumbered text classification and whole-jurisdiction completeness remain review gates. **Parse/integrity PASS does not mean semantic completeness.** These recoveries do not qualify a generic PDF layout or another legal edition.

The remaining text below describes the preserved baseline parser contract and historic evidence. Where transport observations differ, the fresh phase-2 reports above take precedence.

---

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
