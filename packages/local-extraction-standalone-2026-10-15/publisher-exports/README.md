# Publisher export findings and local intake

This package independently verifies bounded publisher downloads and documents the export facilities observed across 24 current routes: eCode360 (14), legacy Code Publishing (5), and municipal.codes (5). `EXPORT-FINDINGS.json` is the status matrix. Evidence was collected on October 15, 2026. The Code Publishing sibling final report qualifies all five operator-assisted HTML downloads and 43 bounded parsed records; this helper independently inspects Fremont. The family packages contain the acquisition adapters; this package supplies a portable local intake CLI and independent source comparisons.

Two actual unattended municipal.codes HTML downloads, Berkeley and Everett section 1.01.010, passed signature, hash, jurisdiction/citation-marker and source-notice checks. The ordinary headed browser used the public **Save → Web Page (HTML)** control and captured a download event. Direct navigation to the same advertised export URL did not qualify. Fremont Title 1 was obtained through an ordinary connected browser and passed independent intake: 73 section headings/locators and eight legal tables. That receipt is **operator-assisted**. The earlier Berkeley operator download is retained separately even though its bytes match the later unattended download.

No whole-code export, full-corpus acquisition, or production import was performed. Two municipal.codes section samples contain no tables. The Fremont sample exercises table preservation; only its first table received a visual row comparison. All eight tables retain cell text, spans and source HTML. The other seven still require individual review before relying on their layout or meaning.

## Install and run locally

Python 3.10+ is recommended. The intake tool needs no Codex service, browser or logged-in session:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s . -p 'test_*.py' -v
```

Run from this package directory. The 16 tests include the retained one-page publisher feature chart PDF, corrupt PDF rejection, sparse/scanned-page review classification, challenge/login HTML rejection, disguised file types, table spans, provenance requirements, missing markers, hash mismatch and overwrite protection. Legal definitions containing authentication/access-denial language remain intact.

A completely local replay of the real Fremont download:

```sh
.venv/bin/python export_intake.py \
  --file verified/fremont-title1/4dbe06350386e7ed8602e004278fea04598db5c3d17dbf621f83f8a9ad7fdc3b.html \
  --provenance verified/fremont-title1/provenance.json \
  --format html \
  --sha256 4dbe06350386e7ed8602e004278fea04598db5c3d17dbf621f83f8a9ad7fdc3b \
  --expect 'Fremont Municipal Code' --expect '1.05.010' --expect '1.30.050' \
  --expect 'Title of Officer' --out /tmp/fremont-export-recheck
```

Use a new or empty output directory. It writes a byte-identical content-addressed original, `sample.txt` and `verification.json`. Acquisition provenance comes from the supplied JSON and must be checked against an actual external receipt. A valid file alone cannot qualify an acquisition method end to end. Marker matches and file integrity remain distinct from legal completeness.

For the fresh standalone Berkeley sample, use `verified/berkeley-ca-standalone/fd702af295060ff2c31a28508ca908c01985cf929f84e09740f63a16ef877c7c.html` and its adjacent `provenance.json`, with `--expect 'Berkeley Municipal Code' --expect '1.01.010'`. For Everett use `verified/everett-wa-standalone/68072312db8eb594a55b15f73f6f746bbaeac0fba3a121ed7760f5b5705c51df.html` and its provenance, with `--expect 'Everett Municipal Code' --expect '1.01.010'`.

For a PDF, specify `--format pdf --pages 1,3,10` and expected jurisdiction/citation text. At most 20 explicitly selected pages are parsed; the default is first and last page. Sparse text or scanned selected pages require OCR/visual review and return exit 2. Mixed image/text pages retain an explicit visual-review gate. PDF extraction retains layout text and detected table cells; it does not remove running headers or certify multi-page section assembly. RTF is identified and preserved, but requires a reviewed converter and returns exit 2. ZIP/DOCX, unsupported binary files, missing text markers and invalid PDFs are rejected or explicitly unqualified. Input is bounded to 30 MiB. HTML is parsed without executing scripts or fetching assets.

Exit 0 means integrity and specified text samples passed. Exit 2 means the file was retained but text qualification needs review (including omitted markers or unsupported RTF parsing). Exit 1 means rejection. Every accepted file retains `legal_semantic_status=MANUAL_REVIEW_REQUIRED`, `scope_completeness_status=NOT_PROVEN`, and `method_e2e_status=NOT_QUALIFIED_BY_FILE_INTAKE_ALONE`.

## Actual publisher facilities and operator steps

| Publisher | Observed facility | Scope and restrictions | Validated outcome here |
|---|---|---|---|
| eCode360, 14 routes | Select content checkboxes; **Print selected content**, **Download selected content** | Official toolbar help describes PDF/Word; options depend on code and login. Current subscription page lists limited public PDF access and $195/year professional access to full PDF/Word. Foster City DOM marks PDF login required, Word permission false. Twelve retained legal subtrees omit body flags; those permissions are unknown. | No publisher export acquired. Initial standalone probes returned 403; Santa Rosa 429 stopped further host probes. Foster City public DOM became readable after passive browser verification, so initial 403 does not prove permanent unavailability. |
| Code Publishing, 5 routes | `form#saveForm`, **Print/Save Selections**, `POST …/cgi/menuCompile.pl` | Checkboxes named `code` select observed title/chapter/section paths. The observed Fremont preview offers RTF, PDF, MOBI, EPUB, HTML and plain text through select[name=type] and Save. This helper independently inspected Fremont; the sibling Code Publishing final report qualifies actual public HTML downloads and bounded standalone semantic imports for all five. | Fremont independent intake passed; sibling family qualifies all five operator HTML downloads and 43 parsed records. Ordinary cookie-free HTTP POSTs returned 403 on all five. |
| municipal.codes, 5 routes | **Save, Share, Bookmark or Print** → Share Section dialog → **Save** tab | Advertises Adobe Reader (PDF), Microsoft Word (RTF), Web Page (HTML), Plain Text, and Print. Exact observed per-section URLs are in `evidence/upstream/municipal-observed-export-plan.json`. | Berkeley and Everett unattended ordinary headed browser Save-UI HTML downloads passed independent intake. Other three cities' export dialogs were observed; no export-file intake for them here. |

For an ordinary operator download, open the current publication and record its current-through notice and selected IDs before saving. Use the publisher's Download/Save format control, retain the resulting file and capture time/selection/source URL, then run `export_intake.py` with a provenance JSON like the retained examples. A browser's **Print → Save as PDF** creates a browser-print artifact and must be labeled `artifact_kind=browser-print`; it cannot be described as a publisher PDF download. eCode360's Print button creates a publisher print preview, which is a separate category from both its Download button and browser print.

For unattended municipal.codes acquisition, see the sibling `municipal-codes/standalone_ui_export.mjs` (or the exact executed script linked by its current report). Use the observed `/…/1.01.010/share` entry, wait for the dialog, select Save, and click Web Page (HTML) while listening for the browser download. The successful receipts record Node v24.19.0, Chrome 155.0.8059.41 and the executed acquisition script hash. A `blob:` download URL is temporary session output; replay the public UI flow rather than caching that URL. The five-city family report remains authoritative for runtime qualification beyond the two files independently inspected here.

The documented eCode360 REST API at <https://developer.ecode360.com/> requires municipality-issued `api-key` and `api-secret` headers. Its TOC endpoint returns structure; its content endpoint returns content objects with nested children, images and attachments. It is a documented credentials-required alternative, untested here. No keys were requested or supplied, accounts created, subscriptions purchased, or authentication controls bypassed.

## Visual checks and evidence

`evidence/visual-qa.json` records exact source spot checks. Offline source screenshots cover Fremont's first legal table and currentness notice, the entire short Berkeley section and Everett section. Both section exports retain legal text, history, references, currentness and clerk disclaimer. Berkeley's section export has a parent-chapter HTML title; its legal body contains only section 1.01.010. Title/canonical metadata alone cannot establish chapter coverage.

The eCode360 feature chart PDF was downloaded over verified HTTPS, rendered with Poppler and inspected. It visibly dates from May 26, 2020 and is documentation rather than a current legal-code export. The package-dependent public PDF footnote is preserved. Current help/FAQ/API facts are attributed to primary publisher pages in the findings; direct ordinary HTTP attempts to those help pages returned 403, while the off-host subscription page and chart PDF returned 200.

Optional offline HTML rendering requires Playwright plus an installed browser:

```sh
.venv/bin/python -m pip install playwright
.venv/bin/python -m playwright install chromium
.venv/bin/python render_html_sample.py --channel chromium \
  --file verified/fremont-title1/4dbe06350386e7ed8602e004278fea04598db5c3d17dbf621f83f8a9ad7fdc3b.html \
  --out /tmp/fremont-visual-recheck
```

`--channel chromium` uses the Playwright-installed Chromium (default). `--channel chrome` explicitly selects installed Google Chrome; `--executable-path /absolute/path/to/browser` records and uses a supplied executable. Validation here used installed `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`, Chrome 155.0.8059.41, Python Playwright 1.64.0. Rendering disables JavaScript and blocks all network requests. Use `--body` only for a short section; without it, the renderer captures the first table and `#current` notice. These screenshots are offline QA artifacts, not acquisition or publisher exports.

`capture_docs.py` is retained as the exact executed bounded documentation-capture script. It is not a production crawler or throttle-aware acquisition adapter. Do not rerun it during this publisher throttle: it includes ecode360.com URLs and does not automatically stop the distinct-document queue on429. Future reuse needs an explicit throttle review/guard; this package made no additional eCode360 host requests after the stop instruction. The saved receipts distinguish 200 documentation files from 403 challenge HTML. Primary URLs are listed in `EXPORT-FINDINGS.json`.

Whole-code exports remain untested. Before relying on a larger selection, validate selected IDs against the current inventory, verify first/last sections and all children, reconcile current-through notices and separately listed new laws, inspect tables/images/footnotes, and retain a fresh acquisition receipt. Everett's standalone file notice matches a separately retained earlier October 15 CUA capture; its new share DOM was a loading shell, so the report does not claim a fresh before/after inventory comparison for that standalone run.
