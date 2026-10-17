# Official source validation — 17 October 2026

This relocatable package validates bounded live acquisition for Portland OR, Baltimore City MD, and Milwaukee WI. It is a method validation, not a complete jurisdiction corpus. No database or prior sealed outputs were changed.

## Findings

| Jurisdiction | Tested live route | Normalized scope | Conservative status |
|---|---|---|---|
| Portland | Python HTTPS downloads of official full-title HTML and a native zoning chapter PDF | 77 legal sections across Titles 1 and 18; 3 HTML tables; Chapter33.10 retained as 4 PDF page records with 1 geometric table | `standalone_e2e_pass` for bounded HTML sample |
| Baltimore City | Official hub's recommended GitHub HTML bulk ZIP, publication/2026-09-28 | 536 legal/table records: Article1 (442 sections), zoning Title4 (39 sections), Charter ArticleI (19 sections), zoning table headings (36 records containing37 tables); 67 HTML tables total | `standalone_e2e_pass` for bounded normalized sample; full bulk archive downloaded |
| Milwaukee | Ordinary headed Playwright + installed Chrome, native download from official TOC link | Complete published CH295-sub5.pdf (35 pages), 3 section text records (295-501,503,505), 35 separate page records; 17 geometric table fragments | `standalone_partial` because rotated table headers/figures need further normalization |

All three `complete_corpus` flags are false. A complete downloaded archive or chapter is distinct from complete, fully verified jurisdiction ingestion. PDF page records are never counted as additional legal sections.

## Run after relocation

Requires Python3.12+ and standard internet access for live acquisition. Offline replay needs only retained files and the Python dependencies:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python verify_offline.py
```

`verify_offline.py` checks script/package hashes from `run_manifest.json`, verifies each retained raw body against its acquisition metadata, replays into a temporary directory, and compares every normalized output byte-for-byte. It never opens a network connection. An independent replay can also be kept:

```sh
.venv/bin/python validate.py --offline --out replay
```

Live HTML/bulk acquisition is independent of Codex:

```sh
.venv/bin/python acquire.py --only portland_index portland_title1 portland_title18 portland_zoning portland_charter_index portland_charter portland_zoning_ch10
.venv/bin/python acquire.py --only baltimore_index baltimore_repo baltimore_html_bulk
.venv/bin/python validate.py --offline --out parsed
```

The Baltimore ZIP URL is pinned to the observed default publication branch. Before a later-current acquisition, inspect `raw/baltimore_repo.json` or GitHub's repository metadata and update the branch if it changed; a pinned branch does not claim future currency. The package retains the complete ZIP without executing its bundled executable/server files or extracting untrusted paths.

For Milwaukee, install Node.js, Playwright, and ordinary Google Chrome. No Codex browser, profile, cookies, CLI, or runtime dependency is required:

```sh
npm install
node milwaukee_browser.cjs
node milwaukee_native_download.cjs
.venv/bin/python validate.py --offline --out parsed
```

`milwaukee_browser.cjs` captures the complete official TOC HTML and its linked publication inventory. Its diagnostic browser-context HTTP PDF request receives403. `milwaukee_native_download.cjs` uses an isolated temporary Chrome profile with the ordinary “download PDFs” preference and clicks the published Residential Districts link. The native PDF download succeeds. It removes only its own temporary profile after completion. No authentication, CAPTCHA solving, challenge interaction, proxy, cookie transfer, or fingerprint changes are used. The direct HTTP/request API path and actual browser navigation behave differently on this host.

`milwaukee_navigation.cjs` is the retained diagnostic navigation script: it observed Chrome's PDF viewer shell but did not download a PDF. That shell and its blank initial screenshot are not evidence of parsed content. `raw/milwaukee_residential_native.pdf` is the actual substantive native export. The retained403 response at `raw/milwaukee_zoning_browser.pdf` is HTML, not a PDF; its metadata explicitly records403 and content-type text/html. Do not import it as a code PDF.

Acquisitions are serial with at least3 seconds between Python requests. There are no automatic retries. A429 ends the Python run. Future operators must honor Retry-After and stop on challenges instead of repeating blocked attempts. Do not invoke the blocked Milwaukee HTTP entries as an automated retry loop.

## Publication inventories and limits

- **Portland:** `parsed/portland_inventory.json` records all34 titles linked by the official City Code index (1–35, with8 absent), all15 charter chapters, and the official policy/map routes. Title33 Planning and Zoning uses separate chapter PDFs and a full printable eFiles publication; this is a separate acquisition format from ordinary `/code/{title}/all` HTML. The zoning page currently advertises a full printable version effective July1,2026 and also lists upcoming changes, including November1,2026. This package tests only Chapter33.10, whose pages show their own revision dates; it does not claim that unincorporated future-effective changes are in force. Charter bodies, other code titles, policies, zoning maps, and full Title33 were not ingested.
- **Baltimore City:** the official hub expressly asks visitors not to scrape and links bulk HTML/XML on the Department of Legislative Reference's GitHub. This package follows the recommended bulk route. The current observed HTML default branch is publication/2026-09-28. `parsed/baltimore_inventory.json` retains the archive path list, family links, code article/building-code links, and selected members. Families include Baltimore Charter, Baltimore Code (including Article32 zoning and building codes), Baltimore Regulations, Public Local Laws, Council Rules, Administrative Manual, Ordinances, Resolutions, and linked state legislative materials. The raw bulk archive is complete as delivered by GitHub, but only four full-document members were segmented. Not every publication, amendment, hyperlink target, attachment, historical version, or effective-date relationship was validated.
- **Milwaukee:** the official TOC separately publishes City Charter, Volume1 Regulatory Ordinances, Volume2 Building and Zoning Code, Volume3 Administrative Ordinances, Salary Ordinance, and Positions Ordinance. Volume2 has split chapters200 and295; the TOC explicitly labels those chapter TOCs as not full text. Whole-volume links point to native Master-V1.pdf, Master-V2.pdf, Master-V3.pdf and Master-Charter.pdf. `parsed/milwaukee_inventory.json` preserves the official publication URLs and all TOC download links. Only Chapter295 Subchapter5 Residential Districts was downloaded, not all of Volume2 or any other volume/family. Full-volume link availability does not prove standalone successful acquisition of each volume.

## Parsing and quality evidence

HTML records preserve source identifiers, hierarchy, headings, legal citations, absolute URLs, amendment notes where supplied, raw reference, body HTML, cross-reference links, and each table's cells/rowspan/colspan. CSV is a text index; JSONL carries structured tables and HTML. Baltimore's quoted editor-note section with an empty ID is deliberately not treated as a separate legal section. The36 zoning table-heading records contain37 actual HTML table elements. `baltimore_crossref_checks.json` checks whether selected internal legal links have corresponding archive members, with absent targets reported rather than silently declared valid; fragments are not validated.

PDF outputs preserve physical page citations and geometry table cells. Milwaukee section text segmentation uses explicit section-start lines and removes the observed running header/footer margins. It identifies295-501,295-503,295-505; tables and figures remain attached to page evidence, not falsely reconstructed into a fully semantic section table model. PDF table_count is **page-level geometric fragments**, not unique logical tables. Images, illustrations, merged header meanings, and reading order have not been exhaustively normalized.

Read-only PDF layout QA followed the PDF skill. Retained renders inspected: Portland zoning Chapter33.10 page1 (headings), page3 (two-column designation/symbol table), and Milwaukee Residential Districts pages1,2,4. The Milwaukee page4 table has rotated zone labels, which plain PDF text mangles. Its body row “General office” was independently compared to the visible PDF: N,L,N,L,L,N,L,Y,Y, and replay asserts those nine cells. This demonstrates a substantive table row while explicitly leaving header reconstruction incomplete. The official source PDFs remain authoritative for layout.

`parsed/verification.json` reports counts and assertions. `raw/*.meta.json` records URLs, times, byte counts, hashes, statuses when exposed, and headers. Native browser download metadata has PDF signature/hash evidence without inventing an HTTP response status. `run_manifest.json` records commands, runtimes, hashes of final scripts, and parsed-output hashes. Diagnostic failures remain available. No parser text from403 pages enters normalized code records.
