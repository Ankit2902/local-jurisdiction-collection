# Current eCode360 standalone headed qualification — 2026-10-16

The ordinary standalone headed browser path passed for all **14 jurisdictions**, retaining fresh legal DOM and producing verified CSV/JSON for **134 records** across bounded chapter/section samples. The phase made **23 accepted fresh legal captures** (including nine separate publisher-export method checks). **13 actual publisher PDF files** were downloaded by selecting one observed legal section and using the publisher's displayed Download → PDF controls. Santa Clara's current page has no Download control; its standalone DOM/parser/export path passes.

**[HEADED-VALIDATION.json](HEADED-VALIDATION.json) is the authoritative current matrix.** `BASELINE-OCT15-*`, `BASELINE-E2E-*`, `HISTORICAL-*`, `live/`, `standalone-live/`, `examples/`, and earlier reports/evidence are copied historical material. Their checkpoints and validation claims are not new results for the current parser. Fresh evidence is under `headed-live/`, current primary output is under `headed-exports/`, and the later nine source replays are under `publisher-method-exports/`. Existing outputs were preserved rather than silently rebound to changed code.

This is bounded method qualification. No publication-wide inventory, complete collection, production import, or release was performed. Every current inventory remains `inventory_complete:false`; release fails closed.

| Jurisdiction | Unique sample records | Standalone DOM → CSV/JSON | Publisher download | Observed code date |
|---|---:|---|---|---|
| Burlingame | 1 | PASS | Acquired PDF | 2026-04-20 |
| Emeryville | 7 | PASS | Acquired PDF | 2026-06-02 |
| Half Moon Bay | 10 | PASS | Acquired PDF | 2026-05-05 |
| Malibu | 28 | PASS | Acquired PDF | 2026-06-22 |
| San Leandro | 1 | PASS | Acquired PDF | 2026-07-20 |
| Santa Clara | 4 | PASS | No Download control | 2026-01-27 |
| Santa Monica | 9 | PASS | Acquired PDF | 2026-07-28 |
| Santa Rosa | 13 | PASS | Acquired PDF | 2026-09-15 |
| South San Francisco | 8 | PASS | Acquired PDF | 2026-09-09 |
| Sunnyvale | 8 | PASS | Acquired PDF | 2026-08-11 |
| West Hollywood | 10 | PASS | Acquired PDF | 2026-06-29 |
| Tukwila | 16 | PASS | Acquired PDF | 2026-05-18 |
| Foster City | 7 | PASS | Acquired PDF | 2026-01-26 |
| SeaTac | 12 | PASS | Acquired PDF | 2026-09-30 |

## Run without Codex

Use Python 3.9 or newer, a normal installed Google Chrome, and the dependencies in `requirements-browser.txt`. The live qualification used Python 3.9.6, Playwright 1.60.0, and installed Chrome **155.0.8059.84** in headed mode on macOS. The supported path launches a fresh isolated browser context for each job and needs a graphical session. It uses ordinary Playwright APIs and filesystem output; it does not depend on CUA or Codex at runtime. Other operating systems and future browser releases have not been live qualified here.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-browser.txt
```

Create a separate reviewed authorization JSON for the intended new run. It must contain `explicit_user_authorized_resumption:true`; record the approver, UTC time, bounded scope, and publisher condition review alongside it. The delivered `headed-live/RESUMPTION.json` and `FOLLOWUP-AUTHORIZATION.json` document this phase's actual authorization and must remain immutable evidence. A new authorization does not automatically clear a rate-limit stop.

For one reviewed route, with a new empty output directory:

```sh
.venv/bin/python run_serial.py --authorization my-authorized-run.json --out fresh-acquisition --slugs foster-city-ca --delay 12
.venv/bin/python ingest_standalone.py --receipt fresh-acquisition/foster-city-ca/receipt.json --jurisdiction 'Foster City' --out fresh-exports/foster-city-ca
```

`run_serial.py` defaults to the 14 routes in `route-registry.json`; use `--slugs` to select a bounded subset, or `--exclude-slugs` to exclude reviewed slugs. Unknown slugs, an empty selection, reused nonempty output, absent authorization, and an active host stop fail before launch. The runner returns nonzero on source failure, rate stop, or a failed/incomplete batch. A missing publisher Download control is recorded separately from successful legal-source acquisition.

The runner obtains exact `#codeContent` outerHTML, verifies the requested chapter/section node plus customer/code/date, and requires two identical source reads with the same URL and edition. `ingest_standalone.py` verifies raw SHA256 and receipt hashes, registry jurisdiction/publication binding, same-edition start/end state, a nonempty on-page TOC, and lexical text preservation before exporting. The wrapper around a retained legal subtree is explicitly disclosed; it is not a fabricated publisher document. CSV and JSON include the 16 documented fields; provenance, TOC, semantic HTML, dispositions and checksums are retained beside them.

If a new publisher edition changes `code_id`, the job fails closed. Review the actually observed new edition and jurisdiction before deliberately updating `route-registry.json`; do not silently reuse an old checkpoint. Replay checks **all** artifact hashes, including already processed checkpoint entries. A changed source or parser binding requires a new run directory.

The historical `standalone.py` and `acquire_browser.py` direct CLI entries are disabled. The imported `standalone.state()` helper remains usable by the current probe. `ecode360.py` provides offline replay and public HTTP method tooling, with zero default retries and immediate publisher429 host stop; fresh direct-HTTP success is not claimed by this phase.

## Publisher files and ordinary manual workflow

The current automated ordinary UI path rejects nonessential cookies through the displayed consent button, selects one observed `guid_<id>_content_checkbox`, opens **Download selected content**, and clicks the displayed enabled **PDF** button. Download and popup listeners are installed before the click. Exact dialog HTML, screenshots, selected IDs/citation, actual download URL, raw file bytes/SHA256, and edition before/after are retained. There is no constructed download endpoint.

A person can follow those same ordinary controls in a normal browser. This manual workflow is documented from the observed UI; a new operator/CUA acquisition is not claimed in this phase. The actual successful file captures were unattended standalone browser jobs. Login, payment, and security controls were not used. **Print/Save as PDF is a separate method and was not substituted for a publisher download.**

Body permission flags alone were misleading: several pages advertised `pdf-login-required=true`, yet the actual displayed PDF action downloaded anonymously. Word was disabled with a Word-specific login warning. Current Santa Clara has no Download action and all retained PDF/Word/export permission flags are false. Its legal DOM provides the qualified source method.

The separate `../publisher-downloads/DOWNLOAD-VALIDATION.json` and companion README contain independent PDF intake, selected-section comparisons, PDF-native exports and visual checks. All13 files passed intake, title and complete operative text comparison and produced13 PDF-native selected-section JSON/CSV records. Twelve passed bounded text semantics; San Leandro includes an incorporated map retained in the PDF/page image, whose map/OCR/GIS semantics remain unqualified. All13 files are one page with no detected tables. Keep those outcomes distinct from the 134 DOM-derived records. A PDF footer download date is not an immutable edition ID; its edition claim is bound to the same live source session's customer/code/date before and after export. Whole-publication PDF coverage is not inferred.

## Rate controls and currentness

The prior Oct15 429 ledger is preserved at `standalone-live/ecode360-host-throttle.json`; Retry-After was unknown. Explicit user-authorized resumption was recorded separately. One fresh headed Foster City sentinel returned200; it was followed by serial conservative bounded jobs. Every fresh job returned initial and final document200, and no fresh429 was observed. Elapsed time and a successful sentinel do not establish perpetual clearance.

Any response429 from ecode360.com **or a subdomain**, including later XHR/download traffic, immediately writes `headed-live/CURRENT-HOST-STOP.json` and aborts further publisher requests. Later jobs refuse launch. There is no automatic retry or automatic stop-ledger removal. Preserve a stop and its headers/Retry-After, then obtain explicit condition review before a separate authorized resumption. The scripts never solve challenges, click security controls, import cookies/profile/storage state, override user-agent, weaken TLS, or use accounts/payments.

Fresh publisher customer/code/date, requested node, source body and edition stability were verified per city. Official city-portal link designation was inherited from separately retained route evidence and was **not freshly crawled** in this phase. Headless and direct-HTTP historical failures are not permanent-denial claims, and neither runtime was newly qualified by the headed result.

## Verify the delivered pilot offline

```sh
.venv/bin/python -m unittest -v
.venv/bin/python verify_headed.py
node --test test_capture.mjs
```

The final Python suite passes **38 tests**. Node reports **11 acquisition regression checks** (one test-file wrapper). `verify_headed.py` validates the 14 current receipt/raw bindings, archived executed source revisions, edition stability, every output hash, CSV/JSON equality, 134 unique-city records and 13 downloaded file hashes without network access. Logs are in `headed-live/TESTS-PYTHON.txt`, `TESTS-NODE.txt` and `VERIFY-HEADED.txt`.

Independent sibling review packages provide additional evidence: `../independent-review/REVIEW.json` checks all14 fresh sources/134 bodies, eight tables, 309 cross-references, five negative controls,16 receipt/text controls and27 core/E2E tests; `../runtime-review/RUNTIME-REVIEW.json` binds the live-tested r4 probe and15 mocked runtime/429/UI guards. The publisher review remains a separate file-format method.

`SOURCE-FREEZE.json` lists final code hashes. `headed-live/executed-r1` through `executed-r4` preserve the exact live acquisition revisions and dependencies. The final launcher has only offline-tested safety/argument/exit changes after r4; historical direct entry points were then disabled. No claim is made that every capture used the final launcher revision. `BUNDLE-MANIFEST.json` binds current files; it excludes transient caches, browser profiles, storage state, cookies and installed runtimes.
