# American Legal full-publication collector

This standalone collector supports dynamic American Legal publication selection, recursive publisher TOC inventory, pinned-edition full traversal, and genuine whole-publication native HTML export. It contains no built-in target IDs or absolute dependency paths. The registry supplies the jurisdiction, state, current source route and publication selector. All fifteen American Legal primaries in the 100-target registry are mapped; live completeness validation is limited to the publications named in `validation-summary.json`.

**Image policy:** all images become literal `[IMAGE]`. Images are never explicitly downloaded. Normalized HTML removes raster/picture/SVG/image objects, image links/posters and active CSS image URLs while retaining source IDs, headings and image-reference metadata. Browser image resources are blocked where practical; publisher security controls are left enabled. Inline image data is represented by a hash and placeholder in normalized metadata. Original publisher HTML/PDF files may contain images and remain source evidence; image binaries are not separately extracted. Intentional image omission is not a completeness gap. Nonimage PDF/document attachments remain separate required assets.

## Install

Use Python 3.9+ on macOS/Linux (the shared gate uses `fcntl`), Node18+ and ordinary installed Google Chrome. Windows locking is untested. Live proof used Python3.9.6, Node24.19.0, Playwright1.62.1, Chrome155.0.8059.84 on macOS26.6.2/arm64. No Codex runtime/API, imported browser profile, masking or challenge interaction is used. PyMuPDF1.26.5 now supplies PDF text geometry and native ruled-table candidates alongside the independent pypdf text engine.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r collectors/american-legal/requirements.txt
npm install --prefix collectors/american-legal
```

`NODE_BIN` optionally selects Node. `BROWSER_CHANNEL` defaults to `chrome`. `PLAYWRIGHT_MODULE_ROOT` optionally identifies a package.json whose normal dependencies include Playwright. The browser bridge receives the current Python interpreter automatically for the gate. These variables permit normal installations; bundled workstation runtime paths are only in execution receipts.

## Fresh, resume and verify

A fresh output directory must not exist. An overview containing multiple independent publications requires an observed slug/title/UUID selector; a publication URL can supply its slug. `--jurisdiction` is checked against the publisher client name after punctuation/case normalization, without dropping county/city distinctions. Use explicit `--identity-alias` only for an observed abbreviated publisher identity. The registry records Louisville's `Louisville-Jefferson County` and Honolulu's `Honolulu` aliases.

```sh
.venv/bin/python collectors/american-legal/collect.py \
  --url https://codelibrary.amlegal.com/codes/san_diego/latest/overview \
  --jurisdiction 'San Diego County' --state CA --publication sandiego_ords \
  --strategy native --assets reference-only --out /NEW/PATH/index-run

.venv/bin/python collectors/american-legal/collect.py \
  --url https://codelibrary.amlegal.com/codes/san_diego/latest/overview \
  --jurisdiction 'San Diego County' --state CA --publication sandiego_ords \
  --strategy native --assets reference-only --out /NEW/PATH/index-run --resume

.venv/bin/python collectors/american-legal/verify.py /NEW/PATH/index-run --offline
```

Default strategy is `traverse`: dynamically inventory the full publication, fetch every independently inventoried renderer-owned doc/index range, and retain full legal HTML/text, parent/path, body-block IDs, tables/spans/relationships, links and notes. Strategy `native` inventories the same complete independent TOC, selects the whole code's visible Download checkbox, chooses Save HTML, asserts the actual posted whole-code scope/version, follows the new job's OPEN link and partitions every native rich block into exactly one independent TOC owner. Extra headings, absent middle nodes, duplicate IDs, leaked descendant bodies and unowned native text fail closed. There is no first-N default.

`--max-items N` is an explicit bounded diagnostic limit on inventory/traversal and always forces incomplete status. `--assets download` is the default for nonimage required assets. `--assets reference-only` deliberately retains references without downloading those documents, forces attachment incompleteness where such references exist, and is useful for large ordinance indexes. It does not suppress the original native PDF for an independently PDF-published unit. Source-explicit incorporated/adopted nonimage standards are required even with extensionless URLs. Unknown types remain unresolved. Nonimage downloads are screened by HEAD; image MIME responses become placeholders without a GET. CSS image dependencies become placeholders; known fonts/styles remain separately qualified.

Exit codes are **0** for sound complete publication text plus required nonimage asset bytes, **2** for a sound incomplete scope/limit or failed acquisition, and **1** for verifier corruption/reconciliation failure. `verify.py --allow-incomplete` returns0 only when the retained evidence recomputes consistently while its explicit incomplete flags remain intact. It does not promote coverage.

## Checkpoints and access stops

Atomic raw-cache and checkpoint writes bind requests to source URLs, original hashes, publication identity and independent inventory hash. Resume revalidates every cached source, refreshes current publication identity, rejects edition/configuration changes, rebuilds outputs deterministically and fetches only uncached legal ranges. Exact executed revisions are retained by content hash in each run's `script-versions/`; `scripts/` retains the latest run revision. A native export job is durably checkpointed immediately after its publisher POST. Resume validates that original whole-book scope/edition and downloads the same UUID through the observed public publisher download route using an ordinary headed browser. The original UI scope and posted job are retained; no cookies/fingerprints are imported and no second job is created for an existing checkpoint. Actual HTTP status/headers and download failure/length checks are retained. `export-checkpoint.json` binds the completed download hash and original scope UI to that job. A policy change requires a new directory; prior proof is retained under its original policy. The final current-source live run is `index-current-final`; `index-no-images-final` is supporting current-policy resume proof. The earlier `index-native-final`, `form-based-pdf-final` and `ordinance-index-live` normalized outputs are superseded by the image policy. Only the renderer reference's retained raw packets are recomputed for the comparison.

The shared publisher gate is `/tmp/compliSolv-american-legal-full-gate` unless `AMLEGAL_GATE_DIR` is set. All processes must share it. Starts are separated by3.5seconds.403/429/challenge stops persist, Retry-After is recorded, and there is no reset command. A challenge requires operator investigation, not another transport/profile/proxy attempt. Direct HTTP returned403 in this stage and remains stopped; the previously qualified ordinary headed-browser route succeeded. Unrelated export-panel polling is omitted during renderer traversal. Fresh whole-export creation follows the visible publisher controls; resumed existing jobs use their observed public UUID download route under the same gate.

Legal-source errors and access blocks stop acquisition and retain durable successful work for resume; failed/interrupted runs cannot pass verification. Unavailable nonimage assets retain their actual HTTP response and a bound unavailable disposition, allow other assets to proceed, and keep attachment completeness false.403/429/challenges always stop the publisher. An exclusive per-output file lock rejects concurrent writers to the same output directory. A missing required document is never treated as a justified exclusion merely to finish. `--retry-unavailable-assets` permits an explicit resume to retry cached unavailable HEAD/binary responses once per asset, preserving immutable earlier response history. It cannot override the publisher access-stop gate. HEAD405/501 falls back to a genuine GET only for an explicit known nonimage file extension; actual downloaded bytes are still format-validated. A corrupted or wrong-edition cache is refused. Same-book references detected in adopted/incorporated language are bound to acquired independent TOC/body IDs; an absent target remains unresolved. References to another book remain required documents.

## Outputs and interpretation

- `run.json`: requested/observed identity, pinned edition, dynamic publication family inventory, policies, executions and status.
- `requests.json`, `raw/*`: original publisher response bytes, response metadata, hashes, scope/ready UI evidence and source URLs. Original HTML/PDF can contain images.
- `inventory.json`, `inventory-end.json`: independently reconstructed recursive TOC nodes, parent/path, source render ranges and pending inventory.
- `checkpoint.json`: acquired IDs bound to inventory hash.
- `sections.jsonl/csv`: exactly one owned TOC-node record. `html` and `text` are normalized under the image policy; original bytes remain in `raw`.
- `pdf-pages.jsonl`: all pages from every retained native publication or required attachment PDF, separate from TOC-node records. Shared PDF bytes use explicit owner aliases, not duplicated page bodies. Positioned text spans/fonts, independent engine character agreement, reading-order diagnostics and ruled-table candidates retain geometry. Unknown table/column layouts remain explicitly unqualified. Raster image objects and page vector graphics become metadata-only `[IMAGE]` markers; no rasterization or image binary extraction occurs.
- `assets.json`: required nonimage assets, deliberate image placeholders, unresolved references and format qualification.
- `coverage.json`: recomputed inventory/missing/extra/duplicate/ownership, text, nonimage attachment, edition, native-file and image-policy fields. Jurisdiction completeness is always false because one selected publication does not enumerate every jurisdiction family.

A complete native PDF file and every extracted page do not by themselves qualify legal-provision segmentation or PDF reading order. `native_publication_files_complete` and `pdf_text_layer_extraction_complete` are separate from `publication_text_complete`. Image omission is intentional; PDF text/section qualification limitations are unrelated to omitted image content. A native HTML file can be complete while linked nonimage ordinances remain unacquired.

## Offline proof and fault tests

```sh
.venv/bin/python collectors/american-legal/test_faults.py
.venv/bin/python collectors/american-legal/verify.py \
  collectors/american-legal/fixtures/nested-synthetic.zip --offline
.venv/bin/python collectors/american-legal/verify.py \
  collectors/american-legal/fixtures/live-index.zip --offline --allow-incomplete
```

The ZIP verifier reads files directly without extraction, network or output writes. It recomputes independent TOC branches, all source hashes, ownership, outputs and coverage instead of trusting a stored success flag. The synthetic fixture is clearly labeled and is not live-law proof. Tests exercise actual production collection/cache/resume: after2 committed nodes, interruption is rejected, resume fetches only3 remaining nodes, and outputs equal an uninterrupted5-node run. Faults include middle-branch loss with all top roots retained, truncated native bodies, duplicate/omitted outputs, corrupt bytes, changed edition, mismatched checkpoints, missing asset dispositions, explicit limits, and image no-fetch/placeholder cases.

An additional whole-body comparison recomputes all30 raw renderer provisions and compares native bodies, raw block IDs and table text/spans:

```sh
.venv/bin/python collectors/american-legal/compare.py \
  /EVIDENCE/index-current-final /EVIDENCE/ordinance-index-live
```

The reference's old normalized outputs are not trusted; its raw response packets are recomputed under the final image policy. Both folders are in the new evidence package, with no dependency on earlier sealed packages. Compact offline comparison fixtures are also included:

```sh
.venv/bin/python collectors/american-legal/compare.py \
  collectors/american-legal/fixtures/live-index.zip \
  collectors/american-legal/fixtures/renderer-reference-raw.zip
```

The renderer-reference ZIP is a raw-only comparison input, not a standalone final-policy collection run. The 54.8MB Cleveland PDF can take several minutes per complete verification because every page is reparsed; its acquisition already ran that verification successfully.

## Prior validated scope and active readiness work

The prior sealed validation established that the genuine independently published San Diego County Comprehensive Ordinance List has30 TOC entries (cover plus1998–2026), all explicit leaves. Full index traversal and a whole-publication native HTML export reconcile all30 IDs and97 rich blocks. The index contains1940 distinct nonimage ordinance-PDF references; those were deliberately not mass-downloaded, so complete ordinance corpus and nonimage attachment completeness are false. This is whole **index-publication** text proof, not a nested whole municipal regulatory code proof.

Cleveland's independently published Form-Based Code is a single native PDF publication with212 pages; the full original file and all page-layer outputs were acquired/parsed. Whole Cleveland Codified Ordinances also produced a genuine22,331,790-byte native HTML file, but its full nested independent inventory was not acquired, so it is retained as native-file/scope proof only. Recursive nested main-code behavior is qualified by independent raw-inventory fault tests, not mislabeled as a completed live nested municipal code.

Before scaling, choose each independently published code/charter/zoning/policy family, review county applicability, allocate time for full dynamic inventories and nonimage required documents, and audit special formats. No full runs across all100 jurisdictions have been performed or implied.

## Readiness extension

The active readiness work is recorded in `validation-summary.json` and the new `outputs/collection-readiness-2026-10-17/american-legal` package. A full nested Cleveland primary code acquisition is running with independent branch inventory, whole-code native export and all required nonimage documents. Do not equate the prior index proof or source route mappings with completed primary regulatory-code verification.

All retained PDF attachments now get normalized page records. PDF character agreement, positional text and qualified simple ruled-grid geometry are tested; ambiguous parallel columns, diagram fragments and incomplete ruled grids remain explicit diagnostics. Automatic table candidates do not certify all tables or legal reading order. The offline PDF inspection CLI can qualify already retained native bytes without a new publisher acquisition:

```sh
.venv/bin/python collectors/american-legal/inspect_pdf.py \
  --pdf /PATH/native.pdf --source-url https://example.gov/document.pdf \
  --owner-id publication-id --out /NEW/PATH/pdf-inspection
.venv/bin/python collectors/american-legal/inspect_pdf.py \
  --out /NEW/PATH/pdf-inspection --verify
```

The live-index fixture was recomputed under the current verifier from its unchanged original raw evidence and explicitly records offline reprocessing. This is compatibility replay, not a new live acquisition.

The readiness checkpoint retains 44 passing production-path fault cases. A real localhost headed-browser interruption test also confirms that an in-flight interrupted RPC closes its owned browser processes (0 remaining; 0.083 seconds), without publisher traffic. The active Cleveland run deliberately interrupted a real submitted native job, then resumed the same UUID and retained the actual 22,331,790-byte HTTP200 HTML download; final full-code independent end reconciliation remains pending until its terminal coverage receipt exists.

The delivered validator also rejects accidentally supplied separate image bytes before any decoder or XML image parser. A regression mocks both raster and SVG decoders to raise; image URL, MIME and signature cases still return policy-excluded. The ongoing Cleveland executed-v3 source predates that defensive unreachable-path removal and remains separately retained; its live execution is not relabeled.
