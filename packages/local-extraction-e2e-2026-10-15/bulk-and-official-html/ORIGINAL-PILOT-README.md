# Bulk XML and official HTML validation pilots

This isolated package delivers runnable parsers, bounded acquisition commands, retained October 15, 2026 source evidence, and focused regressions for San Mateo, King County, and Daly City. It does **not** authorize a full collection or represent a completed jurisdiction corpus. No production adapters, registries, or database data were changed.

Daly City's live official link now goes to Municode. The active local module follows that replacement. The eLaws branch is historical, with source-heading repair and shell rejection tested offline; its currency and official designation were not confirmed.

## Portable environment and commands

Use Python 3.9 or newer (3.11+ recommended) with normal TLS certificate verification. There are no project-checkout imports, bundled browser binaries, `/tmp` environments, or hard-coded user paths required at runtime. The validation run used Python 3.9, Beautiful Soup 4.15.0, and Requests 2.32.5. Install exactly the declared versions in a fresh virtual environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s . -p test_methods.py -v
.venv/bin/python validate.py
```

Run these commands from this directory. `validate.py` uses retained evidence only, runs the regression suite, rebuilds small sample packages, and writes one `VALIDATION-REPORT.json` per jurisdiction plus a top-level report. It parses retained representative documents to inspect section boundaries, but exports only selected King County and Daly City provisions. San Mateo's retained Title 1 and Charter are small standalone sample documents. No whole-jurisdiction extraction occurs.

Rebuild into an arbitrary output directory, including one outside this bundle:

```sh
.venv/bin/python validate.py --out /tmp/complisolv-three-methods-replay
```

The command copies retained source evidence into that output and each sample embeds its own raw source bytes. Output paths and source locators remain portable. `samples/<document>/` is a standalone bounded package with the 16-column JSON/CSV envelopes, blank-fulltext compatibility TOC, node dispositions, provenance, copied raw bytes, and run manifest. The independent jurisdiction inventory sits above those samples and is distinct from derived output TOCs. This layout intentionally describes validation samples, not a full OUTPUT-CONTRACT jurisdiction package.

## Individual replay CLIs

San Mateo uses an explicit 40-character immutable commit. The validation snapshot is `16cc1931d1714f5915319dd98d7640207f4ce76b`; this is a repository version, not a legal current-through date.

```sh
.venv/bin/python san_mateo.py parse --input raw/san-title1.bin --source-url https://raw.githubusercontent.com/cityofsanmateo/law-xml/16cc1931d1714f5915319dd98d7640207f4ce76b/us/ca/cities/san-mateo/code/1.xml --commit 16cc1931d1714f5915319dd98d7640207f4ce76b --scrape-date 2026-10-15 --out /tmp/complisolv-san-mateo-replay
.venv/bin/python san_mateo.py parse --input raw/san-charter.bin --source-url https://raw.githubusercontent.com/cityofsanmateo/law-xml/16cc1931d1714f5915319dd98d7640207f4ce76b/us/ca/cities/san-mateo/charter/index.xml --commit 16cc1931d1714f5915319dd98d7640207f4ce76b --publication charter --scrape-date 2026-10-15 --out /tmp/complisolv-san-mateo-charter-replay
```

The San Mateo CLI accepts an acquisition/replay date. Library functions in all three modules accept `scrape_date`; their default is the date of execution. `validate.py` binds its saved evidence to October 15, 2026 explicitly.

```sh
.venv/bin/python king_county.py --input raw/king-title1.dom.html --source-url https://aqua.kingcounty.gov/council/clerk/code/04_Title_1.htm --out /tmp/complisolv-king-title1-replay
.venv/bin/python king_county.py --input raw/king-charter.dom.html --source-url https://aqua.kingcounty.gov/council/clerk/code/03_Charter.htm --charter --out /tmp/complisolv-king-charter-replay
.venv/bin/python daly_city.py parse --toc raw/daly-toc.json --content raw/daly-content-0.json --node-id TIT1GEPR_CH1.01COAD_1.01.010AD --out /tmp/complisolv-daly-adoption-replay
```

These document CLIs replay the explicitly supplied document. They are not multi-title/full-jurisdiction collectors. The Daly parser emits only the requested actual node even when the API returns a chapter bundle.

## Bounded network acquisition

San Mateo's publisher requests bulk downloads instead of page scraping. The live official Law Library route and repository `index.xml` both identify `cityofsanmateo/law-xml`. Acquisition is confined to that designated repository. The recursive Git tree supplies complete file membership with `truncated=false`; it reveals Code, Charter, drafting manual, editorial actions, and ordinances. Root/code-index include references are reconciled against that frozen tree. The XML serializer retains direct text, numbered paragraphs, table cells/spans, history attributes, and nested structural sections independently. XML child-index locators and retained original XML bind records to exact source nodes.

```sh
.venv/bin/python san_mateo.py acquire --commit 16cc1931d1714f5915319dd98d7640207f4ce76b --out /tmp/complisolv-san-mateo-bulk
```

Add `--archive` to retain the complete publisher ZIP archive and its response/hash receipt without parsing the full corpus. That archive command is implemented but was not executed during this bounded validation. Sample source XML files were acquired from immutable `raw.githubusercontent.com` paths in the same designated repository. General include expansion and XML/HTML parity remain integration gates.

Daly City's official homepage links its Municode ordinance bank; the publisher's observed **Browse codes** link leads to the active codified publication. The established public Municode endpoints resolve CA client 1857 and Code of Ordinances product 16311. The `acquire` command validates those identities, retains the complete TOC and publications response, and limits content acquisition to at most four explicitly supplied TOC node IDs.

```sh
.venv/bin/python daly_city.py acquire --out /tmp/complisolv-daly-live --node-id TIT1GEPR_CH1.01COAD_1.01.010AD --node-id TIT15BUCO_CH15.08BUCO_15.08.080TA1505.1MIROCOCLTYCOME
```

All Requests acquisition uses verified TLS, cache URL/hash binding, strict non-200 rejection, and bounded retries for 429/503. A fresh output directory means a new acquisition. An existing cache is immutable, not a check of current online currency. For moving versions, freeze publication metadata and compare TOC/version markers at the beginning and end before a full run. No workaround for denial, challenge, or expired certificates is provided.

King County's direct HTTP request returned 403 while the supported in-app browser loaded its official landing, Title 1, Title 2A, Title 21A, and Charter. This package therefore qualifies parsing from retained browser DOMs, and does not claim a standalone Requests transport can acquire King County in this environment. The original response bytes/encoding and official Word/PDF parity remain unqualified.

Browser DOMs were captured through the supported Codex CUA session. `capture_cua.js` supplies the reusable capture function for a previously authorized/observed tab; it is a CUA snippet, not an independent Node browser client. It reads DOM chunks, checks length/end markers, and writes metadata. Large browser results are capped at around 200,000 characters, so a single `outerHTML` result must not be trusted for a large title. Failed initial capped captures remain as `.truncated` evidence and are excluded from parser inputs. The parser rejects `[Truncated]` explicitly.

## Validation and remaining gates

`TEST-RESULTS.txt` records synthetic regressions separately from retained live-source checks. The suite covers the King County R05 omission, real anchors without invented fragments, alphanumeric and split bold headings, Charter preamble/subsections, CP1252/UTF8 decoding, error/truncation rejection, XML parent/nested bodies and history, table spans, image ordering, duplicate source identities, exact Municode requested nodes, CSV/JSON agreement, portable raw retention, and interrupted/resumed real XML replay equivalence with version/config/raw binding.

`full_text` retains paragraphs and enumeration labels as readable text. Tables remain semantic HTML in that field to preserve rows, cell relationships and spans; superscript/subscript retain inline tags. Full semantic HTML and original XML remain in provenance. Downstream consumers must preserve those supported structural fragments rather than flattening them.

Each jurisdiction report lists evidence paths/hashes, live source scope, exported sample counts, and unresolved issues. Automated extraction and agent source inspection are recorded; no human legal/source acceptance is asserted. The reports explicitly retain King County TOC/body discrepancies and the Charter landing/document date discrepancy. They do not classify such differences as definitive extraction omissions. Other title variants, container/editorial bodies, images and full-node reconciliation remain required before a full run.

Use `python verify_hashes.py` after packaging to verify `ARTIFACT-HASHES.json`. Rebuilding reports or outputs changes hashes; regenerate the manifest with `python verify_hashes.py --write` after deliberate changes.
