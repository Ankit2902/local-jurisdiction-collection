Boston native footnote ownership candidate

This is an isolated candidate based on reviewed production v12 model
`c568aa07a68a8dc5ae50652fc4b1c164d536b1e90a729b3e49b0ee74df4a6ca4`.
The candidate model is
`015dcba52e415f6e314bf4ed76c397447253221ae5697d20fa8b0a7f3b51c341`.
Production, the original failed Boston v7 run, the original serial queue and all
publisher gate state remain unchanged. No new publisher or government request,
browser, image acquisition/decoding/extraction/rendering/OCR was used.

The original native file is 11,845,430 bytes, SHA256
`33b2fc7d1a2fdaf15f26356adc67a1e038b72892d23438ab45169f7d33c4233c`.
Its publisher job is `b80f966b-b5f1-4b7c-8eee-8b34296a59ad`, native whole HTML,
clientboston, codeboston_ma, edition9b844072-1cfb-4f59-8991-5610c6e2827a
(2026S-2, current through Ordinance2025C14 passed11-5-2025). The exact native job,
byte receipt and independently retained source TOC packets are preserved under
`outputs/collection-readiness-followup-2026-10-17/american-legal/primary-15-boston_ma-v7`.

Boston has one typed `table.footnote` after a literal Notes heading inside the
immediate source section wrapper for owner0-0-0-475, “II.Acts of1948,c452,s3”.
Its three printed note labels are6/7/8. The actual source anchor names are
foot--1/2/3, with reciprocal inline text--1/2/3 targets and hrefs, whose visible
inline labels remain6/7/8. The existing Dallas profile assumed printed labels
matched source-key suffixes and therefore rejected this whole native file.

The bounded change separates the numeric source anchor key from the printed
label. It still requires a unique immediate source owner, Notes heading, typed
footnote cells, unique numeric source keys/printed markers, unique same-section
inline target and reciprocal note/back links. When source key and printed label
differ, every inline link must display exactly the printed note label. Metadata
records the exact label/key binding. Existing matching-label notes keep their
metadata shape. No unowned text or footer is suppressed and no note is moved to
another section or duplicated as a new legal provision.

`replay_full_native.py` confirms the baseline's actual full-native binding failure,
then normalizes the complete retained file with the candidate. It independently
recomputes all2185 inventory nodes and305 source TOC branches. All16251 rich blocks
have unique owners. The two additional fragments are the original Notes heading
and its table, owned exactly once by0-0-0-475; each PlanA/D/E note body occurs once.
An independent original raw-DOM table audit passes44 tables/12250 cells including
text, tags, spans and nested ownership. That audit uses BeautifulSoup independently
of model parsing. An independent inert Chrome audit, if later supplied, is separate
and is not inherited or claimed by this package.

The full-native diagnostic differential removes only the exactly located original
Notes heading and typed table from a projection, so the old baseline can parse the
remaining source. This derived projection is not an acquired source or accepted
final corpus. It has its own hash and exact removed source span in
`projection-witness.json`. Comparing its baseline output with the complete-source
candidate output changes only owner0-0-0-475: HTML/links/auxiliary metadata/notes,
tables/nesting and text/text hash. All other2184 records are equal after the
explicit original-versus-projection source-hash difference is removed. Original
native bytes and all original input files remain byte-identical.

The normalized outputs are `actual-boston-normalization/sections.jsonl` and
`sections.csv`, with source-bound receipt.json. There are zero discovered required
nonimage asset URLs. Images retain exact `[IMAGE]` and source IDs; image references
are intentionally excluded. Two substantive source heading-only units remain
unqualified:0-0-0-10657 (16-A1 LICENSE AND PERMIT DENIAL, REVOCATION OR SUSPENSION)
and0-0-0-4799 (7-13.8.1 Commercial Recycling Requirements for Waste Haulers).
No explicit disposition is present. The original v7 failure also prevented the
closing source refresh. This package proves retained whole-HTML parsing and
inventory/table reconciliation, not whole-publication currentness/completeness.
`publication_complete` remains false.

`offline-suites.json` records156 passing cases:146 existing plus10 Boston cases.
The new portable test uses the bundled exact28,422-byte source group and rejects
missing/ambiguous keys, missing target/backlink, printed-label disagreement,
foreign-owner table placement, unowned operative footer and omitted note ownership
or cells. It checks the matching-label profile and image-only note mutations,
including exact `[IMAGE]`, original body IDs and zero socket/Image.open calls.
All twelve dependency lock pins match the tested shared Python3.12.14 runtime.
The runtime and fixtures were hash-checked unchanged across execution.

To rerun without altering this proof, copy the complete directory to a NEW sibling
under the same project output parent. From the project root:

```sh
study=outputs/collection-readiness-post-1997ee1-2026-10-17/american-legal/boston-native-notes-v1
fresh=outputs/collection-readiness-post-1997ee1-2026-10-17/american-legal/boston-native-notes-REPLAY-FRESH
test ! -e "$fresh"
cp -R "$study" "$fresh"
py=github/local-jurisdiction-collection/.collection-runtime/venv/bin/python
"$py" "$fresh/run_offline_suites.py"
"$py" "$fresh/replay_full_native.py"
```

The156 fixture tests work without Codex or a browser. The full-native replay also
reads the immutable original Boston source/run at its documented project-relative
path; it does not access the network. The direct portable new test is:
`python candidate-source/test_boston_notes.py`.

If root independently approves promotion, the concrete code/test files are
`candidate-source/model.py`, new `test_boston_notes.py`, and new
`fixtures/boston-footnote-source-v1.json`. Append source-bound documentation and
merge history into production validation metadata, then generate a fresh freeze.
Existing source/test receipts and source originals remain preserved. This candidate
performs no production promotion or closing live acquisition.
