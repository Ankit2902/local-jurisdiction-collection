# Legacy Code Publishing runnable validation package

This package contains bounded HTTPS acquisition, import of operator-retained rendered DOM, deterministic offline parsing/export, and source-backed validation evidence for the seven jurisdictions originally assigned to Code Publishing. It changes no production adapters or database records. All runtime inputs and retained fixtures are included; copying this directory to another machine is sufficient for the tests and historical replays.

**Current route correction:** Foster City's municipal-code document explicitly announces migration to [eCode360 FO4449](https://ecode360.com/FO4449). Its current municipal code must use a qualified eCode360 route. The legacy site also lists the **Estero Municipal Improvement District Code**, which needs a separate scope decision. The historical Foster City replay in this package is not a current-code extraction. The observed migration and district HTML excerpts are under `foster-city-ca/live/`.

## Qualification and limits

The source-sensitive implementation has 27 automated tests, including imports and replays of actual retained August 28, 2026 chapter DOM for **all seven** jurisdictions. The historical replays contain 52 records: Flagstaff 5, Foster City 7, Fremont 11, San Carlos 10, Burien 6, Renton 1, SeaTac 12. Fremont includes its chapter-level prior-legislation footnote as a separate unnumbered record, plus 10 numbered sections. The historical chapter TOC anchors reconcile to every numbered section in each replay; every source paragraph with publisher P-level classes (including P0 and P1) is checked for retention. This is a chapter-level denominator, not a publication-wide inventory.

October 15 supported in-app-browser checks established publication roots for all seven, plus Renton root → Roman Title I → Chapter 1 → section 1-1-1 and Flagstaff root → explicit TOC/body frames → Title 1 → Chapter 1-01 → five four-part sections. Flagstaff's three publication families are inventoried separately: Charter, City Code, Employee Handbook. Its Title 1 has 23 linked chapters and the unlinked `1-19 REPEALED.` entry. Those counts demonstrate why links alone cannot account for all source nodes.

The initial direct HTTPS probe received Cloudflare HTTP 403 at every historical root. Supported IAB navigation subsequently worked. No access-evasion or certificate bypass was used. Ordinary Chrome automation failed before site navigation at its request-header policy service. Current root navigation for Fremont and San Carlos uses hash routes, while Foster City and Flagstaff use frames. The old ordinary-HTML/hashes/Flagstaff-only-frames grouping must not be treated as today's verified root configuration.

`live-browser-observations.json` contains selected read-only DOM/AX observations. The few `live/*.html` files are explicitly **selected HTML excerpts**, transcribed from the returned CUA subtree values with a trailing newline. They are not complete current browser DOM captures. The raw `historical/raw/` artifacts are complete retained chapter/title DOM snapshots copied byte-for-byte from the earlier project cache with origin paths and hashes in `import-provenance.json`. Historical currency is unknown; the current publisher currency labels are stored separately and are never assigned to the historical artifacts.

No complete current publication tree or whole corpus was collected. No jurisdiction is marked ready for production. Full scope decisions, complete inventories (including unlinked status nodes and other families), current source acquisition, end/start revision comparison, difficult real tables/images, and human visual QA remain prerequisites for a full run. This package deliberately has no automatic completion/promotion flag.

## Install and run

Use Python 3.9 or later; Python 3.10+ with a supported OpenSSL runtime is recommended for live HTTPS. The validation environment used Python 3.9, requests 2.32.5 and BeautifulSoup 4.15.0; its LibreSSL warning did not affect offline tests. Use normal system certificate trust for live requests.

Run these commands from this package directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s . -p 'test_*.py' -v
.venv/bin/python verify_package.py
```

Windows uses `.venv\Scripts\python.exe` in place of `.venv/bin/python`. No special browser/CDP package, credential, repository import, or absolute filesystem path is required for replay.

Replay one complete retained chapter with the output contract:

```sh
.venv/bin/python cp_collect.py replay --snapshot renton-wa/historical/snapshot.json --out work/renton-replay --checkpoint work/renton-checkpoint.json
```

Replay any of the other six by replacing `renton-wa` with its directory name. `replay/` under each jurisdiction contains the already generated, reviewable contract package: 16-column BOM CSV and JSON, compatibility TOC, separate publication files, raw input, source-node/disposition/provenance sidecars, exceptions, manifest and artifact hashes. `full_text` is a semantic HTML fragment, retaining tables/spans, lists, notes, superscripts, subscripts and links. A plain-text reading aid is in provenance. Image elements become ordered `[IMAGE]` placeholders with alt text where available; the original image markup remains in the retained source. Diagrams still require explicit review.

Demonstrate interruption, then resume:

```sh
.venv/bin/python cp_collect.py replay --snapshot flagstaff-az/historical/snapshot.json --out work/flagstaff-resumed --checkpoint work/flagstaff-checkpoint.json --stop-after 1
.venv/bin/python cp_collect.py replay --snapshot flagstaff-az/historical/snapshot.json --out work/flagstaff-resumed --checkpoint work/flagstaff-checkpoint.json
```

The automated suite also interrupts a two-document fixture between documents and compares clean/resumed exports and sidecars byte-for-byte. Checkpoints bind the entire snapshot/configuration and parser source hash. Any changed raw bytes, snapshot version, selector/configuration or parser source invalidates resume. Ordinary anchors share one acquisition identity; SPA document fragments remain in the key. Duplicate document acquisitions are rejected for explicit alias reconciliation.

## Bounded collection workflow

`discover` follows only **observed** same-jurisdiction links and explicit frame sources, retains raw HTTPS responses and receipts, and is capped at 20 pages per invocation (default 3). It is inventory discovery only. It does not submit forms, guess hidden document paths or interpret hash routes as HTTP response bodies.

```sh
.venv/bin/python cp_collect.py discover --root https://www.codepublishing.com/WA/Renton/ --out work/current-discovery --max-pages 3
```

A 403/429/503 stops the run with retained evidence. Retries are zero by default: inspect the condition and choose a normal supported route before repeating. A provider migration or redirect outside the jurisdiction is a hard error. For hash/frames browser collection, use the supported browser to follow observed links/frames, retain the relevant complete legal container and navigation evidence, and wait for its **specific legal heading**, not only a changed URL. A live Renton transition displayed the old Title I body after its chapter URL had already changed.

An acquisition plan supplies jurisdiction, root, local snapshot identity, separately inventoried publications, and 1–20 explicit documents. Each document must be observed in a retained navigation artifact with its URL/hash/path. A rendered document additionally supplies its observed `rendered_url`, SHA-256, retrieval time and `expected_heading_id`. The expected heading must be present among actual legal h3–h6 headings. Operator receipts remain an explicit trust boundary; this script does not itself drive a browser.

Runnable examples for all seven use the retained historical navigation and DOM without network requests:

```sh
.venv/bin/python cp_collect.py acquire --plan flagstaff-az/historical/acquisition-plan.json --out work/flagstaff-acquired
.venv/bin/python cp_collect.py replay --snapshot work/flagstaff-acquired/snapshot.json --out work/flagstaff-parsed
```

For an ordinary current HTTPS document, clone a plan and remove `rendered_artifact`; the exact planned URL must still occur in the retained navigation evidence. Never convert a hash route to a guessed `/html/` path. `acquire` validates readiness and rejects challenge/migration/empty/navigation pages before producing a snapshot. It cannot certify coherent edition or complete coverage and leaves both false.

## Implementation behavior and acceptance evidence

- Node/record identity uses publication + retained document + observed HTML ID, named anchor, or explicit heading ordinal. Printed duplicate citations survive. HTML ID and named-anchor locator types are distinct.
- Paragraphs belong to the heading range that contains them, including ranges crossing wrappers. Parent bodies and appendices are emitted explicitly; descendants are not duplicated. Chapter/title/article/part columns come from actual ancestor headings and retained title navigation. Publication display names remain in `code_name`; publication slugs stay in sidecars.
- Publisher revision/currency can be unknown. `snapshot_id` is a local immutable acquisition identity, and never masquerades as a publisher edition. Source nodes carry both separately.
- Navigation classes, tooltips, sharing controls and hidden chrome are excluded. A migration notice is rejected. Missing content selectors, unnumbered uninventoried preambles, empty section bodies, stale rendered headings and duplicate locators fail closed or receive unresolved dispositions.
- Tests cover mixed Roman/hyphen/four-part numbering; frames and cross-city boundaries; repeated citations/families; tables with row/column spans; nested lists emitted once; superscript/subscript; images; history; substantive parents; end-of-document continuation; reserved/empty nodes; actual source chapter TOCs/bodies; CSV/JSON equality; deterministic restart and binding failures.

`test-results.txt` is the exact suite log. Each jurisdiction's `VALIDATION-REPORT.json` distinguishes current routing, current representative text, historical parsing, bounded inventory and whole-corpus validation, with relative evidence paths and hashes. `PACKAGE-SHA256.json` binds the delivered files. `build_reports.py` regenerates the included historical outputs/reports offline. `prepare_retained_replays.py` is an **audit-only fixture importer** that requires the original project's relative cache/receipt paths; runtime commands and tests never invoke it, and all its copied inputs are already bundled.
