# Collection validation follow-up — October 17, 2026

This checkpoint preserves current standalone collector scripts, selected publisher captures, exact executed revisions, normalization outputs, and positive and negative validation evidence. It does not declare all jurisdictions ready or all publications complete.

For operation, use the repository root `collect.py` and `collectors/ops/README.md`. This package's `current-runtime/` preserves the same collector bytes at sealing time; create a fresh runtime and output directory using its runbook. Other `collectors/` and `executed-*` directories preserve historical executed revisions and are provenance, not the default launcher. Historical receipt paths may name the original machine; retained manifests and relative paths identify the shipped inputs.

## Image policy

The current collector contract is exact `[IMAGE]` placeholders and no separate image asset downloads, extraction, rendering or OCR. Preserve IDs, headings, hierarchy, available textual captions and surrounding legal text. Normalized legal records and metadata must omit image payloads and active image markup. Original publisher documents and archives may inherently contain embedded images; their immutable bytes are retained as source evidence. Source-proven image-only pages can have text comparison marked not applicable, without claiming transcription. Ambiguous boundaries between image payload and legal prose fail qualification instead of silently deleting prose.

The policy and applicable regression suites are in `current-runtime/collectors/IMAGE-POLICY.md` and `current-runtime/collectors/qa/`. Earlier sealed evidence is retained unchanged and is not a definition of current acquisition behavior.

## Selected evidence and limits

| Evidence | Scope and remaining qualifications |
|---|---|
| American Legal | Cleveland full 6,140-node body and required PDF checks; form-based code 212-page native structure/table checks. Later metadata fixes include actual-source compatibility receipts. The serial additional-publication queue is not represented as complete. |
| Gridics | Miami 828 records and Cupertino 2,687 records; source-first and list-preservation replay checks. Exact current Miami replay plus separate verify were executed. Publication completeness remains false where source/list-format/dependency gaps or retained access stops remain; the new live acquisition loop is not qualified by offline replay. |
| EncodePlus | Overland Park 6,279-record reference reconciliation, native documents and current image-metadata compatibility evidence. Source-empty and native edition/jurisdiction qualifications remain separate. |
| Official sources | Baltimore 6,994-record fresh capture with independent archive/table checks and explicit heading-only qualifications. Spokane 7,492-record primary text replay includes a selected manifest of 145 raw inputs; this selected proof is not the whole attachment closure. |
| Municode | Wrapped Notes metadata candidate, focused/fault tests and compatibility across retained source checkpoints. The actual retained checkpoints had no nonempty Notes exposure; edge-case coverage is synthetic. |
| Integrated QA | Current runtime, image-policy, native-proof and readiness checks, with earlier failed reports retained. Source binding and proof scope matter; a passing test suite does not imply publication acceptance. |

The active registry covers 130 governments and 225 publication entries: 193 dispatchable configurations, 32 unqualified entries and 131 entries affected by observed workflow stops. These are operational counts, not collected jurisdictions. The strict readiness ledger currently accepts zero whole-jurisdiction entries because its required independent dimensions are not all qualified. See `current-runtime/collectors/qa/FOLLOWUP-READINESS.md` for exact evidence and remaining work.

The `research-unpromoted/` directory contains frozen bounded PDF/table and native-label investigations for later review. These are not production replacements; their older parser baselines must not overwrite the current image-safety fixes.

## Integrity and restoration

`BUNDLE-MANIFEST.json` binds every package file except itself. The root delivery manifest also binds this manifest and the release archive. Large files are restored through the repository's `fetch_evidence.py --package collection-validation-followup-2026-10-17`; then run `verify_delivery.py --full`. Hash verification establishes integrity, not legal completeness. The actual tested platform is macOS; Windows/Linux end-to-end execution is not claimed.
