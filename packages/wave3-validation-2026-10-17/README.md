# Wave 3: validated methods for 43 additional local jurisdictions

This handoff covers recommendations **58–100**, the final 43 jurisdictions in the 100-target expansion inventory. Sol agents tested live acquisition, normalization and publisher downloads on October 17, 2026. It follows the completed waves 1 and 2 package for recommendations 1–57. No database changes were made.

The final bounded-sample outcomes are **43 `standalone_e2e_pass`**. Separate publisher-download outcomes are **31 `passed`; 8 `partial`; 4 `unavailable`**. **0 complete jurisdiction corpora are claimed.** A standalone pass means the documented sample was acquired and parsed without a Codex runtime. It does not mean a complete publication was traversed, or that every incorporated document and amendment was captured.

## Find a jurisdiction and run its tested method

Start with [JURISDICTIONS.md](JURISDICTIONS.md), then the linked group README. [results43.json](results43.json) contains the exact tested scope, commands, source route, record counts, checks, evidence paths, limitations and next action. [scope43.json](scope43.json) preserves the original discovery inventory; current routes and source families in the later validation results take precedence when publishers have changed.

| Group and runbook | Targets | Sample outcomes |
|---|---:|---|
| [municode-cities](municode-cities/README.md) | 10 | 10 standalone_e2e_pass |
| [municode-counties](municode-counties/README.md) | 12 | 12 standalone_e2e_pass |
| [american-legal](american-legal/README.md) | 6 | 6 standalone_e2e_pass |
| [icc-ecode](icc-ecode/README.md) | 6 | 6 standalone_e2e_pass |
| [official-sources](official-sources/README.md) | 7 | 7 standalone_e2e_pass |
| [encodeplus](encodeplus/README.md) | 2 | 2 standalone_e2e_pass |

Follow each group’s installation instructions and use a **fresh output directory** for live runs. Historical command receipts preserve the original acquisition paths; the documented portable commands resolve resources within the package. Exact executed script snapshots are retained because some source discoveries and safety fixes happened during validation. The group README identifies the final portable entry points and fresh-run proof.

## Source-driven implementation guidance

- **Municode:** use the tested ordinary headed Chrome/Playwright public workflow, pin client, product and publication job IDs, inventory the current publication tree, and bind every response to the requested node. Direct HTTP returned publisher challenges on this run and was stopped. One unassisted normal-page availability check established the browser route. The final collector gates publisher requests and PDF redirect hops across processes and persists challenge/rate-limit stops. Keep the shared gate across all concurrently running Municode collectors. Supplemental tests exercise operative fee/parking tables; consult their precise coverage. Reno’s current primary publication is the Administrative Code, with a separate Land Development Code; the assumed Code of Ordinances route was rejected and its failure preserved.
- **American Legal:** use the current publication navigation and rendered operative-node extraction, then the actual publisher export flow. Cincinnati and Fairfax County moved to Municode for the main code, so the group’s source inventory and wrappers include those routes. Fairfax zoning is a separate enCodePlus publication.
- **eCode360 and municipal.codes:** use the tested headed-browser node workflow and native section downloads. Buffalo supplies substantial table-bearing evidence; Albany includes article-owned history records. Tacoma’s routing now points to eCode360. Charter, zoning and development publications remain separately inventoried.
- **enCodePlus:** the public server-rendered document route supplies operative HTML. The viewer shell alone is not legal content. Native export requires following the observed HTML status page and polling/file-token flow. Lincoln and Overland Park have tested table-bearing samples and genuine section PDFs; Savannah uses its current enCodePlus publication.
- **Official HTML and PDF sources:** follow the actual official index and visible document/download routes. Some sites require an ordinary browser to reach a native PDF. Preserve document dates and attachment boundaries. PDF page records are not legal sections, and image or table layout can require a different extraction method.

All tested workflows are standalone Python and/or Node with ordinary Chrome where required; the group requirements and lock files record exact dependencies. The tested desktop platform was macOS. Headless, Linux and Windows portability were not established by these tests. Local environments, browser installations, profiles and caches are excluded from the handoff.

## Qualification boundaries the technical team must preserve

Publisher download transport, PDF parseability, sampled-body fidelity and edition currency are separate checks. A PDF can download successfully and still be older than the live code. The row-level `publisher_download` objects and native QA record those distinctions. Cincinnati and Orlando have demonstrated PDF edition mismatches. Allegheny’s inspected code states legislation only through June 4, 2024. These examples are not an exhaustive list of currency qualifications: read each row and its source inventory before selecting a production source.

Lincoln’s 547 TOC depth anomalies leave hierarchy completeness unproved even though its flat IDs and sampled body breadcrumbs are retained. Overland Park’s image-only use-table candidate is negative evidence. Clark County’s supplemental PDF table extraction loses grid/cell fidelity; original PDF bytes are preserved and that structured-table result is not accepted. Official Arlington documents carry their own chapter dates and freshness qualifications. Images, maps, incorporated model codes, attachments, external manuals, uncodified ordinances and separate charter/zoning/development families remain explicit scope work.

The supplied acquisition loops are **bounded validators**, often selecting a few provisions. To turn them into production full collectors, implement the per-group traversal instructions, disposition every inventoried node, distinguish container-owned text from descendant content, handle every linked attachment in scope, preserve source semantics, reconcile IDs/counts and verify publication identity before and after the full run. Do not extrapolate a sampled-table pass or a PDF container check into whole-code fidelity. No full-corpus ingestion was run in this task.

Record counts use different units across groups: operative HTML provisions, article histories, attachments and PDF pages. Do not sum them as unique legal-section coverage. Native exports frequently overlap live HTML samples and must not be counted as additional unique provisions.

## Independent verification and retained evidence

The root integrator copied each completed group to a separate temporary directory and ran its read-only offline verifier using the documented tested dependencies. The reports in [qa/](qa/) retain commands, exit codes and outputs. This checks relocation, raw-response hashes, deterministic parsing, result paths and each group’s substantive source checks without repeating live requests or changing retained evidence. The independent Municode review and its final dispositions are also retained there. The small Savannah native-export assist is preserved separately and within the official-source group; those copies add no new jurisdiction or unique record.

From the package root, run:

```sh
python3 verify_handoff.py
```

This standard-library check verifies the exact 43-target scope, required result fields, evidence paths and SHA-256 manifest. It is an integrity check; it does not replace the group-level semantic verifiers. The group READMEs give their network-free replay commands. Tests that write output should run only in temporary or new directories.

[MANIFEST.json](MANIFEST.json) seals the delivered files; [integrity-verification.json](integrity-verification.json) records the final root check. The sibling ZIP preserves these bytes and has a SHA-256 sidecar. On GitHub, ordinary files are browsable in the repository and large evidence plus the full ZIP are available through the repository release. The root `fetch_evidence.py` restores release-backed files and verifies their hashes before `verify_delivery.py --full` checks the complete delivery.
