# What a full-collection result means

A collector can finish a selected publication without finishing an entire jurisdiction. A publication can have all of its HTML text while still lacking attachments or confirmation that the publisher has incorporated the latest ordinances. These dimensions must remain visible in each run's report.

The [image policy](IMAGE-POLICY.md) is mandatory: no separate image acquisition; every image becomes `[IMAGE]` in normalized output. Intentional image omissions do not block completeness.

## Acceptance gates

| Dimension | Evidence required | Conditions that prevent a complete claim |
|---|---|---|
| Publication identity | Expected government, state, publication ID/title, source route and captured edition/job/version | Wrong government/publication; unresolved migration; stale cache from another source |
| Inventory | Source-backed enumeration of the entire selected publication, including container-owned content and explicit exclusions | Sample subtree; request limit; unexplained empty inventory; pagination left open; unknown node type; ambiguous scope |
| Text coverage | Every required source unit dispositioned once, raw response tied to exact source ID, nonempty expected body or documented source-backed exemption, deterministic parse | Missing/extra/duplicate IDs; headings-only records; swallowed errors; lost parent-only legal text; duplicated descendant bodies |
| Images and attachments | Every image represented by `[IMAGE]` with an explicit policy omission; required nonimage documents acquired and hash checked or reported unresolved | Lost image-only source nodes; missing placeholders; image downloads contrary to policy; unfetched required nonimage attachments |
| Structural fidelity | Preserved source HTML plus tested table/list/note/link handling; extraction limitations reported by format | Flattened or missing legal tables; missing image placeholders; PDF page extraction presented as section-level equivalence |
| Source consistency | Inventory/publication identity checked again at completion against the start snapshot, or an immutable publication version fully pinned | Edition drift; changed inventory; unpinned publication with no closing check |
| Resume integrity | Checkpoint identity and inventory hashes match; all cached raw/parsed artifacts checked before reuse; failures remain visible | Trusting an old success flag; skipped items after interruption; mixed editions; changed or missing cache files |
| Jurisdiction coverage | Explicit requested publication set, known separate families and uncodified/amendment scope reconciled | Uncollected charter/zoning/development code or required external family; primary code alone labeled whole jurisdiction |

A native publisher file can be completely downloaded even when its edition is older than the live code. Complete PDF page extraction means all pages were processed; it does not establish complete legal-section segmentation, table fidelity, OCR fidelity, or incorporated-image interpretation. Likewise, every internal link need not be another required legal provision; classify references and preserve unresolved/externally incorporated material instead of guessing.

## Independent verification

The offline verifier should reconstruct the expected set from retained source inventory evidence and compare it to retained acquisition and parsed output. A `complete: true` field written by the collector is not itself evidence. Coverage reports should include denominators, missing and extra IDs, exclusions with reasons, failed units, source/edition identifiers and asset outcomes, so a reviewer can inspect the reconciliation.

Required negative tests remove or duplicate a source unit, corrupt a retained file, change publication/edition identity, and interrupt a run before completion. A corrupted or incomplete collection must fail the appropriate gate. Resume tests compare resumed output to an uninterrupted expected output and must not hide previous failures. Any `--limit` or similar diagnostic mode must be unmistakably partial.

Testing has separate levels: final-code live transport smoke; complete live collection of a named publication; full retained-evidence replay; and synthetic/fault-injection tests. Reports must state which levels passed. Passing an adapter's representative publication does not retroactively make all targets using that adapter full-live-validated.

## Operational use

Select the exact publication set before launching production collection. Use a fresh output directory or the collector's explicit resume mode. Keep publishers' shared rate gates across parallel runs. Honor stops and Retry-After; an interrupted collector can preserve useful progress without being marked complete. Verify output before ingestion and retain the raw sources, inventory, edition evidence and coverage report together.

Refer to each family's README for its actual implementation, commands, validation evidence and limits. This document defines acceptance criteria; it does not assert that every format or target meets every gate.
