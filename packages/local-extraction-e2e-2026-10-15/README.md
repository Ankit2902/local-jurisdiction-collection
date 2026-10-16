# Local code extraction: live-tested technical handoff

Prepared October 15, 2026. This second validation pass covers the **30 outstanding jurisdictions in the reviewed project inventory**. It does not audit the current database. All 30 now have a successful **bounded live acquisition → retained source → delivered parser → verified export** path. They remain outstanding for full collection; this task completed no whole-jurisdiction corpus or database import.

Six Sol subagents developed and exercised the source-specific packages. The parent independently reran all six Python suites (**161 tests passed**), the JavaScript acquisition checks (**27 checks passed**) and all six package hash manifests (**3,897 references verified, zero mismatches**). Exact results, commands, source hashes and logs are in [the independent review](integration/independent-review/RESULTS.json) and [artifact review](integration/independent-review/ARTIFACT-REVIEW.json). The successful live acquisitions are separately documented in each package's E2E report; offline regression results are not counted as fresh acquisition.

## Start here

- [SOURCE-MATRIX.md](SOURCE-MATRIX.md) lists all 30 jurisdictions, current source URLs, tested output counts, runtime results and remaining gates. [SOURCE-MATRIX.json](SOURCE-MATRIX.json) is the machine-readable equivalent, with per-source evidence references and additional publication-family discoveries.
- [TECHNICAL-PLAN.md](TECHNICAL-PLAN.md) sets out the source-driven extraction sequence and acceptance criteria.
- Each package's README below contains dependency installation, exact entry points, fresh-output examples, supported CUA usage and offline reproduction commands.
- [verify_bundle.py](verify_bundle.py) checks this entire portable delivery. It needs only Python's standard library. [BUNDLE-MANIFEST.json](BUNDLE-MANIFEST.json) contains the hashes.

## Current source grouping and tested runtimes

| Source type | Jurisdictions | Delivered live-qualified method | Runtime limits |
|---|---:|---|---|
| [eCode360](ecode360/README.md) | 14 | Supported CUA module → exact legal DOM → importer/parser → JSON/CSV; 134 sample records | Plain HTTP blocked for all 14. Standalone Chrome blocked for Foster City; other 13 not run. |
| [Code Publishing](codepublishing/README.md) | 5 | Supported CUA module → actual chapter/frame → CLI replay; 77 current records | Standalone Chrome challenged for all five current sources. Legacy SeaTac test is separate. |
| [Municipal.codes](municipal-codes/README.md) | 5 | Supported CUA module → primary Contents/chapter/difficult samples → section-card parser; 125 records | HTTP and standalone Chrome challenged for all five. Bellingham Charter-family Contents also challenged in CUA. |
| [CivicPlus PDF](civicplus/README.md) | 2 | Rockland: HTTP index and PDFs. Portland: verified standalone Chrome or CUA index, then HTTP PDF and parser | Portland plain HTTP index certificate-chain failure remains. PDF semantic exceptions remain despite integrity checks passing. |
| [Gridics / Cupertino](gridics/README.md) | 1 | Standalone Playwright and supported CUA; 59 records from three standalone routes; acquisition interruption/resume tested | Full observed tree expanded, but complete legal body collection and legal currency remain unverified. |
| [Open Law XML / San Mateo](bulk-and-official-html/README.md) | 1 | Live repository HEAD → pinned archive → Git blob checks → bounded actual XInclude traversal → XML parser | 96 Charter +39 Title 1 records; other includes excluded. A commit is not a legal current-through date. |
| [Municode / Daly City](bulk-and-official-html/README.md) | 1 | Public API discovery/TOC/content → parser; adoption text matches both CUA and standalone Chrome | Three sample provisions only; table/appendix browser parity and full acquisition remain. |
| [First-party HTML / King County](bulk-and-official-html/README.md) | 1 | Fresh CUA landing discovery → HTTP original HTML and Word → parser | Hybrid discovery/acquisition, not wholly unattended. 261 records across three documents; source discrepancies retained. |

The largest three families account for **24 jurisdictions**, and their successful live path currently requires Codex's supported CUA runtime. CUA helpers are runnable modules within that runtime; they are not general standalone Node browser clients. The standalone implementations are also delivered, with successful and blocked attempts explicitly recorded. A team without CUA access should treat transport qualification for those 24 as an implementation dependency and obtain an authorized publisher export or establish another supported acquisition path before a full run.

The source inventory changed materially: **Foster City and SeaTac moved from Code Publishing to eCode360**, and **Daly City uses Municode rather than the original eLaws assignment**. Current counts are therefore 14 eCode360, five Code Publishing, five Municipal.codes and six jurisdictions across the other five source types. Do not run the old seven-city Code Publishing or Daly City eLaws plan unchanged.

## What live testing resolved

- eCode360 current bodies are now captured and parsed for every mapped jurisdiction, including both migrations. A real Foster City list-wrapper defect was fixed so A.–J. markers survive.
- Code Publishing's frame/chapter paths were exercised live. Fremont's business chapter preserves 147 P0–P3 paragraphs; its visible reference table preserves 2,212 rows and 4,422 cells, excluding hidden UI clones.
- Municipal.codes primary inventories total 16,863 observed nodes. All five have matching before/after primary inventory, currency and chapter-body checks. Actual tables, appendix clauses and image markers broaden the sample beyond adoption chapters. Extra publication-family scope stays explicit.
- Cupertino now has successful live acquisition in both runtimes, a deliberate interruption/resume, and 2,687 observed navigation identities with zero remaining closed controls. Title 1's 65 semantic fingerprints agree across runtimes. The nuisance table preserves 13 rows/26 cells; the ordinance-list table preserves 2,290 rows/4,580 cells. The 2,621 unacquired legal bodies remain unresolved.
- Rockland's earlier live HTTP blocker is closed. Portland's standalone and CUA paths produce equal ordered provisions. Selected PDF table/line defects have source-hash-bound recovery rules that reject changed input.
- San Mateo's archive is acquired from a pinned live commit and all 291 Git blobs are checked. The parser follows actual includes in the declared Title 1/Charter scope; unsupported mixed parent-body/include content fails explicitly.
- King County now retains original CP1252 HTTP bytes. Official Word documents corroborate the HTML's numbering and Charter-date conflicts, so the scripts preserve and flag them. Daly City's API tree and publication metadata are stable before/after the bounded run, and its adoption text matches both browser runtimes.

## Reproduce verification

Unzip the entire bundle, keep its relative directory structure, and verify it before running anything that writes new files:

```sh
python3 verify_bundle.py
python3 -m venv /tmp/local-code-review
/tmp/local-code-review/bin/python -m pip install -r requirements-review.txt
/tmp/local-code-review/bin/python integration/run_offline_review.py
/tmp/local-code-review/bin/python integration/review_artifacts.py --node node
```

Use a modern Python/OpenSSL build and Node 20+. The independent review used Python 3.12.14 and Node 24.19.0. Package reports retain the actual live interpreter, Playwright and browser versions; they differ by package. Browser installations and virtual environments are deliberately excluded from delivery. Package-specific requirements describe normal dependency installation. CUA does not expose browser version/executable or response headers through every supported operation; reports identify unavailable metadata.

These review commands perform no fresh acquisition. They write review logs, so the root manifest will subsequently report those files as changed; that is expected after a rerun. Keep an untouched original bundle for comparison. Do not use `verify_bundle.py --write` to conceal differences: that option intentionally reseals changed content and is for reviewed bundle maintenance only.

For live repeats, use each package's documented commands and **new output directories/attempt IDs**. Refresh the discovery/identity/version markers first. A retained source fixture replay is not a live run. Some helpers were hardened during validation; accepted captures identify their exact executed revision, and those revisions are preserved. The final immutable-capture guards were tested, but not every earlier city was reacquired with the final helper revision.

## Remaining acceptance work

The reports qualify methods on bounded samples. They do not certify complete publication scope, every legal structure, legal currency or whole-corpus coverage. The main handoff gates are transport portability for the CUA-dependent families; complete publication inventories and dispositions; full-run version reconciliation; and semantic review of broader tables, images, appendices and incorporated material.

PDF integrity passing is especially distinct from semantic completion: Portland retains 10 exceptions and Rockland 28, including an unreadable symbol, other table cases and obscured Charter text. King County retains numbering/date conflicts. Cupertino has unresolved route identities and unacquired bodies. Foster City's Estero district publication and Municipal.codes extra families need explicit scope decisions.

Earlier reports, fixtures and failed attempts are retained for traceability. Use the package **E2E-VALIDATION.json** and current README as the current qualification; filenames marked historical, baseline or v1 describe earlier evidence. The original handoff and first validation directories were preserved separately and were not edited during this pass.
