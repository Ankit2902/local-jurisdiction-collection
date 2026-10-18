# Local jurisdiction collection

The latest [native, live-recovery and image-policy checkpoint](collectors/qa/followup-proof-receipts/native-and-live-2026-10-18/README.md) passes **41 integrated check programs and 349 unittest cases**. Current scripts preserve exact `[IMAGE]` placeholders and acquire no separate images. The 718-record native derivative retains all 201 source image positions; the completed actual Flagstaff capture retains 882 placeholders. New source-specific native logic and V9 retained-source verification are independently reviewed, while external dependencies, legal edition, final corpus packaging and broader readiness remain explicitly qualified. The paragraph below describes the preceding sealed checkpoint.

The current [canonical PDF and image-policy checkpoint](collectors/qa/followup-proof-receipts/canonical-pdf-2026-10-18/README.md) passes **37 integrated check programs and 198 unittest cases**, alongside the composed **81-test enCodePlus suite**. Source-verified tables and printed indexes now drive JSON and CSV. Across 636 retained PDF records, 13 are corrected, all 795 original failed-cell payloads remain available, and 44 inferred-cell disagreements remain in canonical output. All **201 image placeholders** retain their source positions and ownership; no separate images are collected. Full-publication acceptance remains source-specific and unresolved gaps stay explicit.

The earlier [source-fidelity update](collectors/qa/followup-proof-receipts/source-fidelity-2026-10-18/summary.json) adds corroborated Dallas PDF references, explicit short Fort Worth dispositions, and PDF whole-word/diagnostic corrections. Validation passed 146 American Legal cases, 56 enCodePlus cases, and 34 integrated check programs. These are tested collector improvements; remaining source, access, document and legal-structure gaps are still listed in the current readiness ledger.

Technical handoff for source discovery, acquisition scripts, parsing, and validation of the **original 30-jurisdiction backlog and 100 additional local jurisdictions**. The expansion adds major cities, populous counties, and coverage in states missing from the earlier inventory. The newest stage provides standalone full-publication collectors, a target registry, resume workflows, and source-derived completeness checks. Earlier sealed packages retain their bounded sample results. Representative whole-publication tests qualify specific collector paths; no completed collection of all 100 jurisdictions or new database audit is claimed.

## Full-publication collectors

Start with the [integrated setup and execution guide](collectors/ops/README.md), [full-collection runbook](collectors/README.md), and [completeness criteria](collectors/COMPLETENESS.md). The current combined registry covers the original 30 jurisdictions and the 100 expansion targets. Run `python3.12 collect.py plan --all` for the exact current primary/secondary configurations, required publication dependencies and unsupported discoveries. Configuration coverage is not a count of completed collections.

**Image policy:** the current collectors omit separate image downloads and replace images with `[IMAGE]` in normalized output; see the [policy and verification requirements](collectors/IMAGE-POLICY.md).

The earlier [source-structure and image-policy verification](collectors/qa/followup-proof-receipts/structure-recovery-2026-10-18/README.md) passed 36 integrated programs and 173 unittest cases against the updated scripts. Actual normalized Boston and Flagstaff output passes the image audit; the new 1,870-file evidence package contains no separate image binaries. Full-publication gaps remain explicit.

The [October 18 integrity corrections](packages/collection-integrity-corrections-2026-10-18/README.md) add named-configuration binding, explicit per-document semantic acceptance, deterministic inline-image identities and a source-auditor offset fix. The checkpoint includes a fresh isolated setup, 31 passing regression programs and an actual full-source verification that correctly keeps unqualified PDF contents incomplete. Remaining collection and semantic gaps are preserved.

The [sealed readiness checkpoint](packages/collection-readiness-checkpoint-2026-10-17/README.md) preserves selected complete and incomplete source captures, the 282-check isolated baseline, focused final fixes, and exact collector revisions. Its [checkpoint ledger](collectors/qa/readiness-requirements.json) records the historical 224 entries, 186 dispatch configurations, 38 unqualified candidates and 128 stopped configurations. The current catalog covers 130 governments and 225 publication entries: 195 are dispatchable configurations, 30 remain unqualified, and observed workflow stops prohibit automatic acquisition for 131 entries. These are configuration and operational counts, not completed-collection counts or a claim that every publisher URL is unavailable. The [active follow-up ledger](collectors/qa/followup-requirements.json) and [follow-up findings](collectors/qa/FOLLOWUP-READINESS.md) distinguish source-bound proof, discovered separate publications and remaining collection gaps.

The [follow-up validation checkpoint](packages/collection-validation-followup-2026-10-17/README.md) preserves its sealed runtime, image-policy regressions, selected full-publication source captures and exact validation evidence. Its [release archive](https://github.com/OliverFlint-98/local-jurisdiction-collection/releases/tag/collection-validation-followup-2026-10-17) restores the two large source files through `python3 fetch_evidence.py --package collection-validation-followup-2026-10-17`. Current normalized-output checks include section, PDF-page and reference streams plus supplemental metadata. This checkpoint retains explicit incomplete outcomes and is not a claim that all 130 jurisdictions are ready.

The [operational validation checkpoint](packages/collection-operational-validation-2026-10-17/README.md) contains the then-current standalone collectors, full Flagstaff and King County source replays, Dallas table validation, and image-placeholder fixes in both body text and metadata. Its [release archive](https://github.com/OliverFlint-98/local-jurisdiction-collection/releases/tag/collection-operational-validation-2026-10-17) preserves exact executed versions and scoped positive and negative evidence. Follow the current root launcher and runbooks; historical snapshots are provenance. Original publisher files may inherently contain embedded images, but normalized outputs exclude their payloads and acquisition excludes separate image assets. Fresh acquisitions still running at sealing are explicitly pending.

Two results finished after the operational archive was sealed. The [fresh standalone Overland primary run](OVERLAND-LIVE-RESULT-2026-10-18.json) passed acquisition and common verification for 6,279 records, 552 tables and five required nonimage documents, with 531 `[IMAGE]` placeholders and no separate image acquisitions. Full native export remains unavailable; edition and jurisdiction completeness remain false, and PDF integrity does not establish normalized attachment text/table fidelity. [Burlington's current read-only verification](BURLINGTON-VERIFY-RESULT-2026-10-18.json) reproduced its incomplete coverage with all 1,126 files unchanged. These compact terminal receipts are versioned directly in Git; they supersede the archive's earlier pending status only for their exact scope and do not include a new full acquisition archive.

A subsequent correction tightens full-publication acceptance for required PDF attachments: every PDF now needs explicit text and table qualifications. The earlier Overland receipt remains immutable, but its successful result does not establish PDF semantics. Current validation also binds named enCodePlus configurations and corrects a control-character offset error in the independent source auditor. See the [current readiness notes](collectors/qa/FOLLOWUP-READINESS.md) for the precise scopes and remaining gaps.

The registry resolves each publication to an explicit source and collector configuration. Plans identify unsupported sources and unresolved publication families before acquisition. Full traversal is the default; limited, interrupted, or source-inconsistent runs cannot silently become complete. Publication text, attachments, edition consistency, native-file coverage, and jurisdiction scope remain separate measures.

The [first full-publication release](https://github.com/OliverFlint-98/local-jurisdiction-collection/releases/tag/full-publication-collectors-2026-10-17) preserves the earlier sealed validation evidence and its exact collector snapshot. Its independent offline suite passed 126 cases; see its [evidence index](packages/full-publication-validation-2026-10-17/README.md). The active `collectors/` layer contains subsequent validation fixes and source-specific runbooks. Full publication validation is ongoing; selected live and retained-source results remain incomplete where required documents, source consistency or semantic qualification are unresolved. Historical packages below are provenance, not the default current collector entry points.

## Expanded scope: 100 additional jurisdictions

Use the [combined 100-jurisdiction index](EXPANDED-SCOPE.md) to find the latest result and runbook for every target, or [expanded-scope-index.json](expanded-scope-index.json) for machine-readable scope, source, qualification and next-action fields.

The [recommendation inventory](packages/local-jurisdiction-expansion-2026-10-17/recommendations.json) records the selection rationale, sources, ordering and waves. Its [visual report](packages/local-jurisdiction-expansion-2026-10-17/jurisdiction-shortlist.html) presents the proposed coverage. The inventory starts from 74 existing scope entries across 12 states; the proposals would bring the planned scope to 174 jurisdictions across all 50 states. These are scope counts, not collected-corpus counts.

| Wave | Scope | Handoff |
|---|---|---|
| 1 and 2 | Recommendations 1–57 | [README](packages/expanded57-validation-2026-10-17/README.md) · [jurisdiction matrix](packages/expanded57-validation-2026-10-17/JURISDICTIONS.md) · [machine-readable results](packages/expanded57-validation-2026-10-17/results57.json) |
| 3 | Recommendations 58–100 | [README](packages/wave3-validation-2026-10-17/README.md) · [jurisdiction matrix](packages/wave3-validation-2026-10-17/JURISDICTIONS.md) · [machine-readable results](packages/wave3-validation-2026-10-17/results43.json) |

Waves 1 and 2 passed standalone live acquisition through normalization for 56 of 57 targets; Milwaukee remains partial. Native publisher downloads are a separate measure: 49 passed, two are partial, five were unavailable and one was blocked. Each row identifies the tested publications, sample size, exact command, retained evidence, source currency, and remaining work. Wave 3 passed standalone live acquisition through normalization for all 43 targets; native-download outcomes are 31 passed, eight partial due to edition qualifications, and four unavailable for the primary code. Separate Cambridge and Fairfax zoning exports passed. Across all 100 expansion targets, the result is 99 standalone sample passes and one partial result, with 80 native-download passes, ten partial, nine unavailable and one blocked. No complete jurisdiction corpus is claimed.

Start with each group’s README for the tested runtime and fresh-output command. HTTP and ordinary headed-browser collectors run without Codex. Browser automation uses a normal locally installed Chrome session with Playwright; macOS was tested. No claim is made that all collectors have been tested on Linux, Windows, or unattended headless infrastructure. All groups include offline validation or deterministic parsing checks.

The [release](https://github.com/OliverFlint-98/local-jurisdiction-collection/releases/tag/expanded-scope-validation-2026-10-17) contains the complete sealed wave archives. Large evidence files are restored with the helper described below. Scripts and reports remain browsable in Git.

## Original 30-jurisdiction backlog: historical bounded results

Use these packages in precedence order; later work supersedes earlier runtime and validation claims for the jurisdictions it covers.

| Scope | Current handoff | Key result |
|---|---|---|
| 14 eCode360 jurisdictions | [Headed-browser handoff](packages/ecode360-headed-2026-10-16/README.md) · [14-city matrix](packages/ecode360-headed-2026-10-16/SOURCE-MATRIX.md) | All 14 passed bounded standalone headed acquisition → parsing → CSV/JSON; 134 sampled provisions. Thirteen actual publisher PDFs downloaded without login. |
| Other jurisdictions in the 24 formerly CUA-dependent group | [Standalone handoff](packages/local-extraction-standalone-2026-10-15/README.md) · [24-city matrix](packages/local-extraction-standalone-2026-10-15/SOURCE-MATRIX.md) | Municipal.codes bounded headed/browser-export pilots and CodePublishing operator-download/local-import workflows. Its earlier eCode360 gaps are superseded by the headed-browser handoff above. |
| All 30 jurisdictions and the other source families | [Live acquisition handoff](packages/local-extraction-e2e-2026-10-15/README.md) · [30-city matrix](packages/local-extraction-e2e-2026-10-15/SOURCE-MATRIX.md) · [Technical plan](packages/local-extraction-e2e-2026-10-15/TECHNICAL-PLAN.md) | Bounded live acquisition, retained sources, parser exports, and source-family acceptance gates. Later standalone packages supersede their covered runtime claims. |

The latest eCode360 result includes independent comparison of **134 provisions, eight tables, and 309 cross-references**. All 13 publisher PDFs yielded selected-section JSON/CSV and matching operative text/title; twelve passed bounded text-layout checks. **San Leandro's incorporated map remains a semantic-review gate. Santa Clara's tested publication had no Download control, but its DOM extraction passed.** The PDF samples overlap the DOM provisions and must not be added as unique records.

The current non-eCode360 distinctions remain explicit: Berkeley, Petaluma, Sonoma and Everett have bounded standalone pilots; Bellingham's earlier standalone pilot is partial because a later 429 prevented its final consistency check. Flagstaff, Fremont, San Carlos, Burien and Renton have tested manual publisher downloads followed by standalone local importers. No full-corpus completion is inferred.

## Historical scripts and execution evidence

- [eCode360 browser acquisition and DOM export](packages/ecode360-headed-2026-10-16/ecode360/README.md)
- [eCode360 actual PDF downloads and narrow PDF-native selected-section parsing](packages/ecode360-headed-2026-10-16/publisher-downloads/README.md)
- [Municipal.codes standalone acquisition and publisher HTML exports](packages/local-extraction-standalone-2026-10-15/municipal-codes/README.md)
- [CodePublishing ordinary publisher download and local importer](packages/local-extraction-standalone-2026-10-15/codepublishing/README.md)
- [Other source families and technical acceptance](packages/local-extraction-e2e-2026-10-15/TECHNICAL-PLAN.md)

Follow the per-package dependency installation and commands. Run against new output directories, preserve original evidence, and distinguish fresh acquisition from offline replay. The tested headed path requires a graphical Chrome session; Linux/Windows execution and headless scheduling were not established by the macOS headed-browser result. Rate limits stop the affected host rather than triggering automatic retries.

The current collectors implement publication-wide enumeration, source-node disposition reconciliation, checkpoints, and edition checks for their supported source structures. Consult the current runbook for tested paths and remaining source or semantic gaps. Database import is outside this work.

## Complete package history and downloads

All directories and archives below preserve their delivered bytes. Historical reports remain available for provenance; do not treat their statuses as newer than the packages listed above.

| Stage | Browsable package | Original archive |
|---|---|---|
| Source discovery and original extraction plan | [Original handoff](packages/local-extraction-handoff-2026-10-15/README.md) | [ZIP](archives/local-extraction-handoff-2026-10-15.zip) |
| Initial source-family validation | [Validation handoff](packages/local-extraction-validation-2026-10-15/README.md) | [ZIP](archives/local-extraction-validation-2026-10-15.zip) |
| Live acquisition and export validation | [E2E handoff](packages/local-extraction-e2e-2026-10-15/README.md) | [ZIP](archives/local-extraction-e2e-2026-10-15.zip) |
| Standalone and publisher-export validation | [Standalone handoff](packages/local-extraction-standalone-2026-10-15/README.md) | [ZIP](archives/local-extraction-standalone-2026-10-15.zip) |
| eCode360 headed acquisition and publisher PDFs | [Latest eCode360 handoff](packages/ecode360-headed-2026-10-16/README.md) | [ZIP](archives/ecode360-headed-2026-10-16.zip) |

[Archives](archives/) contains the original backlog ZIPs and supplied SHA-256/verification sidecars. The expanded validation archives, dated October 17, 2026, are attached to the repository release; their expected hashes and restoration members are recorded in [RELEASE-ASSETS.json](RELEASE-ASSETS.json).

## Verify the repository delivery

```sh
git clone https://github.com/OliverFlint-98/local-jurisdiction-collection.git
cd local-jurisdiction-collection
python3 verify_delivery.py

# Download the full expanded validation ZIPs and restore large evidence files.
# Private repository access uses the existing Git credential helper.
python3 fetch_evidence.py
python3 verify_delivery.py --full
```

These helpers require Python 3.10 or later and only the standard library. The verifier checks delivered collector/package/archive files against [DELIVERY-MANIFEST.json](DELIVERY-MANIFEST.json). Before release evidence is restored, it reports `PASS_GIT_FILES` and lists the deferred files. `--full` requires every byte, including the full release archives. The download helper checks archive SHA-256, then restores only the manifest’s exact missing large files and verifies their hashes. It refuses to overwrite altered evidence.

You can restrict restoration with `--package full-publication-validation-2026-10-17`, `--package expanded57-validation-2026-10-17` or `--package wave3-validation-2026-10-17`. For a ZIP downloaded separately, use `--package NAME --from-archive /path/to/NAME.zip`. Private releases require repository access; no credentials are included in this handoff.

Individual sealed packages also have manifests and offline verification commands. Run any tests that write files in a working copy or fresh output directory so that original evidence remains verifiable. Hash checks establish byte integrity, not legal completeness or ongoing publisher availability.

This repository includes scripts, runbooks, source inventories, public-source captures, actual publisher files, screenshots/renders, validation receipts, exact executed script revisions, regression tests, and sample exports. Local virtual environments, installed browser runtimes, browser profiles, Python caches, and unrelated CompliSolv project data are excluded. Git attributes disable line-ending conversion to preserve sealed source and evidence hashes. Files of 50 MiB or less in the new packages are stored in Git. Larger evidence and the complete expanded validation ZIPs are stored as repository release assets, with their exact restoration paths and SHA-256 hashes in the delivery manifests. Git LFS is not required.
