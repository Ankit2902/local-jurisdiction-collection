# Local-jurisdiction extraction scripts and validation handoff

**Prepared October 15, 2026. Six Sol agents validated methods for the 30 outstanding jurisdictions in the project handoff inventory. The independent parent review passed all 126 tests across six packages.** No current database audit was used, and no full-jurisdiction collection or import was completed here.

The result is runnable source acquisition/import and parser/replay code, exact retained evidence, meaningful regressions, sample exports and source-specific remaining work. These are completed method-validation packages. They are not a claim that every unattended acquisition path or full corpus is production-qualified.

Start with [the 30-jurisdiction source matrix](SOURCE-MATRIX.md), its [machine-readable equivalent](SOURCE-MATRIX.json), and [technical-team execution/acceptance](TECH-TEAM-ACCEPTANCE.md). Every source package has its own setup, commands, evidence and validation report.

## Current source grouping and delivered code

| Current source method | Jurisdictions | Main runnable code | What has been established |
|---|---:|---|---|
| eCode360 | 13 | [ecode360.py](ecode360/ecode360.py), [instructions](ecode360/README.md) | 12 historical chapter DOMs replayed: 115 records; all 12 current mapped publisher identities observed; four current text observations and one current Santa Monica section excerpt parser-tested. Additional Foster City current root verified; its current body sample remains pending. |
| Code Publishing | 6 | [cp_collect.py](codepublishing/cp_collect.py), [instructions](codepublishing/README.md) | All 7 baseline historical sources replayed: 52 records, including historical Foster City. Current roots observed; Renton and Flagstaff title/chapter checks. Exact heading readiness protects against stale hash navigation. |
| Municipal.codes | 5 | [municipal_codes_cli.py](municipal-codes/municipal_codes_cli.py), [instructions](municipal-codes/README.md) | Current primary-code Contents DOMs: 16,863 navigation nodes; current and retained chapter parsing for all 5, totaling 54 section cards plus 2 parent notes. |
| CivicPlus PDFs | 2 | [civicplus.py](civicplus/civicplus.py), [instructions](civicplus/README.md) | Portland 44-document and Rockland 21-document indexes; real Chapter 13, Chapter 1 and Charter PDFs parsed, with layout-specific review gates. |
| Gridics | 1 | [gridics.py](gridics/gridics.py), [acquire.py](gridics/acquire.py), [instructions](gridics/README.md) | Cupertino Title 1: 65/65 source UUIDs reconciled; 56 numbered sections and 2 chapter notes; real table retains 13 rows/26 cells. |
| Open Law XML | 1 | [san_mateo.py](bulk-and-official-html/san_mateo.py), [instructions](bulk-and-official-html/README.md) | San Mateo immutable repository tree and actual XML Title 1/Charter parsing, including lists and a table. |
| Municode | 1 | [daly_city.py](bulk-and-official-html/daly_city.py), [instructions](bulk-and-official-html/README.md) | Daly City's current official source; 2,506-node live tree and 4 representative provisions including a table and Appendix D amendment. |
| First-party title HTML | 1 | [king_county.py](bulk-and-official-html/king_county.py), [instructions](bulk-and-official-html/README.md) | King County 31-title index; retained current title/Charter HTML, complete heading-range parser and 14 selected representative exports. TOC/body discrepancies remain visible. |

The source grouping changed in two places. Foster City's legacy publisher explicitly announces migration to [eCode360 FO4449](https://ecode360.com/FO4449); the Estero Municipal Improvement District Code is a separate unresolved family. Daly City's [official homepage](https://www.dalycity.org/) links Municode; its observed Browse Codes destination is the [Daly Municipal Code](https://library.municode.com/ca/daly_city/codes/code_of_ordinances). The old eLaws route is retained only as historical context. These changes do not change the 30-jurisdiction count.

## Independent verification

The parent agent ran the delivered suites under Python 3.12 with the combined pinned dependencies in `requirements-review.txt`:

| Package | Passing tests |
|---|---:|
| eCode360 | 22 |
| Code Publishing | 27 |
| Municipal.codes | 24 |
| Gridics | 17 |
| CivicPlus PDF | 15 |
| XML / King County / Daly City | 21 |
| **Total** | **126** |

[Independent results and Python source hashes](integration/independent-review/RESULTS.json) and the adjacent exact test logs are included. A targeted CivicPlus cache regression was additionally rerun after the final cache guard change; it is not double-counted in the 126 tests. Parent CLI smoke checks also replayed Renton and Berkeley into output directories outside the bundle. Per-package reports contain agent source comparisons, acquisition metadata and hash manifests.

To reproduce the independent offline review from the extracted bundle:

```sh
python 3 -m venv .review-venv
.review-venv/bin/python -m pip install -r requirements-review.txt
.review-venv/bin/python integration/run_offline_review.py
```

Use Python 3.12 or another supported modern Python for this combined environment. Source packages also document their narrower runtime requirements. The offline review uses included fixtures and makes no live collection requests. `integration/run_offline_review.py --packages municipal-codes` can rerun a selected package and merge its result into the local review report. Optional standalone browser helpers have separate Node/Playwright dependencies documented in their source README.

The tests exercise actual retained source paragraphs/cards and source identities, not merely output row counts. They also cover observed failure cases: Contents pages treated as provisions, repeated citations, stale asynchronous navigation, truncated DOM export, nested-content duplication, body continuation loss, PDF revision headers, raw tampering and incompatible resume state. Synthetic rich-structure tests are clearly separated from real-source validation.

## Remaining work that materially affects deployment

- **Transport qualification:** direct HTTP returned 403 for the main vendor groups; supported in-app browser navigation succeeded for many routes. Some eCode child routes remained challenged. Delivered standalone Playwright helpers for Municipal.codes/Gridics were not live-executed in this review. Code Publishing/eCode/King/PDF workflows support retained browser artifacts where needed; do not mistake that for a validated unattended browser service.
- **Full scope and inventories:** additional Charters, Petaluma Zoning/SmartCode, Flagstaff Employee Handbook, Foster City's Estero district code, King County Board of Health and other families need explicit scope decisions. A complete primary-code DOM or one title's reconciliation does not settle every family.
- **Source discrepancies:** King County has printed TOC/body numbering mismatches and a Charter landing/document date conflict. San Mateo's cross-file include expansion remains integration work. PDF mixed-content/table/locator-overlap pages require review. The per-source reports identify the exact evidence.
- **Full collection and edition closure:** acquire the remaining bodies, reconcile all independent source nodes to dispositions and compare beginning/end source versions. A Git commit, hash or retrieval date is not automatically a legal current-through date. The sample exports intentionally stay incomplete.

Each module exports the legacy 16-field CSV/JSON envelope with additional provenance, source-node, semantic and disposition data as documented. They are separate source pilots; integrating them into the team's scheduler/storage/import pipeline remains technical-team work. Failed/truncated acquisition attempts are preserved as negative evidence and explicitly identified so they cannot silently become legal text.

`BUNDLE-MANIFEST.json` hashes the delivered files; `verify_bundle.py` verifies them after extraction. Raw evidence and fixtures make the ZIP self-contained. Original project paths that appear in evidence are provenance labels; runtime replay commands use packaged inputs. No virtual environments, browser profiles, credentials or production database are included.
