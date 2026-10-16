# Local jurisdiction collection

Technical handoff for source discovery, acquisition scripts, parsing, and validation of the **30 jurisdictions in the reviewed collection backlog**. This repository contains all five completed handoff stages, their source evidence, tested scripts, sample exports, and original ZIP archives. It does not contain a new database audit or completed full-jurisdiction corpora.

## Start with the current results

Use these packages in precedence order; later work supersedes earlier runtime and validation claims for the jurisdictions it covers.

| Scope | Current handoff | Key result |
|---|---|---|
| 14 eCode360 jurisdictions | [Headed-browser handoff](packages/ecode360-headed-2026-10-16/README.md) · [14-city matrix](packages/ecode360-headed-2026-10-16/SOURCE-MATRIX.md) | All 14 passed bounded standalone headed acquisition → parsing → CSV/JSON; 134 sampled provisions. Thirteen actual publisher PDFs downloaded without login. |
| Other jurisdictions in the 24 formerly CUA-dependent group | [Standalone handoff](packages/local-extraction-standalone-2026-10-15/README.md) · [24-city matrix](packages/local-extraction-standalone-2026-10-15/SOURCE-MATRIX.md) | Municipal.codes bounded headed/browser-export pilots and CodePublishing operator-download/local-import workflows. Its earlier eCode360 gaps are superseded by the headed-browser handoff above. |
| All 30 jurisdictions and the other source families | [Live acquisition handoff](packages/local-extraction-e2e-2026-10-15/README.md) · [30-city matrix](packages/local-extraction-e2e-2026-10-15/SOURCE-MATRIX.md) · [Technical plan](packages/local-extraction-e2e-2026-10-15/TECHNICAL-PLAN.md) | Bounded live acquisition, retained sources, parser exports, and source-family acceptance gates. Later standalone packages supersede their covered runtime claims. |

The latest eCode360 result includes independent comparison of **134 provisions, eight tables, and 309 cross-references**. All 13 publisher PDFs yielded selected-section JSON/CSV and matching operative text/title; twelve passed bounded text-layout checks. **San Leandro's incorporated map remains a semantic-review gate. Santa Clara's tested publication had no Download control, but its DOM extraction passed.** The PDF samples overlap the DOM provisions and must not be added as unique records.

The current non-eCode360 distinctions remain explicit: Berkeley, Petaluma, Sonoma and Everett have bounded standalone pilots; Bellingham's earlier standalone pilot is partial because a later 429 prevented its final consistency check. Flagstaff, Fremont, San Carlos, Burien and Renton have tested manual publisher downloads followed by standalone local importers. No full-corpus completion is inferred.

## Scripts and execution

- [eCode360 browser acquisition and DOM export](packages/ecode360-headed-2026-10-16/ecode360/README.md)
- [eCode360 actual PDF downloads and narrow PDF-native selected-section parsing](packages/ecode360-headed-2026-10-16/publisher-downloads/README.md)
- [Municipal.codes standalone acquisition and publisher HTML exports](packages/local-extraction-standalone-2026-10-15/municipal-codes/README.md)
- [CodePublishing ordinary publisher download and local importer](packages/local-extraction-standalone-2026-10-15/codepublishing/README.md)
- [Other source families and technical acceptance](packages/local-extraction-e2e-2026-10-15/TECHNICAL-PLAN.md)

Follow the per-package dependency installation and commands. Run against new output directories, preserve original evidence, and distinguish fresh acquisition from offline replay. The tested headed path requires a graphical Chrome session; Linux/Windows execution and headless scheduling were not established by the macOS headed-browser result. Rate limits stop the affected host rather than triggering automatic retries.

Full collection still requires publication-wide enumeration, source-node disposition reconciliation, attachments and full-run edition checks. Database import was outside this work.

## Complete package history and downloads

All directories and archives below preserve their delivered bytes. Historical reports remain available for provenance; do not treat their statuses as newer than the packages listed above.

| Stage | Browsable package | Original archive |
|---|---|---|
| Source discovery and original extraction plan | [Original handoff](packages/local-extraction-handoff-2026-10-15/README.md) | [ZIP](archives/local-extraction-handoff-2026-10-15.zip) |
| Initial source-family validation | [Validation handoff](packages/local-extraction-validation-2026-10-15/README.md) | [ZIP](archives/local-extraction-validation-2026-10-15.zip) |
| Live acquisition and export validation | [E2E handoff](packages/local-extraction-e2e-2026-10-15/README.md) | [ZIP](archives/local-extraction-e2e-2026-10-15.zip) |
| Standalone and publisher-export validation | [Standalone handoff](packages/local-extraction-standalone-2026-10-15/README.md) | [ZIP](archives/local-extraction-standalone-2026-10-15.zip) |
| eCode360 headed acquisition and publisher PDFs | [Latest eCode360 handoff](packages/ecode360-headed-2026-10-16/README.md) | [ZIP](archives/ecode360-headed-2026-10-16.zip) |

[Archives](archives/) also contains the supplied SHA-256 and archive-verification sidecars. The latest package is named by its UTC date, October 16, 2026.

## Verify the repository delivery

```sh
git clone https://github.com/OliverFlint-98/local-jurisdiction-collection.git
cd local-jurisdiction-collection
python3 verify_delivery.py
```

The standard-library verifier checks every delivered package/archive file against [DELIVERY-MANIFEST.json](DELIVERY-MANIFEST.json). Individual sealed packages also have their own manifests and verification commands. Run tests in a working copy if they write logs, so the original evidence remains verifiable.

This repository includes scripts, runbooks, source inventories, public-source captures, actual publisher files, screenshots/renders, validation receipts, exact executed script revisions, regression tests, and sample exports. Local virtual environments, installed browser runtimes, browser profiles, Python caches, and unrelated CompliSolv project data are excluded. Git attributes disable line-ending conversion to preserve sealed source and evidence hashes. Files are stored directly in Git; Git LFS is not required for this delivery.
