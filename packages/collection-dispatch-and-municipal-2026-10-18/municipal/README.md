# municipal.codes canonical HTML handoff — retained incomplete Phoenix Charter

This standalone reader uses municipal.codes full `contents-toc` inventory and typed `article` ownership, not eCode GUID conventions. It is capable of projecting a whole publication when a qualified complete input exists. The only real input qualified here is incomplete: **279 inventory nodes, 81 resolved dispositions (73 owned bodies and 8 structural), and 198 explicitly missing nodes**. It retains the original HTTP429 stop and missing closing sweep. It makes no publisher requests and never resets gates.

The selected opening source says “The Phoenix City Charter is current through the November 6, 2018 election.” This is a literal source currency label, not a statement of present legal currency. The requested state is AZ; source state verification remains false. The reader does not certify other Phoenix publications or external adopted law.

All 73 canonical own bodies are emitted with exactly 16 corpus fields. Every one of the 279 independently inventoried source nodes gets a disposition, including all 198 missing/unacquired nodes as `unresolved`. Source order comes from the 277 literal full-contents anchors, with source-defined nesting, plus the opening root's typed preface; the retained ID-sorted IR ordinal is kept separately as provenance. Parent relationships, source headings, tables, notes, body links, image-reference metadata and raw hashes are retained. No citation/ID-depth hierarchy is generated. An incomplete source is never promoted by serialization.

An independent audit of all 16 original responses found all 73 acquired rich and canonical bodies faithful, with 235 IDs, 32 body links, 3 notes, 159 subsection elements, and no unknown legal text outside the profiled owners. It also found three heading footnote callouts omitted by the old IR's heading removal. The new ordinary `record-provenance.jsonl` exposes the exact source heading HTML, raw/normalized heading hashes, literal/resolved callout URLs, and uniquely owned note target evidence. Notes are not appended again to canonical bodies. The independent source audit and order witnesses are included in `independent-source-audit/`.

**The real sample has zero tables and zero images.** These dimensions are tested separately with an explicitly synthetic complete publication using the actual collector against an in-memory backend, followed by the actual standard verifier. It includes an image-only own body, an image in a colspan table cell, and a header footnote. Bounded additional tests cover header picture/CSS background images and captions, opaque-MIME image anchors, multiline image metadata refusal and LF-only source slicing with U+2028/RS/CR. All images become literal `[IMAGE]`; no separate image bytes are acquired, decoded, rendered, extracted or OCRed. Header source hashes preserve the original witness without exporting image payloads in normalized provenance.

The actual selected historical standard engine verifies all 73 retained input files under network/process/base64/Pillow tripwires. Its proof is reconstruction qualification only: `verified:true`, `complete:false`, and the corresponding standard completeness exit is 2. The real export has `serialization_complete:true` and `package_verified:true`, while `complete:false`, `selected_publication_ready:false`, and `downstream_ready:false` remain explicit. The synthetic complete control is not municipal-law evidence and does not grant independent legal or jurisdiction readiness.

The portable writer and verifier are Python standard-library only, including the raw source-order reader. The separate raw verification helper/QA additionally require the exact selected collector dependencies and `collectors/corpus_package/requirements-verification.txt` (Pillow, beautifulsoup4, requests and pypdf preflight before any output directory is made). Use ordinary Python 3.12 in that environment; only macOS arm64 is tested. POSIX fcntl locking is used; Windows is unqualified. No Codex service or browser is required for this offline handoff.

From this directory, using an ordinary configured interpreter:

```sh
MC_PY=python3

# Inspect/verify the self-contained real incomplete export, no third-party imports.
"$MC_PY" -B -S package-v3/packager-source/package.py verify --out package-v3
# Expected exit2, package_verified:true, complete:false.

# Recreate an ACTUAL standard source-verification receipt in a fresh directory.
"$MC_PY" -B source/verify_municipal_input.py \
  --input package-v3/evidence/input \
  --collector-root package-v3/evidence/input/executed-source \
  --publication-id phoenix-charter-municipal-codes --out fresh/source-proof
# Helper exit0 means reconstruction verified; publication_complete:false.

"$MC_PY" -B -S source/package.py package \
  --input package-v3/evidence/input --proof fresh/source-proof/read-only-proof.json \
  --family-verification fresh/source-proof/family-verification.json \
  --reader municipal-codes-html-publication-v1 --out fresh/package
# Expected exit2. Fresh disjoint directories are mandatory; no source overwrite.

"$MC_PY" -B source/test_municipal_codes_html.py \
  package-v3/evidence/input actual-standard-proof/read-only-proof.json \
  synthetic-controls-v2 synthetic-controls-proof-v2/read-only-proof.json
# 22 tests, all network/process/pixel operations guarded.
"$MC_PY" -B source/test_municipal_helper_preflight.py \
  --input package-v3/evidence/input --helper source/verify_municipal_input.py
# 6 tests including missing dependency -> no output, no selected engine import.
```

Only `source/municipal_codes_html.py`, `source/verify_municipal_input.py`, the two tests and the small reader/packager registration deltas are proposed for integration. Existing copied common modules are exact proof snapshots, not permission to overwrite later shared changes. `integration.json` gives the whitelist and commands. The frozen manifest omits intermediate failed package attempts and redundant preliminary packages; their logs remain historical development receipts where explicitly selected. Root owns production promotion, registry/launcher mapping and Git. No source acquisition or access restoration is part of this change.
