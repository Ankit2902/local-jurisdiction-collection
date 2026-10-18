# Cleveland retained whole-code HTML corpus candidate, revision 2

This isolated, stdlib-only reader projects the complete retained Cleveland Code of Ordinances HTML publication into the shared 16-field corpus contract. It has not been promoted into production. The original acquisition and source normalization remain immutable; this is an offline export and current-source verification of that retained acquisition, not a new live capture or a new edition check.

The source is `cleveland-final-v6`, publisher version `2026 S-28`, UUID `f0e7839e-f7cd-45ed-a9a9-a52efe04fd04`, current-through text September 28, 2026. Original native HTML SHA256 is `922b8f2b798ed607e4374d0b99cc49ed9f4be646ff6d811a7b04bcf9ad4334e5`. The portable package includes every one of the 988 input files and the exact source-verification proof/report. The source's original executed-v3 and later normalization lineage remain included unchanged.

The new reader contract is `american-legal-native-html-publication-v1`. Qualification here covers this exact full Cleveland publication. It refuses PDF/page/limited acquisitions, missing or changed start/end inventories, unknown source kinds and unconserved/reordered native blocks. It does not automatically qualify all American Legal configurations.

The source's old seven-column CSV did not satisfy the corpus contract. This candidate writes 6,140 canonical rows: 6,135 exact source-owned normalized HTML bodies plus five source-explicit passthrough TOC containers represented by their own escaped headings. It reconstructs 459 raw TOC branches independently in source preorder, checks both inventories and the pinned native job, and reconciles every one of 43,676 native rich-block IDs exactly once. The original IR uses breadth-first order; that original line ordinal remains in provenance while the canonical corpus uses independently agreeing native-forward/TOC-preorder order. Source tables, links, notes, table spans, ownership and IDs remain in the exact HTML and rich provenance.

Hierarchy fields are literal printed roles on exact source-proven ancestor chains. No level is generated from numeric node IDs or tree depth. In 1,439 rows, multiple nested Part headings cannot be represented by one scalar `part`; that scalar remains blank and every exact heading/ID plus conflict is retained in the sidecar. This is a documented 16-field representational limit, not a loss of the full ancestry. There are 5,666 source-literal section numbers. No generated legal citations or corrected source text are added.

There are 20 additional asset inventory nodes: 15 intentional image references, four required zero-text-glyph PDFs with source-proven image-policy N/A, and one retained text/table PDF without qualified canonical legal-unit segmentation. No PDF page is invented as a provision. Its original five-page diagnostics and required bytes remain portable evidence. That one canonical nonimage-source gap remains `unresolved`. The original producer coverage is copied byte-for-byte; its true HTML/publication flags are not relabelled into missing shared jurisdiction/dependency/final-review gates. Package verification succeeds with expected exit **2**, `package_verified:true`, `complete:false`. This result is not strict jurisdiction readiness.

Images are never separately acquired, extracted, decoded, rendered or OCR'd. Exact `[IMAGE]` remains in the normalized HTML (15 positions), and the original PDF diagnostics retain their 18 markers. Image references are explicitly disposed without binary files; original embedded source evidence is allowed. Current full source verification, the pure all-row consumer, compact fault tests and relocated shipped verifier record zero forbidden network/image operations. The source verification guarded PDF image streams as well as all known image APIs. The portable writer and reader need only Python's standard library; the source-verification helper requires the explicitly selected collector environment. The exact tested shared environment includes pdfplumber 0.11.8 and pypdfium2 5.14.0 as guard dependencies in addition to the captured AL lock. Installing only the AL lock is not claimed to install the shared helper environment.

## Commands

Run from this packet directory with the existing common collection Python for source verification. `INPUT` and `COLLECTOR` may point to the portable package's retained input and this packet's `verification-source`. A fresh output is mandatory.

```sh
PY='/absolute/path/to/.collection-runtime/venv/bin/python'
INPUT="$PWD/package/evidence/input"
COLLECTOR="$PWD/verification-source"
"$PY" -B candidate/verify_input.py --reader american-legal-native-html-publication-v1 --input "$INPUT" --collector-root "$COLLECTOR" --publication-id 59-primary --out "$PWD/fresh-verification"
"$PY" -S candidate/package.py package --input "$INPUT" --proof "$PWD/fresh-verification/read-only-proof.json" --reader american-legal-native-html-publication-v1 --out "$PWD/fresh-package"
```

The second command's expected result is exit 2, not 0. Source verification does not strengthen scope or edition acceptance. The source-verification proof uses a caller-assigned safe namespace; registry mapping remains explicitly unverified. The tested actual portable adapter invocation is recorded under `portable-verification/`; the earlier fixed retained harness and its separate proof remain for executed-source lineage.

The already shipped package can be copied anywhere and checked with ordinary Python (no `-B`, no dependencies or original project paths required):

```sh
python3 -S package/packager-source/package.py verify --out package
python3 -S audit_actual.py
python3 -B -m unittest discover -s candidate -p test_american_legal_html.py -v
python3 -B -m unittest discover -s candidate -p test_verify_input_interface.py -v
```

`test_relocation.py` copies the complete package to an outside temporary path, runs the shipped command under outside-read/write/network/process/image/third-party-import tripwires, and compares all 1,016 artifact hashes before and after. It deliberately writes a new `relocation.json` evidence receipt if rerun; preserve the frozen receipt first. The packaged verifier itself is read-only. `audit_actual.py` independently walks original raw TOC branches, raw native block sequence, every exported field, all HTML/notes/links/table metadata, asset dispositions, all BOM/CSV/JSON/TOC values and the unchanged original flags; it similarly writes its own audit receipt if rerun.

Compact tests cover missing middle branch with roots present, changed closing inventory, missing/duplicate/reordered/unowned native blocks, missing IR/table, wrong native scope/edition, limited/PDF modes, intentional image-only policy, typed opaque image payload/active image link refusal without decoder/network calls, literal Unicode JSONL separators, repeated hierarchy roles, source-only passthrough, explicit unresolved nonimage document and injected package interruption/resume/corrupt inventory. All 32 pass; the seven preexisting MC/EP interface tests also pass against the AL-extended helper.

## Integration delta

Only the new `american_legal_html.py`, its compact test, and the AL-specific changes to `verify_input.py` should be promoted directly. Add its import/reader entry and one MODULES entry to the current composed production registry/writer. `integration.patch` records those deltas against the pre-readiness shared baseline. Do not overwrite current shared `common.py`, `flagstaff.py`, `readiness.py` or other families with this candidate's older copied writer snapshot. Root owns composition and the resulting final fingerprint/actual package rerun.

The historical initial `toc-destination` assumption failed because that CSS class marks only 5,702 of 6,135 headers. Its exact source/error and the corrected all-rich-ID/independent-TOC witness remain in the immutable sibling `cleveland-html-corpus-candidate-v1/attempts/native-order-assumption/`. No failed attempt is relabelled a successful full export.

The original serial AL queue is independently stopped after Sacramento's required external Legislature URL returned HTTP403 with `cf-mitigated: challenge` at 02:56:17 UTC on October 18. There are five terminal entries of 14 planned. Original queue/child PIDs were absent at 03:04:51, but the persistent operator-review stop and original `finished_at:null` are authoritative. There is no Dallas safe acquisition slot, no retry, and no publisher work in this candidate.

## Revision 2 safety closure

The first frozen packet is preserved, manifest `c1b0c2b4354248e55ee95780f8b97e13c5dc284fe0491c4afc51d5ee574ea5f8`. Independent peer review found two real synthetic refusal gaps: a declared multi-page required PDF could be policy-excluded from only one zero-glyph row, and an orphan required asset could be accepted without an HTML owner. This revision requires nonempty independently owned HTML references for every required nonimage asset. Policy N/A now additionally requires retained bytes with the exact verified SHA, qualified native PDF validation, strictly positive native page count matching normalized/document/related-row counts, exact unique page-1-through-n IDs, source SHA-derived attachment owner, and matching original source ownership/image policy for every page. The existing zero-glyph/marker-only guards still apply to every page. Inconsistent page evidence stays unresolved; it is not silently excluded. Seven refusal cases and two two-page controls extend the compact suite to 32 tests.

No source normalization or native PDF parse was repeated: the unchanged actual source already satisfies every new guard. The new source was exercised by generating a fresh entire package and re-running the all-row consumer and relocated shipped verifier. `actual-asset-closure.json` binds all five required PDFs and every page ID to actual bytes/source owners. `v1-v2-differential.json` proves all 988 original source inputs, both proofs and all 15 generated corpus/provenance/disposition/coverage artifacts are byte-identical; only the reader source snapshot and its two manifest/state fingerprints differ. This zero-exposure proof is not a new acquisition claim. The helper and previous seven interface tests are unchanged from revision 1. Root must apply the current revision-2 reader rather than the original revision-1 reader when composing the production writer.
