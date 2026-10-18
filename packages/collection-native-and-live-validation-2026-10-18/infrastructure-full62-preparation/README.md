# Prepared full 62-page Infrastructure retained-source workflow

Status: PREPARED; not launched. Root must announce the combined code freeze first. No production or common-launcher files were changed. The literal registered native URL alias must be promoted before snapshotting. SolidWaste workflow integration must also be stable.

`actual-source-preflight.json` independently hashes the genuine retained start/end originals and their receipts: source SHA915fe1fdf8ff5da33acfce7d08637808cb57886fbbc7f157b2b81bfcf970827c; 3,339,774 bytes each; 62 expected physical pages. Source checkpoint phase is finished. The receipts retain their original October17 acquisition timestamps and HTTP200 status. Preflight performs no PDF parse or requests. Seven transport integrity/fault tests pass (`preflight-tests.log`); their synthetic envelope is explicitly not used to prove PDF validity.

After freeze, choose fresh runtime/output/external-receipt paths and run:

```sh
python3.12 -B capture_runtime.py --repo REPO --out FROZEN_RUNTIME
python3.12 -B retained_native.py replay --runtime-tree FROZEN_RUNTIME --runtime-manifest FROZEN_RUNTIME/SOURCE-HASHES.json --source ORIGINAL_NATIVE_RUN --config FROZEN_RUNTIME/collectors/encodeplus/configs/native-82-0c6b3dc40877.json --out FRESH_FULL62 --receipt EXTERNAL_REPLAY_RECEIPT.json
```

The frozen runtime is a literal copy of all top-level enCodePlus Python files, targets, requirements and exact native config. The driver checks every captured hash before import and after execution. It invokes the unchanged standard native collector and its internal strict verifier. Only the collector's cached transport function is substituted: exact old start/end native bytes and exact receipt bytes are copied into the newly created output when the normal workflow requests them. Unknown URLs/paths, changed source/config/receipts or overwrites refuse. Driver/runtime/input hashes are recorded before execution in an external origin receipt. No parser, coverage flags or validation functions are patched.

The driver adds fail-closed image-stream/pixel/render/OCR-adjacent and network/decoder API tripwires. Original PDF bytes are allowed; image streams are not decoded. Only terminal receipts may establish zero forbidden calls. Current images remain `[IMAGE]`; captions/native labels remain text. This is retained-source validation, not a fresh live acquisition or new currentness witness.

After this workflow terminates, use the actual common standalone launcher in readonly mode with its owned runtime:

```sh
python3.12 REPO/collect.py --runtime OWNED_COMMON_RUNTIME verify --target 82 --publication 82-0c6b3dc40877 --out FRESH_FULL62
```

The normal launcher executes the registry-bound family verifier, records exact before/after source/evidence hashes, and does not write to the source output. This step may reparse the62pages as part of strict verification. It is not monkeypatched by this driver. Its receipt must distinguish native file/page success from full-publication acceptance; current native-only scope can correctly yield shared exit2 even when family verification succeeds. Do not relabel that result as a full legal corpus.

At terminal inspect coverage/summary/JSONL/CSV and compare `baseline-expectations.json`: all62source pages, four canonical TOC/cover selections,96entries/110units/603words,44old failed cells retained only as diagnostics, and three explicit page6leader/folio spacing discrepancies. Check every exact raw/hash/owner, retained source consistency, markers and legal labels, no data-image payloads, runtime equality and readonly file hashes. Other pages' concrete text/font/table/reading-order conditions remain visible; the finite four-page source fix does not certify the whole book's legal semantics or adopted-edition dependencies.

Do not run capture/replay until root freeze; do not reuse output paths; do not reset publisher gates or fetch images.
