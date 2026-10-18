# Collection startup, corpus export and image-policy validation

This checkpoint delivers reviewed startup recovery, portable publication corpus exporters and source-specific native collection improvements. The active scripts are under [`collectors/`](../../collectors/); frozen candidate snapshots here identify the exact bytes executed by each proof. Historical results keep their original qualifications.

**All normalized images are exact `[IMAGE]` placeholders.** No separate image requests, assets, extraction, decoding, rendering or OCR are allowed. Immutable publisher HTML/PDF/DOCX/archive originals may intrinsically embed images. Tests distinguish those original documents from separately collected image assets and reject active image markup or payloads in normalized text and recursive metadata. MIME classification strips surrounding whitespace and normalizes case. Ordinary PDF links, captions, surrounding prose and inert omission provenance remain available.

## Technical-team entry points

- [Common collector launcher and operational runbook](../../collectors/README.md).
- [Flagstaff and original-source acquisition, resume and verification](../../collectors/originals/README.md).
- [Portable fulltext/TOC corpus export](../../collectors/corpus_package/README.md): three explicit HTML readers, standard-library packaging, owned resume and self-contained verification after relocation.
- [enCodePlus native collection](../../collectors/encodeplus/README.md): automatic source-specific Infrastructure integration through the normal native operation.
- [Image policy](../../collectors/IMAGE-POLICY.md) and [independent QA commands](../../collectors/qa/README.md).

## Corpus exports and independent validation

The final composed writer was exercised against three retained whole-publication inputs:

| Selected publication | Records | Independent source nodes | Source features retained |
|---|---:|---:|---|
| Flagstaff City Code and Charter | 2,661 | 2,661, including three explicit body-only units | 377 tables, 27,167 cells, 800 note metadata entries, 882 `[IMAGE]` markers |
| Henderson Municode publication | 2,122 | 2,123, including one source-proven structural landing | 60 tables and 10 `[IMAGE]` markers |
| Lincoln Charter | 188 | 188 | 17 lists, exclusive parent-owned bodies and observed source order |

All 16 corpus fields, canonical HTML, JSON/CSV/TOC agreement, source parents and dispositions were checked. Flagstaff's final 15 generated artifacts and 544 original input files remain byte-identical to the independently reviewed fidelity base. The final composition adds two readers and strict proof handling without changing Flagstaff content. Source hierarchy and locators are exported only with reader-specific witnesses. Unsupported populated separate notes, including notes on excluded structural landings, cause refusal rather than omission.

The writer is offline. A separate portable helper runs the explicitly selected Municode/enCodePlus family verifier and binds input, collector code, Python/dependency identities and reports. Caller-assigned publication IDs are explicitly not registry crosswalks. Default report selection uses a hash-bound relative path; historical absolute log paths are refused unless the caller supplies the exact report explicitly. Relocation checks exercise the shipped entry point without access to original source locations, network or image APIs.

Verified serialization is distinct from publication acceptance. The tested packages intentionally return exit 2 with `package_verified:true` and `complete:false` where source, dependency, legal edition or jurisdiction qualifications remain unresolved.

Selected evidence:

- `corpus/flagstaff-reviewed-base` and `corpus/flagstaff-independent-review`: complete fidelity base, tests and independent source/field review.
- `corpus/mime-guard` and `corpus/mime-independent-review`: narrow HTML/metadata image MIME whitespace correction and negative/PDF controls.
- `corpus/flagstaff-composed-current` and `corpus/flagstaff-composed-independent-review`: final eight-module runtime and whole-source relocation bridge.
- `corpus/municode-encodeplus-final`: final actual Henderson and Charter packages, portable proof helper, exact promotion plan and operator commands. Its final source freeze is `ecbd57b7…`; the source-only history preserves earlier findings without duplicating full output trees.
- `corpus/portable-verifier-review` and `corpus/reader-independent-review`: explicit-runtime proof helper, safe report selection and actual Municode/enCodePlus semantic review. Each review states its exact revision and bounded scope.

The final current acquisition-to-export proof is `corpus/flagstaff-current-live-export`, independently reviewed in `corpus/current-live-independent-review`. It runs the promoted writer directly on the newly completed live collection and exact current common/family reports, without proof augmentation, reacquisition or source normalization. All 558 current source files, 2,661 records, source parents/dispositions and 882 placeholders are preserved. The primary publication's current acceptance/coverage remains true; the corpus package retains false whole-jurisdiction, dependency and independent-final-review gates, returning verified serialization with exit 2. This current package is separate from the historical fidelity base and composition bridge above.

Portable current end-to-end evidence verification:

```sh
python3 -B corpus/flagstaff-current-live-export/verify_packet.py
```

## Infrastructure normal native workflow

The exact 62-page Infrastructure PDF now yields 172 source-printed units through normal native collection and verification: one cover, one contents unit and 170 other printed-heading units. These are not asserted to be 172 legal provisions. All 18,662 word IDs are assigned once; 1,776 source blocks, 142 page controls and 40 cross-page units are reconciled. Five source-stroked grids supply 79 canonical cells. Nine false grid detections become source-order prose while their original diagnostics remain available.

The mixed export contains 828 records. All 656 unrelated records and all 201 source image positions remain intact. Five Infrastructure image IDs use explicit namespace aliases preserving original IDs; the other 196 IDs are unchanged. All 616 old detector cells, including 44 failed comparisons, remain diagnostic evidence. Nested-list semantics, full legal reading order, required external dependencies, edition and publication acceptance remain unqualified.

`infrastructure/native-default` contains the final default-workflow proof and complete 533-file family snapshot. Only authentic retained transport was substituted; the native parser and strict verifier were executed. The full family suite passed 130 tests and the focused suite passed 11. `infrastructure/native-independent-review` independently checks the source mapping and final outputs without rerunning a full native parse. Earlier `full62-operational` and its review preserve the preceding page-oriented operational proof.

Portable verification of the compact terminal proof:

```sh
python3 -B infrastructure/native-default/verify_compact.py
python3 -B corpus/flagstaff-composed-current/verify_bridge.py
```

Run these commands from this checkpoint directory. These commands verify retained evidence and do not perform new publisher acquisition.

## Startup recovery and other terminal evidence

`originals/initialization-reviewed-v4` and `originals/initialization-independent-review` retain the reviewed early-inventory recovery implementation and 18 focused tests. A durable initialization marker owns the operation before native inventory finishes; resume preserves the interrupted generation, verifies exact code/source ownership, and honors retained access refusals. An incomplete native inventory can require a fresh native generation. This does not imply zero-refetch recovery at every boundary.

`originals/current-live-recovery` is the terminal actual current ordinary-Chrome proof: real SIGINT after one initial native response, same-command resume, all 361 documents and 421 source artifacts acquired, final closing controls successful, then a separate current common read-only verification accepted the primary publication. Its 558-file collection retains the interrupted eight-file inventory generation. All 455 raw/native bodies and nine normalized streams passed image audits, with 882 exact placeholders and no separate image bodies. The three literal fragment defects remain explicit. Primary operational acceptance is true; whole-jurisdiction/external adopted-law closure is false, native-capture acceptance is false, and edition completeness is null. Employee Handbook remains outside the selected scope. This actual current proof is separate from the earlier retained-source export base.

`official/milwaukee-original-terminal` records the completed exact historical parser verification: six native files, 2,300 pages, 1,171 detected tables and seven image placeholders, with all 60 source files unchanged. It retains 74 failed word-conservation results and 3,745 cell mismatches; legal semantics and manual-review gates remain unresolved. Its exact historical verifier was not instrumented with the newer image-call tripwires, and this packet does not claim otherwise. Full native outputs remain at the recorded original location; the compact packet's receipt-only mode does not substitute for checking those source files.

Other ongoing publisher jobs and untested jurisdictions remain separate. A completed sample, raw acquisition, native file, unit mapping or export package never establishes all-jurisdiction readiness. Publisher refusal gates are preserved.

## Integrity and scope

`COPY-RECEIPTS.json` records source manifest hashes and every copied file. `BUNDLE-MANIFEST.json` seals this selected checkpoint. Omitted transient or duplicate output trees receive no replay credit; each compact proof describes its selection. Earlier sealed packets are unchanged. The root delivery manifest and `verify_delivery.py --full` cover the complete repository delivery.

The current readiness ledger retains the original 130 governments and 225 known publication entries. Broader source, access, native semantic, dependency, edition and jurisdiction completeness gaps remain explicit. Database loading is outside this handoff.

Release verification: 45 integrated check programs and 415 unittest cases passed with unchanged source/runtime; 19 additional actual reader cases passed. All selected checkpoint evidence passed separate-image signature/MIME audits, including the final current-live export and its independent review. Exact root reports are in [the checkpoint QA receipts](../../collectors/qa/followup-proof-receipts/startup-and-corpus-2026-10-18/README.md).
