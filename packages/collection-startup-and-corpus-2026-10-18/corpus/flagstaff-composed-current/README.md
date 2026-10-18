# Composed writer: actual Flagstaff integration bridge

This is a separate, frozen offline integration proof. The independently reviewed `6744bed5` Flagstaff base remains unchanged. The eight executed writer/reader modules are the final composed runtime: package `119a9e45`, registry `b76afada`, common `b522283f`, and the unchanged Flagstaff reader/hierarchy helpers. The registry now also exposes the independently developed Municode and enCodePlus HTML readers. This bridge executes the Flagstaff reader only; Major’s separate actual Henderson and Lincoln Charter proofs qualify the other two readers. Native/PDF/Word grouping and all-family readiness are not claimed.

The ordinary-Python fresh build packaged every one of the same2,661 records,2,658 TOC nodes and3 explicit body-only units. All15 generated corpus/sidecar artifacts are byte-identical to the reviewed base. These include all16 fields, BOM CSV, fulltext/derived TOC, source parent/disposition/provenance sidecars, inherited coverage and validation report. All544 original input files, canonical HTML, tables/lists/notes,882 `[IMAGE]` markers, IDs, source acquisition times and version are unchanged. There is no raw HTML normalization, publisher access, native parser, or image decoding/extraction/rendering/OCR.

The actual selected package is `actual/flagstaff-composed-package-v3`. Its captured `packager-source/` is self-contained. Runtime dependencies are Python standard library only; POSIX `fcntl` is used. Tested CPython3.12.14 for the fresh ordinary-Python build,27 Flagstaff tests and both ordinary/`-B` guarded relocated entrypoints on macOS26.6.2 arm64. Verification returns2 because the original incomplete source gates remain false. Package verification passes; source consistency, publication acceptance, jurisdiction/dependency closure and final independent-source review are not upgraded by packaging.

## Report-path workflow actually exercised

The original common receipt’s absolute `log` path points to a complete JSON family report. Its original bytes were confirmed identical to the retained family report and copied to `bridge-input-proofs/original-common-family.log`. No manual JSON extraction or reserialization occurred. The original receipt is preserved byte-for-byte as `original-read-only-proof.json`.

A clearly labeled derivative receipt adds only a normalized relative `family_verification_path`, its exact SHA256, and original-proof/log lineage. The fresh build omitted `--family-verification`, so the final writer selected the exact copied `.log` through that explicit relative path. This is proof-path augmentation, not a new source verification. No original source gate changes. A separate actual negative with the untouched old receipt refuses to follow its historical absolute log automatically and creates no output.

```sh
# All commands below are relative to this selected packet.
python3 actual/flagstaff-composed-package-v3/packager-source/package.py verify \
  --out actual/flagstaff-composed-package-v3
# Expected exit2, package_verified:true, complete:false.

python3 -B verify_bridge.py
python3 -B audit_actual.py actual/flagstaff-composed-package-v3
python3 -B relocate_verify.py actual/flagstaff-composed-package-v3
(cd writer-tests && python3 -B -m unittest -v test_package)

# Fresh isolated reproduction of the actual default-relative-log workflow:
python3 writer-tests/package.py package \
  --input actual/flagstaff-composed-package-v3/evidence/input \
  --proof bridge-input-proofs/read-only-proof-relative-log.json \
  --reader originals-flagstaff-html-v1 --out /fresh/disjoint/destination
```

`verify_bridge.py` checks all15 generated artifact hashes against the included original base manifest, all544 source input hashes, exact proof/log lineage and all eight executed module hashes without accessing an outside original path. `audit_actual.py` performs the all2,661-row/source-ancestry/heading/CSV consumer audit. `relocate_verify.py` runs the shipped source with both ordinary Python and `-B`, denies outside-package file reads/socket creation/writes, and proves no bytecode or artifact changes.

The source-only capture receipt `SOURCE-FREEZE.json` pins Major’s final MC landing Notes/Footnotes guard (`municode_html.py`88ac7625). Only its eight writer MODULES are executed by this bridge and included in `WRITER-SOURCE-BINDING.json`. The separate verify-input helper is deliberately not shipped or qualified here; its final proof belongs to Major/AL. The prior8ce and978f bridges remain unchanged as historical proofs; this freshv3 rebinds corrected MC plus padded image-MIME common guard without altering Flagstaff projection. `writer-tests/` contains only the executed writer modules, portable27-test source and compact original HTML fixtures. The raw original HTML fixtures/evidence may intrinsically reference images; no separate image assets are included or fetched. Exact `[IMAGE]` positions remain the normalized output policy.

The selected copy plan contains the complete current actual package plus compact lineage, source and test evidence. It excludes the local pre-final snapshot and unused helper files. This bridge has no production/common-launcher/Git/database mutations and makes no new live or full-jurisdiction claim.
