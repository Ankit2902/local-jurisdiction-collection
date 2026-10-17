# Gridics native-tree collector

This adapter traverses every top-level root exposed by the ordinary Gridics CodeHub application. It uses installed headed Chrome through Python Playwright and captures the native JSON responses requested by that application, together with the rendered legal DOM for each root. It repeats the full traversal in a fresh context to check source consistency. It does not need Codex.

Two separate configurations have now exercised full native acquisition in ordinary headed Chrome: Cupertino, California (document 75), and Miami, Florida (document 45). Both have independent opening and closing traversals. Counts below are evidence, not hardcoded limits; the collector follows the fresh source inventory on every new run. Neither publication currently passes every completeness criterion.

Install the repository's [integrated runtime](../ops/README.md), then run from the repository root:

```sh
.collection-runtime/venv/bin/python -B -m collectors.gridics.collect collect --config collectors/gridics/configs/cupertino.json --out /absolute/path/cupertino
.collection-runtime/venv/bin/python -B -m collectors.gridics.collect verify --config collectors/gridics/configs/cupertino.json --out /absolute/path/cupertino
```

For Miami, use `collectors/gridics/configs/miami.json` and a separate fresh output directory. The same commands apply.

Repeat collection with `--resume` after a recoverable interruption. Resume requires the identical config and collector source hashes. Existing retained source is checked; a changed publication inventory or altered bytes fails rather than mixing editions. Verification makes no network requests. Both commands return `0` only when their complete selected-publication criteria pass, and `2` for incomplete or invalid output.

October 17, 2026 validation results are recorded in [validation-summary.json](validation-summary.json), with compact receipts in `proof-receipts/`:

| Publication | Roots / records | Tables / cells | Image placeholders | Remaining completeness gaps |
| --- | ---: | ---: | ---: | --- |
| Cupertino | 22 / 2,687 | 131 / 11,681 | 35 | Five unexplained empty publisher entries; 2,308 unresolved reference occurrences |
| Miami | 32 / 828 | 137 / 10,892 | 439 | Two unexplained empty publisher entries; 1,439 unresolved reference occurrences; 112 opening/closing comparison differences |

Cupertino's native text, headings, table structure and image counts agree with the rendered witnesses. Miami's 56 differences per traversal are whitespace differences, including joined inline words and nested list breaks inside table cells. The source text is preserved, and this diagnosis **does not waive** the exact comparison failures. Both runs have stable opening/closing inventories and zero separately downloaded image assets. Their verifiers return `2` because the documented completeness gaps remain.

The collector retains the native code and reference inventory, but does not automatically fetch external nonimage documents. These include Cupertino's comprehensive ordinance index. Empty entries are preserved with source IDs and headings; a flat sequence of numbered headings is not assumed to prove an empty entry is merely a container. No whole-jurisdiction completeness claim is made.

App JavaScript indicates a DOCX export capability, but the observed anonymous pages did not expose a verified usable download control. A publisher export is therefore not currently a qualified alternative to the tested native-tree acquisition.

## Evidence and acceptance

The output retains acquisition configuration and executed source, hashed native response bytes, root inventories, per-root rendered HTML, opening/closing checkpoints, request dispositions, normalized `records.jsonl`, `references.jsonl` and `coverage.json`. Each heading owns its immediate body blocks; source child order and block IDs remain explicit so parent material is not duplicated into descendants.

The verifier reconstructs normalized records from retained native trees and compares inventories, headings, owned text, tables and image placeholder counts against the independently rendered DOM. Opening and closing native responses must be distinct acquisitions. Required source changes, missing roots, duplicate IDs, broken hierarchy, unknown node types, unexplained empty leaves and unresolved external references prevent the corresponding completeness flags.

All image handling follows [IMAGE-POLICY.md](../IMAGE-POLICY.md). Browser image/media/font requests are blocked, and separate image response bodies are not saved. Normalized output uses literal `[IMAGE]`; source IDs/headings and image-only legal units remain. Original HTML/JSON may contain embedded source image markup as immutable evidence, but normalized HTML has no active image elements or CSS fetches. No image extraction or OCR occurs.

Run the offline regressions from the repository root:

```sh
.collection-runtime/venv/bin/python -B -m unittest collectors.gridics.tests.test_model collectors.gridics.tests.test_native_fixture collectors.qa.test_gridics_acceptance collectors.qa.test_all_family_image_metadata
```

The 27 tests include an actual retained Cupertino Title 11 native tree and independently rendered witness: 190 records, 19 tables and its image placeholder. That fixture is one complete root, not a full-publication proof. Other tests reject source-identity, revision, receipt-phase and closing-time mismatches, and test image-only provisions and embedded image data. Full retained runs can be re-normalized with `replay --config CONFIG --source OLD --out NEW`; this is an explicit offline derivative with preserved source lineage, never a live acquisition claim.

The shared rate gate is `~/.local/state/local-jurisdiction-collection/gridics`, with a minimum 3.5 seconds between first-party document/XHR/fetch requests. HTTP 401/403/429 produces a persistent stop. The collector does not clear the gate, import cookies, alter browser fingerprints or circumvent a publisher challenge.

Final image-policy hardening treats MIME types, data URLs and image input types case-insensitively. The focused model, actual-source fixture and acceptance suite passed 23 tests without network requests; see `proof-receipts/image-casing-final-tests.log`. Earlier retained live proofs preserve their actual executed revisions.
