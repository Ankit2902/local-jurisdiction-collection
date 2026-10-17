# Full-publication collection handoff

This is the current collector layer for the **100 additional jurisdictions** in the expansion inventory. It upgrades the earlier bounded acquisition scripts to full publication traversal, durable resume, and reconciliation against retained source inventories. It runs with standalone Python, Node.js and, for some publishers, ordinary headed Chrome. Codex is not a runtime dependency.

Use the [registry runbook](registry/README.md) for target selection and executable plans. Each source-family runbook explains its installation, source structure, output, tested scope, and limitations:

| Source family | Primary expansion targets | Implementation and runbook |
|---|---:|---|
| Municode | 63 | [Municode](municode/README.md) |
| American Legal | 15 | [American Legal](american-legal/README.md) |
| eCode360 and municipal.codes | 11 | [ICC publishers](ecode/README.md) |
| enCodePlus | 3 | [enCodePlus](encodeplus/README.md) |
| Official HTML, PDF sets, bulk HTML and CodePublishing | 8 | [Official sources](official/README.md) |

The target count is **configuration scope**, not a count of completed full collections. Representative whole-publication runs establish specific adapter capabilities. Previous bounded tests remain in the immutable packages; they are not relabeled as full-publication validation. The registry includes **100 runnable primary configurations and 45 qualified secondary configurations**, with **42 additional source candidates explicitly unsupported** pending configuration or operator work. These are publication entries, not 187 independently validated books.

## Plan, collect, resume, verify

Install the dependencies listed in the selected family runbook, then run these commands from the repository root. Use Python 3.12 for the combined workflow; a graphical Chrome session is needed for headed browser adapters. The tested host was macOS. Windows, Linux, and unattended headless operation have not been established by these tests.

```sh
# Read-only plans: inspect every publication boundary and unsupported source.
python3 collectors/registry/collect.py plan --all
python3 collectors/registry/collect.py plan --target 60

# A fresh output directory. No item limit means full selected-publication scope.
python3 collectors/registry/collect.py collect --target 60 --out /data/local-codes/target-60

# Resume the same publication after a normal interruption.
python3 collectors/registry/collect.py collect --target 60 --out /data/local-codes/target-60 --resume

# Read-only verification from retained sources; no publisher requests.
python3 collectors/registry/collect.py verify --target 60 --out /data/local-codes/target-60
```

Choose a secondary publication with the exact `--publication` identifier returned by the plan. A target's primary publication is not automatically all of that government's law. Unsupported plans identify the missing configuration or operator step; do not substitute a historical source for a current one.

Use fresh output directories outside the sealed evidence packages. The collectors retain source responses, source identifiers, inventory, normalized records, checkpoint state and coverage reports. Keep the whole output directory together. Resume validates the identity, source bindings and cached bytes; it is not an instruction to overwrite mismatched or corrupt evidence. Explicit limits produce incomplete results.

## Image policy

**The collectors do not download separate image assets. All images become the literal `[IMAGE]` in normalized output.** Image-only provisions keep their source ID, heading and placeholder. Deliberate image omissions do not count as missing attachments. Original publisher files may contain embedded images; those source files are retained without separately extracting image binaries. See [IMAGE-POLICY.md](IMAGE-POLICY.md) for the full rule and PDF qualifications.

## Validated publication runs

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

Required nonimage document integrity remains explicit. For example, the standard-library Municode adapter retains PDF attachments as unqualified without a full format parser, so their presence alone cannot close attachment coverage. The source-family runbooks explain supported formats and review requirements.

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

The [full-publication validation release](https://github.com/OliverFlint-98/local-jurisdiction-collection/releases/tag/full-publication-collectors-2026-10-17) contains the sealed source evidence, run receipts, exact executed revisions, and a complete current collector snapshot. The [browsable evidence index](../packages/full-publication-validation-2026-10-17/README.md) links each family. Restore large files with `python3 fetch_evidence.py --package full-publication-validation-2026-10-17`, then run `python3 verify_delivery.py --full`. The [independent integration review](qa/integration-review.json) records relocated replays and the final source-hash comparison.
