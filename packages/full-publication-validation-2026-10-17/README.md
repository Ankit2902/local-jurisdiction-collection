# Full-publication collector validation — 17 October 2026

This package contains the evidence behind the standalone full-publication collector handoff for 100 additional local jurisdictions. It includes 100 runnable primary configurations and 45 qualified secondary configurations. Forty-two additional candidates remain explicitly unsupported. Configuration coverage is not completed-corpus coverage.

The current implementation is preserved in [collector-source/collectors](collector-source/collectors/README.md). The authoritative repository implementation and operating runbooks are [on GitHub](https://github.com/OliverFlint-98/local-jurisdiction-collection/tree/main/collectors). Historical executed revisions are retained inside individual runs; they are not silently replaced by the current source snapshot.

## Image rule

All current collectors omit separate image downloads and replace images with the literal `[IMAGE]` in normalized text and HTML. Source identifiers and headings remain, including image-only provisions. Original publisher HTML, PDF and ZIP files may contain embedded images and are preserved as source evidence. No separate image extraction is performed. Required nonimage documents remain subject to completeness checks. Historical attempts before the policy update remain unchanged and are distinguished from final selected proofs.

## Evidence by family

| Family | Evidence and runbook | Representative result |
|---|---|---|
| Municode | [README](municode/README.md) | Henderson: 2,123 inventory IDs, 2,122 owned records, one justified empty landing; selected publication reconciled with matching start/end edition |
| American Legal | [README](american-legal/README.md) | San Diego County ordinance index: 30/30 nodes, 97 blocks; 1,940 linked ordinance PDFs unacquired. Cleveland Form-Based Code: whole native PDF and 212 page text layers |
| eCode360 / municipal.codes | [Current runbook](collector-source/collectors/ecode/README.md), [validation summary](ecode/validation-summary.json) | Albany: 3,253/3,253 nodes resolved, 3,006 records; six required documents and closing check incomplete after 403. Phoenix Charter: 81/279 nodes resolved, stopped after 429 |
| enCodePlus | [Implementation runbook](encodeplus/IMPLEMENTATION-README.md) | Lincoln Charter: 188/188 nodes. Access Management Policy: 14/14 nodes and whole 17-page native PDF, with one unresolved external required PDF |
| Official sources | [Runbook](official/implementation/RUNBOOK.md), [validation summary](official/validation-summary.json) | Worcester 659 pages; Milwaukee Volume 2 624 pages; Baltimore 6,989 owned records with 12 unresolved required references; other explicitly bounded checks |
| Independent QA | [Current QA runbook](collector-source/collectors/qa/README.md), [integration review](integration-review/integration-review.json) | 14 network-disabled commands / 126 cases passed. All 17 selected terminal image audits passed with zero separate image binaries |

Every family summary records acquisition vs replay, source revision, exact counts, failures and qualifications. A verifier can successfully confirm an accurately incomplete result. In particular, eCode360/municipal.codes terminal proofs return exit 2 with `verified=true` and `complete=false`; those are expected outcomes. Publisher stops are retained; they must not be cleared automatically or worked around.

Only Henderson is a primary target with a completed full live text-and-attachment proof. Lincoln Charter is a separate secondary publication with full observed source coverage; a global official legal edition is not asserted. PDF file and physical-page completion do not establish section, table, OCR or legal-semantic completeness. No whole jurisdiction is marked complete.

## Portable replay

Create a fresh Python 3.12 environment and install `collector-source/collectors/qa/requirements.txt`. From `collector-source`, run:

```sh
python -B collectors/qa/run_offline.py --out /path/to/new-qa-results
python -B collectors/registry/verify.py
```

Follow each family runbook for its full raw-source verifier and expected exit status. Run tests in a working copy or write outputs outside this sealed package. The collector snapshot runs without the historical packages; references to those packages in provenance fields and some documentation describe repository history. For current live collection, use fresh output paths and the standalone runtime dependencies in the selected family runbook. Ordinary headed Chrome requires a graphical session; macOS was tested.

## Integrity

`PACKAGE-MANIFEST.json` records every included file's size and SHA-256. Family manifests and executed-source snapshots provide more detailed bindings. The outer ZIP has a SHA-256 sidecar and is published as a GitHub release asset. The repository's delivery manifest and `fetch_evidence.py` restore large evidence files without changing sealed bytes. Virtual environments, installed runtimes, browser profiles and caches are excluded.
