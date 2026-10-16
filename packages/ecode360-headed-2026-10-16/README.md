# eCode360 standalone headed-browser handoff

**All 14 previously unqualified eCode360 primary-code routes now have successful bounded standalone acquisition → parsing → CSV/JSON pilots.** Ordinary headed Chrome acquired fresh legal sources without Codex, CUA, operator intervention, credentials or imported browser state. Independent review checked **134 sampled provisions, eight legal tables and 309 cross-references**.

The same standalone browser workflow also acquired **13 actual selected-section publisher PDFs without login**. Santa Clara’s tested anonymous publication had no available Download control; its four-record legal-page pipeline still passed. All 13 PDFs passed file intake and yielded PDF-native selected-section JSON/CSV with complete operative text and titles matched against the fresh legal-page sources. Twelve passed the bounded text-layout checks. San Leandro contains an embedded map: its PDF, full-page render and image coordinates are retained, and the record remains explicitly review-required. The DOM export retains the image reference; it does not transcribe the map either. Actual PDF acquisition, file integrity and text/nontext semantics remain separate milestones in the [download review](publisher-downloads/DOWNLOAD-VALIDATION.json).

Start with the [14-city matrix](SOURCE-MATRIX.md), [machine-readable matrix](SOURCE-MATRIX.json) and [primary runbook](ecode360/README.md). The authoritative phase report is [HEADED-VALIDATION.json](ecode360/HEADED-VALIDATION.json). Copied earlier `STANDALONE-VALIDATION.json`, E2E reports and historical files are baseline evidence; their earlier failures do not describe this new run.

## What the technical team can run

The preferred structured-text route is **ordinary headed Playwright → stable legal DOM capture → the standalone importer → verified CSV/JSON**. It uses the current publisher customer/code/date, exact route and section identities, on-page TOC, original captured source and receipt hashes. The delivered scripts reject mismatched publications, empty outputs, changed source artifacts and unsupported editions. Clean and interrupted/resumed exports were compared independently.

The supported entry points are `ecode360/headed_probe.py` for a bounded source and `ecode360/run_serial.py` for selected registry routes. Follow the exact setup and authorization-file commands in [the runbook](ecode360/README.md). Use fresh output directories. The serial runner validates selected slugs before launch, respects host stops and returns failure for incomplete or failed jobs. Historical direct browser entry points are disabled in this new copy so they cannot accidentally bypass the revised controls.

The optional publisher-file route uses the same ordinary browser session: reject non-essential cookies through the visible consent dialog, select one observed section checkbox, open **Download selected content**, and choose **PDF**. The script retains the actual browser download and its selection, source edition, timestamp, URL and SHA-256. It does not generate a substitute PDF with browser printing. A human can also use the documented normal interface, but all fresh acquisitions counted in this phase were automated standalone runs.

The [publisher-download runbook](publisher-downloads/README.md) covers the local file verifier and narrow selected-section PDF parser. Prefer the DOM pipeline for general structured extraction; the PDF parser is qualified only for its tested layouts and rejects or flags unsupported structure. PDF samples overlap provisions in the DOM pilot and are not additional unique provisions.

## What changed after the prior rate limit

The prior 429 receipt did not preserve headers, so its Retry-After value remains unknown. The new user-authorized Foster City sentinel began 8 hours 15 minutes after that receipt, in a fresh ordinary headed Chrome context. It returned legal content with HTTP 200. That observation justified proceeding with one serial worker; elapsed time alone was not treated as clearance.

The phase completed 23 accepted captures across 14 unique jurisdictions, including later small export-method probes, with no new 429 recorded. Primary captures and later selected source captures have matching legal-source hashes. No parallel workers sent publisher traffic. Other agents inspected and tested retained bytes offline.

A page’s permission/login flags did not reliably predict anonymous PDF access. In the observed Download dialog, PDF was enabled while the login warning applied to Word; actual files confirmed PDF access for 13 cities. Santa Clara’s current controls differed. The handoff records observed controls and actual downloads separately, rather than promoting a page flag into a universal access conclusion.

Future 429 responses still stop the host queue immediately, including responses during consent handling or PDF generation. The scripts retain Retry-After when provided and do not solve security challenges, transfer cookies/profiles, change user agents or weaken TLS. Passive browser verification is supported, but this phase’s accepted initial and final document responses were HTTP 200; it does not establish why the earlier attempts failed.

## Validation and portability

[Independent semantic review](independent-review/REVIEW.json) verified all 14 fresh source files and 134 records, including exact word boundaries and order, printed numbers and source anchors, editions, table/list structure, cross-references, CSV/JSON agreement, provenance, and clean/resumed equality. It also passed five targeted safety controls, 16 receipt/text acceptance checks and 27 existing offline tests.

[Runtime review](runtime-review/RUNTIME-REVIEW.json) passed 15 offline guard regressions against the actual live probe revision. Its receipt snapshot includes repeated routes; the phase report supplies the final unique-city counts. The primary package passed 38 Python tests and 11 Node acquisition checks. The PDF helper passed 29 tests and 13 post-freeze CLI replays: 12 returned success and San Leandro deliberately returned review-required. All 13 pages were visually inspected; that inspection does not claim semantic transcription of the map.

The actual successful browser runtime was installed Chrome 155.0.8059.84 in headed mode with Python Playwright 1.60.0 on macOS. Use a modern Python/OpenSSL environment and the declared dependencies. A graphical browser session is required. Headless scheduling, direct HTTP acquisition and Linux/Windows execution were not qualified by these runs.

Exact live-executed revisions are archived and bound to receipts. Final launcher argument/preflight/exit changes and disabled historical CLI entry points were tested offline after live work; the acquisition probe remains the live-tested r4 revision. The final source hashes and reports distinguish these facts.

## Scope and integrity

This is a source-method handoff. It does not change the corpus database, establish complete publication inventories, collect entire jurisdictions or qualify every attachment, appendix, image or PDF layout. Before production collection, the technical team should reproduce a bounded pilot on its own machine, enumerate the full in-scope publication families, then reconcile source-node coverage and editions across a paced, resumable run.

Unpack the complete archive and verify it before writing new outputs inside the delivery:

```sh
python3 verify_bundle.py
```

Run replays and tests in a working copy or new output directories, following the component runbooks. The previous sealed handoff remains unchanged and passed its original 3,862-file integrity check after this work. The new release includes original public-source bytes, actual PDFs, executed scripts, receipts, frozen review inputs, test logs and provenance. Runtime installations, browser profiles and Python caches are excluded.
