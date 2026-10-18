# Independent final municipal.codes reader peer

This append-only peer supplements the immutable source audit in `../SOURCE-AUDIT-MANIFEST.json` (61c225bd41921caa195dcde5c41c5e6e733423407fbcbbe7c4e478415d79146e). Original source audit files were not changed. No new publisher request, source acquisition, full collector normalization, PDF parsing or image operation occurred.

The final reviewed candidate is `../../../municipal-corpus-reader-v1/CANDIDATE-MANIFEST.json`, cb83300f9d12ae6e18b779c906db17cc511974ca9a5b562c8770a400b1211e0f. Only its selected 181 files are the frozen producer packet; the final package is package-v3, with 105 files and 73 unchanged source inputs. Earlier package attempts are historical, not promoted proof.

The source audit independently compared every original acquired typed article to rich and canonical HTML with all DOM tags/attributes and ordered text, rather than applying the producer's stripping selectors. All 73 acquired body records, 235 IDs, 32 body links, 3 notes and 159 subsection nodes pass. The independent source inventory is 277 literal TOC entries plus the publication root and explicit preface. It reconciles all 279 nodes: 73 included, 8 structural (seven source-empty articles plus the bodyless root), and 198 explicitly unresolved. No acquired source tables or images exist. Unacquired nodes remain unknown. Text outside typed articles is independently classified as source TOC navigation, the contents heading or explicit source UI, with no unclassified legal text.

`literal-text-review.json` adds word-boundary fidelity: all 73 decoded source bodies match both canonical and rich text after only whitespace collapse, and 72 are literal decoded-text equal. The single remaining raw formatting difference is nine leading newlines at Chapter VIII after descendant removal; no word, punctuation, codepoint or note discrepancy is waived. No browser is needed because original and canonical body DOMs also match.

`audit_package.py` imports no reader or producer. It independently recomputes all 73 × 16 row fields, literal source TOC/frontmatter order and parent chains, all 279 inventory dispositions, all 73 exact original heading slices/raw hashes, CSV/BOM/JSON/TOC pairs, and source/proof bindings. All three heading footnote anchors VI/VIII/X are now available to an ordinary consumer in `record-provenance.jsonl` fields `source_heading_html` and `source_heading_links`. Their exact source href, target ID, raw heading hash and same-owner target hash are preserved. All three note bodies remain once in canonical full_text; no duplicate legal body was appended.

The final source uses LF-only offsets. Twenty-two author reader tests were independently rerun, plus six helper-preflight tests and seven independent bounded controls covering U+2028/U+0085/RS/CR exact slicing, opaque image source, typed image-anchor caption and redacted payload, and picture/table image slots. Socket/process/base64/PIL decoder tripwires stayed untouched. Final runtime reader is stdlib-only; Pillow is used only to install the negative decoder tripwire in tests.

`verify_relocated.py` copies the exact package into an unrelated temporary directory and runs the shipped ordinary no-B entrypoint with `-S`, using socket/process/decoder/import guards. It returns the intended exit 2 with package_verified=true and complete=false. All 105 original/copied files remain byte-identical and no __pycache__ is created. It regenerates the portable projection from retained IR/raw heading/TOC witnesses; it does not run the collector's source normalization or native PDF parser.

The package retains the literal source currency (current through November 6, 2018 election), no closing inventory, 198 missing nodes, the authoritative 429, edition/text/attachment/jurisdiction incompleteness, and state_source_verified=false. Package serialization/reconstruction are qualified within the retained partial scope. Selected publication, whole-publication and jurisdiction readiness are not inferred. Synthetic complete controls do not upgrade this real acquisition.

Compact replay from the project root:

```
github/local-jurisdiction-collection/.collection-runtime/venv/bin/python -B outputs/collection-readiness-post9ef7220-2026-10-17/american-legal/municipal-source-independent-v1/final-reader-review/audit_package.py
github/local-jurisdiction-collection/.collection-runtime/venv/bin/python -B outputs/collection-readiness-post9ef7220-2026-10-17/american-legal/municipal-source-independent-v1/final-reader-review/verify_relocated.py
```

These commands require the retained original/candidate trees at their documented paths; the shipped producer package itself has a source-independent relocated verifier. No production, Git, gate state, original source or sealed packet was edited by this peer.
