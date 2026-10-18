# Current live Flagstaff → promoted corpus exporter

This frozen packet closes the actual current live collection to current promoted export. It uses ICC’s finalized early-inventory live collection and its separate CURRENT common read-only verification, not the historical Flagstaff bridge. The source collection, proof and actual family JSON log were read unchanged. The promoted production writer was invoked directly with ordinary Python; no source normalizer, publisher request, native parser or image operation was run during export.

The selected corpus is `package/`. It contains all558 exact current input files, the unmodified current common receipt and family report, the eight captured promoted runtime modules, and all2,661 source-derived rows/dispositions. Fulltext is exact canonical semantic HTML, preserving377 tables,27,167 cells, source lists/notes and882 literal `[IMAGE]` positions. All16 fields, source parents/locators, CSV UTF-8 BOM, JSON envelopes and derived TOC are audited against the CURRENT input. Acquisition timestamps and source-version binding come from this current collection; they are not borrowed from the historical package.

## Acceptance dimensions

| Dimension | Result |
|---|---|
| Actual live collection | terminal exit0 |
| Separate CURRENT common read-only verification | exit0, `verified_publication`, acceptance gaps empty |
| Inherited primary text, nonimage documents, legal structure and source target coverage | accepted |
| Inherited `publication_accepted` and primary `complete` | true |
| Literal source navigation | false, preserved as its own observation |
| Native capture / edition | false / null in the current common acceptance; no new claim |
| Whole jurisdiction, external dependency closure, independent final-source review | false, preserved |
| Corpus serialization/package verification | passed |
| Strict corpus `complete` / downstream readiness | false; expected exporter exit2 |

The exporter’s exit2 is the strict jurisdiction/readiness qualification. It does not erase the actual current primary operational acceptance. Three literal-reference observations retain their source-target resolution evidence; packaging neither removes those observations nor invents a new source waiver.

## Exact input and runtime binding

`ORIGIN-BINDINGS.json` records the exact production argv and origin paths. `TERMINAL-BINDINGS.json` proves all558 original files, proof/log bytes and eight production source modules remained unchanged and exactly match the copied package.

- CURRENT receipt SHA256: `4f0146a2e52ff4953fdf6e2be1333fe7a3c375538a5b10c7db512f58b0156a85`.
- Actual CURRENT family JSON log SHA256: `53818c2ea07a257cba24b8c86f0cc12b31b4d4af367aba488c9f2696c1faed74`.
- Current coverage SHA256: `f07572dbd7052805215aeac74962fda18e67a79e067094df73b7e873fd5573d9`.
- Promoted runtime includes common `b522283f`, package `119a9e45`, registry `b76afada`, MC reader `88ac7625`; all eight exact hashes are retained in the package binding.

The original common JSON log was passed directly as `--family-verification`. No manual JSON extraction, reserialization, relative-path augmentation or receipt mutation was needed. The copied operational proof references are relative. Absolute origin strings inside original evidence are provenance only and are not followed by portable verification.

`acquisition-lineage/` retains ICC’s immutable terminal summary and602-file acquisition manifest as documentary origin evidence. This selected packet fully includes the558-file current collection and required corpus proofs. The acquisition packet’s supplemental terminal controls remain separately retained by ICC/root; this export does not promise to restore every602-file acquisition control from this selection.

## Standalone commands

From this packet directory:

```sh
python3 -B verify_packet.py

python3 package/packager-source/package.py verify --out package
# Expected exit2, package_verified:true, strict complete:false.

python3 -B audit_actual.py package
python3 -B relocate_verify.py package

# Fresh offline reproduction from the complete embedded current source:
python3 package/packager-source/package.py package \
  --reader originals-flagstaff-html-v1 \
  --input package/evidence/input \
  --proof package/evidence/proofs/read-only-proof.json \
  --family-verification package/evidence/proofs/family-verification.json \
  --out /fresh/disjoint/destination
```

`operator-command.sh` records the exact actual production invocation as evidence; its original output is now sealed. Use a fresh destination for reproduction. Completed verification is read-only. Runtime dependencies are Python standard library only with POSIX `fcntl`; actual build/verification used the common CPython3.12.14 runtime on macOS26.6.2 arm64. Windows is unqualified.

The all-row consumer audit covers every row and source disposition. The relocated shipped CLI ran with both ordinary Python and `-B`, with outside-package file reads, writes and sockets denied; it added no bytecode and changed no evidence. `verify_packet.py` verifies the selected hash inventory and captured corpus while requiring the CURRENT primary acceptance and preserving strict jurisdiction false. No unit-suite, raw normalization or publisher replay was repeated. No separate image assets are copied/fetched; immutable original HTML may intrinsically reference images, while all normalized output retains exact `[IMAGE]` placeholders.

Historical `6744`, `ef1`, `8ce` and `978f` packages remain immutable. This is a new current-live export, and no historical acceptance result substitutes for its current receipt.
