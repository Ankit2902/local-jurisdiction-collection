# Full-publication collection handoff

This is the current collector layer for **130 distinct jurisdictions: the original 30 backlog targets and the 100 expansion targets**. Existing expansion IDs `1`–`100` stay stable; original targets use `original-<slug>` IDs in a separate source-backed catalog. It upgrades the earlier bounded acquisition scripts to full publication traversal, durable resume, and reconciliation against retained source inventories. It runs with standalone Python, Node.js and, for some publishers, ordinary headed Chrome. Codex is not a runtime dependency.

Use the [current readiness guide](registry/READINESS.md) and [union catalog API](registry/catalog.py) for target selection and executable plans. The [earlier registry runbook](registry/README.md) describes the sealed 100-target expansion stage. Each source-family runbook explains its installation, source structure, output, tested scope, and limitations:

| Source family | Primary expansion targets | Implementation and runbook |
|---|---:|---|
| Municode | 63 | [Municode](municode/README.md) |
| American Legal | 15 | [American Legal](american-legal/README.md) |
| eCode360 and municipal.codes | 11 | [ICC publishers](ecode/README.md) |
| enCodePlus | 3 | [enCodePlus](encodeplus/README.md) |
| Official HTML, PDF sets, bulk HTML and CodePublishing | 8 | [Official sources](official/README.md) |

The target count is **configuration scope**, not a count of completed full collections. Representative whole-publication runs establish specific adapter capabilities. Previous bounded tests remain in the immutable packages; they are not relabeled as full-publication validation. The prior sealed release contained **100 runnable primary configurations, 45 qualified secondary configurations and 42 unsupported candidates**. The active union catalog adds the original 30 targets, their observed separate publications, source-backed configuration corrections and newly discovered dependencies. Run the no-network plan to obtain current counts; dispatchable configurations are not full live validation or permission to contact a stopped publisher. The [new requirement ledger guide](qa/READINESS.md) retains every original publication scope and records the evidence and unresolved gates separately.

## Plan, collect, resume, verify

The unified launcher creates an isolated pinned Python 3.12 runtime, obtains Node and the Playwright API from the official Python Playwright wheel, and checks an ordinary locally installed Chrome session. Codex, npm and a system Node installation are not required. The tested host is macOS with a graphical desktop. POSIX file locks are required; Windows and unattended headless operation are not qualified.

```sh
# Fresh standalone installation; only dependency installation accesses the network.
python3 collect.py setup --python /path/to/python3.12

# No publisher requests: inspect one source, all targets, or one cohort.
python3 collect.py plan --all --cohort all
python3 collect.py plan --all --cohort original
python3 collect.py doctor --target 60
python3 collect.py plan --target original-cupertino-ca

# Explicit publication only. Repeat run to resume a matching launcher-owned job.
python3 collect.py run --target 60 --out /data/local-codes/target-60
python3 collect.py run --target 60 --out /data/local-codes/target-60

# Read-only source verification; logs are outside the retained evidence.
python3 collect.py verify --target 60 --out /data/local-codes/target-60
```

`doctor.ready` describes runtime/access preflight only. It does not certify a publication. The launcher distinguishes `family_verifier_passed`, `native_capture_verified` and `publication_accepted`; a zero native-file/page exit cannot mark a legal publication complete. Missing required separate publications appear as explicit unresolved dependency IDs and prevent full acceptance. No all-target acquisition is launched by default or by `plan --all`.

The launcher preserves shared family gates and durable refusal history. A missing `/tmp` gate after reboot does not erase an observed stop. It binds each job to its publication, source/configuration and runtime; before/after source hashes prevent a code edit during acquisition from silently becoming a current-code validation pass. Use a fresh output or an explicit family migration when bindings change. Direct family commands remain available for scoped technical work through the [registry dispatcher](registry/collect.py).

Choose a secondary publication with the exact `--publication` identifier returned by the plan. A target's primary publication is not automatically all of that government's law. Unsupported plans identify the missing configuration or operator step; do not substitute a historical source for a current one.

Use fresh output directories outside the sealed evidence packages. The collectors retain source responses, source identifiers, inventory, normalized records, checkpoint state and coverage reports. Keep the whole output directory together. Resume validates the identity, source bindings and cached bytes; it is not an instruction to overwrite mismatched or corrupt evidence. Explicit limits produce incomplete results.

## Image policy

**The collectors do not download separate image assets. All images become the literal `[IMAGE]` in normalized output.** Image-only provisions keep their source ID, heading and placeholder. Deliberate image omissions do not count as missing attachments. Original publisher files may contain embedded images; those source files are retained without separately extracting image binaries. See [IMAGE-POLICY.md](IMAGE-POLICY.md) for the full rule and PDF qualifications.

## Prior sealed validation — not the new readiness ledger

The independent integration suite passed **126 cases across 14 network-disabled commands** from a relocated collector tree and fresh Python 3.12 environment. Actual source evidence is replayed separately. The [QA runbook](qa/README.md), [validation matrix](qa/validation-matrix.json) and each family's `validation-summary.json` distinguish implementation tests, fresh acquisition, retained-source replay and bounded checks.

| Publication or method | Measured scope | Qualification |
|---|---|---|
| Henderson Municode Code of Ordinances | 2,123 TOC IDs, 2,122 owned records, one explicit empty landing page; ten `[IMAGE]` substitutions | Full selected-book reconciliation, matching start/end edition; separate development code and uncodified ordinances remain outside this book |
| Lincoln City Charter, enCodePlus | 188 source nodes; 174 owned bodies and 14 containers; 17 acquired/closing body blocks | Full observed-publication source and nonimage attachment coverage; official legal edition and whole-jurisdiction coverage not asserted |
| Lincoln Access Management Policy, enCodePlus | 14 source nodes, six tables, one `[IMAGE]`; genuine 17-page native PDF | Full source traversal; one externally linked nonimage PDF unavailable |
| San Diego County ordinance index, American Legal | 30/30 independently inventoried nodes; 97 owned blocks; whole native HTML | Full index text; 1,940 underlying nonimage ordinance PDFs remain unacquired. Not a whole nested regulatory-code proof |
| Cleveland Form-Based Code, American Legal | Complete native PDF, 212/212 page text layers | File/page-layer qualification; legal section segmentation and reading order remain unqualified |
| Baltimore bulk Code archive | 6,989 owned records, 172 tables; canonical members reconciled to a pinned Git commit | Full selected Code HTML traversal; twelve required document references unresolved, so combined completeness remains false |
| Worcester Part One / Milwaukee Volume 2 | Complete native files and 659 / 624 physical pages | Full file/page extraction with 109 / two image placeholders; legal section/table semantics and other city publications remain separate |
| New Orleans CZO native HTML | Entire observed legal wrapper, 89 tables, 144 image placeholders | Whole native HTML path qualified; three required document references unresolved |
| Albany Code, eCode360 | All 3,253 discovered nodes resolved: 3,006 owned records, 53 reserved/repealed units and 194 structural units; 28 `[IMAGE]` substitutions | First required PDF HEAD returned 403; six required documents and the closing consistency check remain outstanding. All completion flags stay false |
| Phoenix Charter, municipal.codes | 279 inventoried nodes; 81 resolved, including 73 owned bodies; 198 missing | HTTP 429 stopped the publisher. Partial retained-source proof and offline tests only; no whole-publication completion |

The remaining official-source live checks deliberately used bounded runs against the full dynamic inventories. Their runbooks retain exact counts and missing-document lists. American Legal's recursive nested-code path has meaningful synthetic/retained-source fault tests; the full live text proof above is a separately published flat index. Neither is promoted to a full run across every mapped target.

The table above describes the prior sealed release. The current Municode revision uses a pinned real PDF parser for byte/object/page/content integrity, with image streams left unextracted; this does not establish legal table or section equivalence. Current source owners record fresh runs and stronger retained-source replays under `outputs/collection-readiness-2026-10-17`. The new QA ledger does not reuse representative or bounded proof as an all-target pass.

## What completion means

Read [COMPLETENESS.md](COMPLETENESS.md) before interpreting any success flag. The acceptance checks distinguish:

- **Publication text:** every source-inventoried content unit has a reconciled disposition; parent-owned legal text, descendants, tables, notes and image-only content are accounted for.
- **Images and attachments:** images have ordered `[IMAGE]` placeholders and omission metadata; required nonimage documents have been acquired and hash-bound, with failed or external references retained in a ledger.
- **Edition consistency:** the selected publication identity and source inventory remain consistent across the run, using the checks supported by that publisher.
- **Native files and PDF extraction:** exact file acquisition and physical-page extraction are separate from legal section segmentation, OCR accuracy and table/map meaning.
- **Jurisdiction scope:** all required publication families and uncodified or incorporated material must be resolved separately. Collecting one book does not close this boundary.

Offline verifiers reconstruct coverage from retained raw source evidence and compare it with the delivered records and claims. Fault tests cover omitted, duplicate, corrupt and wrong-edition content, interrupted runs, resume, unexplained empty nodes and required assets. A missing required nonimage asset can leave text complete while preventing full publication completion. A source stop, failed closing check or explicit sample limit cannot silently pass.

## Operating the collectors

Run publishers serially at the documented default rate. Share the family gate across jobs. Respect retained access stops and `Retry-After`; do not clear a stop or change browser identities to work around it. The collectors preserve failures for review. Direct HTTP and headed browser paths have separate tested qualifications where documented; historical direct-HTTP refusals are not evidence that a new direct path is safe to retry.

The scripts retain rendered/source HTML and table structure as well as text. Review image-only provisions, native PDF page coverage, source exceptions and external incorporations before ingestion. Inventory coverage proves that enumerated source units were handled; it does not prove legal currency beyond the publisher's recorded edition or completeness of other law.

The technical team should retain publication-specific outputs, run each offline verifier, and review every false coverage dimension before loading downstream systems. Database loading is outside this handoff.

## Sealed evidence and delivery

The [full-publication validation release](https://github.com/OliverFlint-98/local-jurisdiction-collection/releases/tag/full-publication-collectors-2026-10-17) contains the prior sealed source evidence, run receipts, exact executed revisions, and the collector snapshot for that release. Active readiness changes and evidence are a later stage and are not implicitly covered by that release manifest. The [browsable evidence index](../packages/full-publication-validation-2026-10-17/README.md) links each family. Restore large files with `python3 fetch_evidence.py --package full-publication-validation-2026-10-17`, then run `python3 verify_delivery.py --full`. The [independent integration review](qa/integration-review.json) records relocated replays and the final source-hash comparison.

Required separate publication proofs can be supplied explicitly to `run` or read-only `verify`, for example `--dependency 100-fairfax-public-facilities-manual=/proofs/pfm` when checking publication `100-0506c8bf0a84`. The launcher verifies exact catalog source/configuration and every dependency proof under the current owned runtime, hashes its evidence before and after, and refuses missing, partial, mismatched or changed proof. A native file/page capture cannot substitute for full publication text. See [registry readiness](registry/READINESS.md) and [independent QA readiness](qa/READINESS.md).

## Canonical PDF delivery requirements

Full-publication acceptance follows the original [output contract](../packages/local-extraction-handoff-2026-10-15/OUTPUT-CONTRACT.md#content-fidelity), as amended by the current [image policy](IMAGE-POLICY.md). Retaining a complete native file and extracting every page is a separate, narrower result.

A corrected source representation must drive the exported records, ordered blocks, text and CSV. Adding correct tables or index entries alongside known-bad primary tables is insufficient. Superseded detector output must remain recoverable in an explicitly noncanonical diagnostics field or hash-bound evidence artifact; it must not be counted or exported as a second authoritative representation. Canonical and diagnostic failure counts must be reported separately.

Qualification requires source identity and version binding, every original word/glyph owned once, verified source reading order, preserved headings and nested enumeration, source table headers/cells/spans, and logical sections that continue correctly across page boundaries. Running page numbers and revision dates remain publication controls rather than legal section identities. Source-bound corruption tests and independent comparisons must exercise the actual publication, and JSON/CSV/provenance must agree. A successful parser return, generic test suite, or absence of detected tables alone does not prove these requirements.

Preserve the publisher's literal text, placement, blanks, duplicate printed designations and source defects. Extraction does not authorize correcting an apparent legal drafting error or deciding what a citation was intended to mean. A faithfully retained source ambiguity must be described separately from a missing glyph, incorrect cell, unowned continuation or unresolved source version. No source defect may excuse incorrect extraction, and no scoped repair grants acceptance to the rest of a publication.

Exact `[IMAGE]` placeholders and native original retention follow the current image policy; no image fetching, decoding, extraction, rendering or OCR is allowed.
