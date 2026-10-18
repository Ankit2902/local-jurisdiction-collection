# eCode360 retained acquired-HTML corpus reader — incomplete source

There is no retained real eCode360 whole-publication proof with complete body/document/closing coverage. `gap-audit.json` inventories29real coverage snapshots and2synthetic snapshots. Albany is the strongest available acquired HTML scope:3,253discovered nodes with3,006owned records,53reserved/repealed and194structural dispositions;397content responses,401total rawartifacts. The missing closing sweep and six unqualified required document references block publication completeness. The retainedHTTP403 stop is preserved. Earlier bounded captures (including any134row combined corpus) are not substituted for this source proof. Phoenix municipal.codes remains279inventory/81resolved/73records/198missing with429.

This isolated reader emits all3,006actual Albany canonical HTML records and one disposition for every3,253source nodes, with exactly16corpus fields, original raw/IR bindings, publisher node IDs, source notes/tables,28literal[IMAGE] positions and false source gates. It does not repair legal text, acquire publisher content, clear stops, upgrade evidence, or claim a complete publication. `publication_accepted` is false in reader metadata; missing acceptance keys in original inherited coverage stay null rather than being invented. `serialization_complete:true`/`package_verified:true` are serialization/reconstruction outcomes; `complete:false`, `downstream_ready:false`, expectedexit2 remain explicit.

All3,252nonroot source GUIDs have unique literal `data-position` values. The reader follows those exact publisher positions, corroborates each acquired source TOC DOM sequence and retains the first exact raw/selector witness. The bodyless customer root is only an inventory wrapper. Original ID-sorted IR line ordinals remain in provenance. A narrow standard-libraryHTMLParser reads only these attributes inside#toc; independent BS4comparison across all401rawartifacts found exact position-sequence equality. No numeric GUID/depth hierarchy is inferred. Exact retained own-body parent/path chains are carried; genuinely absent source relationships are not guessed. Explicit printed hierarchy labels populate scalar fields when unambiguous; literal§/SECTION headings provide section numbers; unknown fields remain blank.

`semantic_html` is the sole canonical full_text. History/footnotes already inline are never appended again; original typed notes_html/tables_html are retained in provenance. All24tables and every3006canonical body are preserved exactly through projection. Original source HTML/notes remain immutable evidence. Images are exact[IMAGE] placeholders; no separate images, image members, image decoding, rendering, OCR or browser requests are used. Metadata/image negatives include nested notes and opaque dataMIME references.

## Exact standalone commands

Use Python3.12 on the tested macOSarm64 environment. The shipped reader/writer/verifier use only the Python standard library, demonstrated with `-S` from/tmp. The raw standard-verifier helper and QA scripts additionally use the exact selected collector dependencies in source/requirements.txt (BS4,pypdf,Pillow for source reconstruction and image tripwires). No browser dependency is used by this workflow. POSIXfcntl locking is required; Windows is unqualified.

From this evidence directory, with a configured interpreter assigned to ECODE_PY:

```sh
# Verify the already shipped corpus with site packages disabled.
"$ECODE_PY" -B -S package/packager-source/package.py verify --out package
# Expectedexit2, package_verified:true, serialization_complete:true, complete:false.

# Re-run the ACTUAL standard source verifier, explicitly selecting its hash-pinned
# retained executed source. Fresh disjoint output is mandatory. No collect/adopt.
"$ECODE_PY" -B source/verify_ecode_input.py \
  --input package/evidence/input \
  --collector-root package/evidence/input/executed-source \
  --publication-id albany-ecode-acquired-html --out fresh/source-proof
# Expectedexit0 means raw reconstruction verified; publication_complete:false.
# The equivalent standard collector CLI completeness exit is2.

"$ECODE_PY" -B -S source/package.py package \
  --input package/evidence/input --proof fresh/source-proof/read-only-proof.json \
  --family-verification fresh/source-proof/family-verification.json \
  --reader ecode-html-retained-incomplete-v1 --out fresh/package
# Expectedexit2, sound incomplete corpus serialization.

"$ECODE_PY" -B source/test_ecode_html.py \
  package/evidence/input actual-standard-proof/read-only-proof.json
#14actual-source and refusal tests; no network/process/image decoder calls.
```

Actual initial standard verification used the original retained `albany-image-context-replay-v2` root; exact actual commands are in terminal-summary.json. Its458input files and selected10standard collector modules remained unchanged. Those10modules also match current production hashes at audit time, but the helper still explicitly labels its source choice and does not infer fresh acquisition/current legal currency. The retained standardcommon verification is `publication_acceptance_incomplete`,exit2. Our helper invokes actual engine.verify and records verified:true plus complete:false; it does not replace or weaken that verifier.

## Evidence and integration

`actual-standard-proof/` contains actual full raw reconstruction proof/report under socket/process/base64/PILtripwires. `actual-reader-tests.log` is the final14test result. `stdlib-vs-bs4-all-raw-comparison.json` binds every401raw position comparison. `package/` is the self-contained serialized corpus, input evidence, proofs and nine shipped writer modules. `relocated-shipped-verifier.log` is actual stdlib-only portable verification from/tmp. Final copied root image auditors separately qualify the actual retained normalized/raw source with zero publisher requests.

Only ecode_html.py is the new production-reader candidate. Proposed registry key:ecode-html-retained-incomplete-v1. Proposed existing writer module-manifest addition:ecode_html.py. verify_ecode_input.py is a separate explicit source-verification adapter; test_ecode_html.py and compare_source_positions.py are QA. Root owns common reader dispatch/writer composition; copied common modules here are an exact isolated proof snapshot, not an instruction to overwrite later shared changes. No repository/Git/DB/shared config edits were made.

The first candidate's eager BS4import was rejected during source review. Its source, source-position ledger, manifests and proof logs are retained under attempts/bs4-candidate-v1; redundant regenerated serialized/rawcopies were removed before finalfreeze. The final portable reader is stdlib-only. A first relocated command used a relative interpreter from/tmp and exited127 before Python ran; that launch failure remains under attempts. The corrected absolute interpreter commands executed the real verifier. No failed acquisition or completeness claim is hidden by these operator/tooling corrections.
