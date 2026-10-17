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

The target count is **configuration scope**, not a count of completed full collections. Representative whole-publication runs establish specific adapter capabilities. Previous bounded tests remain in the immutable packages; they are not relabeled as full-publication validation. Secondary publications have separate entries where an exact source and usable configuration are available.

## Plan, collect, resume, verify

Install the dependencies listed in the selected family runbook, then run these commands from the repository root. Use Python 3.12 for the combined workflow; a graphical Chrome session is needed for headed browser adapters. The tested host was macOS. Windows, Linux, and unattended headless operation have not been established by these tests.

```sh
# Read-only plans: inspect every publication boundary and unsupported source.
python3 collectors/registry/collect.py plan --all
python3 collectors/registry/collect.py plan --target 70

# A fresh output directory. No item limit means full selected-publication scope.
python3 collectors/registry/collect.py collect --target 70 --out /data/local-codes/target-70

# Resume the same publication after a normal interruption.
python3 collectors/registry/collect.py collect --target 70 --out /data/local-codes/target-70 --resume

# Read-only verification from retained sources; no publisher requests.
python3 collectors/registry/collect.py verify --target 70 --out /data/local-codes/target-70
```

Choose a secondary publication with the exact `--publication` identifier returned by the plan. A target's primary publication is not automatically all of that government's law. Unsupported plans identify the missing configuration or operator step; do not substitute a historical source for a current one.

Use fresh output directories outside the sealed evidence packages. The collectors retain source responses, source identifiers, inventory, normalized records, checkpoint state and coverage reports. Keep the whole output directory together. Resume validates the identity, source bindings and cached bytes; it is not an instruction to overwrite mismatched or corrupt evidence. Explicit limits produce incomplete results.

## Image policy

**The collectors do not download separate image assets. All images become the literal `[IMAGE]` in normalized output.** Image-only provisions keep their source ID, heading and placeholder. Deliberate image omissions do not count as missing attachments. Original publisher files may contain embedded images; those source files are retained without separately extracting image binaries. See [IMAGE-POLICY.md](IMAGE-POLICY.md) for the full rule and PDF qualifications.

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
