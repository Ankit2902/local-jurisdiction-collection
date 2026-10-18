# Albany retained-source body-preservation correction — incomplete publication

This is an offline correction of acquired Albany eCode360 HTML. It is not new acquisition, publisher access restoration, a complete publication, or a fresh currency/closing proof. Original source/version/403 records and the prior normalized outputs remain immutable. No publisher requests, gate resets, image fetches, image extraction/decoding/rendering/OCR were used. Every image position is normalized to literal `[IMAGE]`.

The old normalizer removed nested legal `.content` elements without distinguishing independently owned GUID bodies. The original four-item ACCESSORY USE OR STRUCTURE definition retained only its numbered labels. The exact before-source reproduction is in `before-four-items-source-proof.json`. The corrected parser removes only explicitly independently owned GUID bodies and preserves parent-owned definition/list content. Its residual ownership check refuses unknown `.content` before generic UI/heading removal. The V2 combined-class fail-closed lesson and V3 refusal are retained in `unknown-content-boundary-before-after.json`.

The corrected retained scope has 3,253 inventory/disposition nodes and 3,006 records. Restored legal content changes 860 records, increases tables from 24 to 256, and restores image placeholders from 28 to 440. Own raw-DOM conservation checks bind all 3,006 acquired records, 7,706 legal nested content elements, 11,704 note elements and 12,175 source ID occurrences. The independent audit is a separate receipt supplied by American Legal's reviewer; do not confuse own parser comparisons with that independent source audit. V3's corrected record stream is byte-identical to V2, with all 401 raw hashes and all normalized streams bound in `v2-v3-whole-source-byte-bridge.json`.

Three MAP-labeled links are uniquely source-owned definition self-anchors, not external documents. Two were in the original six required references; the third becomes visible only after its legal parent body is restored. Each has exact source owner/target/href/definition-body pins. Required classification still wins when the same URL has a separate required-document reference. Cross-owner, different term/fragment/host, duplicate-target and actual PDF MAP links remain required.

Four actual required PDFs remain unqualified: AL0934-211a Appendix I, AL0934-211b Appendix II, AL0934-211c Appendix III, and AL0934-375a Table of Zoning Map Amendments. The only unique retained Albany publisher PDF is the one-page §1-13 bounded export; it cannot satisfy these. No source closing sweep follows the last acquired body. The original HTTP403 stop, no-network state and all false publication/attachment/edition gates are preserved. Restoration also exposes 21 unresolved statutory-forwarding link occurrences (18 unique URLs); their original source `statref` class and exact law contexts are inventoried separately, without extending selected-publication scope or silently waiving them.

`albany-derived-v3/source-coverage-original.json` preserves the original coverage bytes, including its six originally required references. `coverage.json` is an explicitly new derivative correction; it does not overwrite that historical outcome. The standard source verifier's `verified:true` means reconstruction consistency under the selected exact source, while `complete:false` and its corresponding completeness exit 2 remain explicit. A corpus writer's successful serialization cannot upgrade these source gates.

Use the configured Python 3.12 environment with the selected collector requirements and the root-owned `collectors/corpus_package/requirements-verification.txt`. The separate verification helper checks Pillow, beautifulsoup4, requests and pypdf before creating any output or importing the selected engine. The portable corpus writer/verifier itself remains standard-library only. macOS arm64 is the tested platform; Windows is unqualified.

From this folder, with ECODE_PY set to the configured interpreter:

```sh
# Fast focused ownership/classification/image tests, no network.
"$ECODE_PY" -B test_ecode_body_ownership.py --collector-root candidate-v3
# Expected 18 PASS.
"$ECODE_PY" -B test_ecode_helper_preflight.py --input corrected-corpus-v3/evidence/input --helper handoff-candidate/verify_ecode_input.py
# Expected 6 PASS, including missing-dependency refusal before output creation.

# Existing synthetic graph/edition/asset/interrupt and municipal behavior suite.
"$ECODE_PY" -B run_existing_faults.py --collector-root candidate-v3 --test-source qa-source/test_faults.py

# Actual standard full raw reconstruction, fresh disjoint proof folder.
"$ECODE_PY" -B handoff-candidate/verify_ecode_input.py \
  --input corrected-corpus-v3/evidence/input --collector-root corrected-corpus-v3/evidence/input/executed-source \
  --publication-id albany-ecode-acquired-html --out fresh/source-proof
# Helper exit0 means raw reconstruction verified; publication_complete:false.
# The equivalent selected standard collector completeness result is exit2.

# Exact 16-field corpus serialization from that actual standard proof.
"$ECODE_PY" -B -S writer-source/package.py package \
  --input corrected-corpus-v3/evidence/input --proof fresh/source-proof/read-only-proof.json \
  --family-verification fresh/source-proof/family-verification.json \
  --reader ecode-html-retained-incomplete-v1 --out fresh/package
# Expected exit2 with package_verified:true and complete:false.
"$ECODE_PY" -B -S fresh/package/packager-source/package.py verify --out fresh/package
```

`promotion-candidate.json` and `promotion.patch` are candidate-only integration instructions: two eCode runtime files and the separate verifier helper. Root owns production promotion, shared requirements/docs and Git. No source config, publisher gate, registry or other publisher parser is changed here. The exact municipal parser source and actual nested-article behavior are regression checked.
