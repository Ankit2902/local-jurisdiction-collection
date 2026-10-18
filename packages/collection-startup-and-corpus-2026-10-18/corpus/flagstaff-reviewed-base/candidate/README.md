# Offline corpus package candidate

This is an isolated implementation candidate, not an installed collector or common-launcher action. It packages an already verified, immutable source IR; it does not collect source or rerun a source normalizer.

Only `originals-flagstaff-html-v1` is supported. It reads the original operational Flagstaff HTML collection root, its hash-bound read-only verification receipt, and the corresponding family raw-replay JSON report. Other family/native modes fail closed. The reader registry and `Projection` interface make later mappings explicit; there is no guessed universal field adapter.

Tested: CPython3.12.14 and3.9.6, macOS26.6.2 arm64. Runtime dependencies are Python standard library only. POSIX `fcntl` locking is used for packaging; Windows is unqualified. No browser, Codex, database, Node, PDF reader, image library or network dependency is used. The entrypoint sets `sys.dont_write_bytecode=True` before local imports. Both ordinary Python and `-B` shipped CLI forms are tested with no added bytecode files.

## Commands

```sh
python3 -B package.py package \
  --reader originals-flagstaff-html-v1 \
  --input /retained/flagstaff-operational-root \
  --proof /retained/flagstaff-current-readonly.json \
  --family-verification /retained/exact-family-verifier-output.json \
  --out /fresh/jurisdiction-package

# Same exact source/proof/reader/code bindings; continue an owned interruption.
python3 -B package.py package \
  --reader originals-flagstaff-html-v1 \
  --input /retained/flagstaff-operational-root \
  --proof /retained/flagstaff-current-readonly.json \
  --family-verification /retained/exact-family-verifier-output.json \
  --out /fresh/jurisdiction-package --resume

# Self-contained read-only verification after copying the package elsewhere.
python3 -B /copied/jurisdiction-package/packager-source/package.py verify \
  --out /copied/jurisdiction-package

python3 -B -m unittest -v test_package
```

Exit0 means a verified package whose inherited required readiness gates are all true. Exit2 means serialization/package verification passed but the source/readiness result remains incomplete. Exit1 is invalid input, corrupt/foreign evidence, unqualified mapping or verification failure. `package_verified:true` is distinct from `complete:true`. Test-only `--interrupt-after N` exits75 after a durable artifact boundary; resume/fresh output equality is tested.

The actual retained Flagstaff input has raw replay equality but remains incomplete for three missing source anchors. Its literal source consistency/publication/jurisdiction/independent-review false gates are preserved. This candidate does not borrow the later isolated navigation-v9 results, assert a new full live run, or silently qualify additional publications.

## Input binding and retained evidence

The read-only proof must include identical complete `evidence_sha256_before`/`evidence_sha256_after` maps, stable collector-source maps, no publisher requests, no runtime/source drift, explicit selected config and publication ID. Every input file must match this map; missing or additional files fail. The separate family report must affirm raw replay equality, no modified inputs, source-route/chronology checks, exact config and source-checkpoint hash. A source-completeness nonzero outcome can still affirm these sound incomplete-data checks.

The reader checks the source/raw receipts, copied normalization code, coverage/summary agreement, complete independent TOC mapping and original block ownership without parsing original HTML. It copies **all** bound original files byte-for-byte into `evidence/input`, including rich JSONL, raw HTML, receipts, source inventories and captured execution code. Reports go under `evidence/proofs`. Original absolute path strings inside historical evidence are retained as provenance only; operational package references are relative and verification never follows original absolute paths. This is a binding to an existing explicit verifier result, not cryptographic authentication of an arbitrary user-supplied report.

No separate images are copied/acquired as assets. Image file extensions or image MIME source artifacts are rejected. Original publisher HTML may contain image references/data intrinsically; it remains unchanged original evidence. Canonical output must already be image-free source IR. Active image/SVG/image-MIME/CSS image markup or image data in canonical text/attributes is refused rather than transcribed. The literal `[IMAGE]` stays in its existing owned position; no image grabbing, decoding, extraction, rendering or OCR occurs.

## Delivered interface

The output contains `run-manifest.json`, `publications.json`, `source-nodes.jsonl`, `node-dispositions.jsonl`, `record-provenance.jsonl`, `validation-report.json`, `exceptions.jsonl`, immutable evidence, and publication/aggregate fulltext and derived TOC JSON+CSV pairs. `package-state.json` owns resumable packaging and `packager-source/` captures the exact five runtime modules.

Every corpus row has exactly the original16 ordered string fields. JSON uses `{metadata, provisions}`; CSV uses UTF-8 BOM and standard quoting. Fulltext/TOC/publication/aggregate identities and order match; the derived TOC changes only `full_text` to empty. It is never used to prove independent source completeness.

`full_text` is the exact canonical `semantic_html` from the verified rich record, preserving tables/spans, paragraphs, source list wrappers/enumeration, notes, superscript/subscript and `[IMAGE]`. No table/list/note/diagnostic text is appended from other fields. Correct canonical structure therefore drives consumer HTML; `superseded_detector_diagnostics`, if present in rich IR, stays only in preserved evidence. Plain convenience text is not substituted for structured HTML.

Source rows retain the original order and record IDs through provenance. Flagstaff's locally assigned body IDs are copied from its verified normalizer (source document plus source block ordinal); raw block/heading locators and exact executed normalizer versions remain available. Publisher TOC edge IDs retain their original composite identities and descriptors. Duplicate printed headings remain separate; no printed designation is renumbered. Source introduction labels assigned by the normalizer are not exported as publisher citations.

Hierarchy is projected from available publisher evidence. The complete `ancestor_classes` path is scoped to its component `root_index`; the exact trailing `source_id.split()` token sequence identifies the current node, and the remaining unique path identifies its parent. This handles repeated Charter section IDs and source IDs containing spaces without guessing ancestry from printed citations or URLs. Every TOC node retains its original descriptor and a separate parentage witness. Three body-only units remain explicit body-only dispositions; their contextual parents come from their document root or shared published parent ancestry, not fabricated TOC edges.

Canonical heading classes/types supply field roles: `h1.Title` to `title`, `p.Division` to `division`, and `h2.CH` with an explicit printed CHAPTER or ARTICLE label to its corresponding field. A literal APPENDICES group has no invented chapter label. One explicit adjacent `h2.CH` / `h2.CHTitle` continuation is joined only for the chapter label when its raw source, consecutive block order and heading-only predecessor agree; its two records and complete bodies stay separate. Unknown or conflicting types remain qualified blanks. The exact canonical heading must agree with the IR heading after omission of existing `[IMAGE]` markers from the label comparison only; those markers remain unchanged in `full_text`.

For source `h3.Cite` and the two source SECTION groups, `section_number` is the actual displayed locator corroborated by its own heading/anchor `name` or `id`. Numeric, PW-prefixed and Amendment No. locators are supported; comparison permits published dash/dot separator variants and strips anchor-edge whitespace, but the emitted locator is displayed source text. Thirteen unnumbered statutory-reference headings remain unnumbered. No locator is inferred from arbitrary publisher IDs. Section names remove a qualified own locator from Cite headings; citations remain the complete literal heading, including actual note suffixes. The remaining hierarchy columns stay blank when that role is not supplied by source. Every field has source record/node/raw-hash/heading/anchor witnesses in provenance. `scrape_date` is the raw body acquisition `started_at`, with timestamp precision retained, not replay time or a legal effective date. Publisher currency is kept verbatim with a source-checkpoint snapshot ID; no legal date is inferred.

Independent source nodes comprise every original TOC edge plus body-only source units. Each receives exactly one disposition and its emitted record IDs. Own-content, source-confirmed reserved/repealed and source-confirmed structural cases use existing source classifications. The raw TOC witness and body witness remain distinct. There is no blanket heading-only-container exclusion. Publication scope stays the original selected City Code including Charter; discovery/closure of all other jurisdiction publications remains unqualified.

## Safeguards and supported scope

Fresh output must be empty and disjoint from input. Resume requires an owned checkpoint with exact reader/publication/input/proof/code bindings and matching committed artifacts. Unknown checkpoint schemas/phases, corrupt pending/committed bytes, unrelated files, symlinks, unsafe paths and source drift fail closed. Writes are atomic; explicit interruptions preserve existing artifacts. Completed resume verifies without modifying the package. The verifier reconstructs every generated artifact, checks exact file inventory/hashes and all CSV/JSON/TOC fields, and does not write or access original source locations.

The first adapter does not support partial source inventories, speculative hierarchy, PDF-page-to-section conversion, native Word-unit grouping, multi-family jurisdiction assembly or any other publisher. New readers must explicitly produce the same typed `Projection`, preserve canonical fields and all source dispositions/version bindings, and supply their own real-source fixtures. The shared writer is reusable; unsupported mappings are not silently accepted.

Actual evidence: `../actual/flagstaff-package-v2`; full raw/source input preserved there. The compact `fixtures/actual-selected.json` plus original source HTML cover seven actual table/list/note/image/duplicate/unnumbered cases. They are bounded fixtures, not a replacement for the whole2,661-row package. The26 synthetic/actual-fixture tests add canonical-versus-diagnostic exclusion, negative/resume cases, and direct shipped CLI verification with and without `-B`. `../audit_actual.py` is an independent all-row consumer comparison to verified rich IR, not a new raw normalizer. `../relocate_verify.py` verifies a copied package with all outside-package file reads and socket creation forbidden.

## Narrow revision lineage

This isolated fidelity revision preserves the frozen609f756c baseline and84056045 no-bytecode revision unchanged. It retains bytecode suppression before local imports and strict unexpected-artifact refusal. Its changes add source-qualified parent/hierarchy/locator projection, physical-LF-only JSONL reading, a fifth small hierarchy module, and fail-closed HTML/recursive normalized metadata image checks. Active image inputs, MIME-less known-image objects, image links and CSS `url (` forms are refused. Known image metadata may not carry opaque data payloads. It does not strip ambiguous legal prose or fetch/decode an image.

The actual fresh derivative uses the previous package’s complete embedded verified input. All544 original evidence files, all2,661 canonical HTML bodies and their record IDs, raw hashes, acquisition times, literal citations and image positions are preserved. Previously blank corpus hierarchy/locator fields and corresponding source-parent/provenance sidecars intentionally change. The inherited coverage is byte-for-byte equal. This is no new acquisition or raw normalization. All source navigation and jurisdiction/dependency qualifications remain unchanged.

JSONL readers split only on physical LF (`'\n'`), preserving literal U+2028/U+0085 within legal values. Tests exercise both those characters. The CLI’s `--family-verification` argument accepts an actual JSON family-verifier log directly; no separate manual JSON reserialization is required. Automatic receipt-log discovery is not implemented.
