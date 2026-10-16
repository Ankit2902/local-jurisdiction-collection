# Code Publishing standalone publisher-export handoff

The current report is **`STANDALONE-VALIDATION.json`**. For Flagstaff, Fremont, San Carlos, Burien and Renton, an ordinary browser operator can use the publisher's Print/Save Selections → HTML download, then run the delivered local importer without Codex, CUA, browser automation, cookies or network access. All five publisher downloads were actually acquired and passed bounded semantic intake/export validation. The validation used supported CUA to operate the ordinary public UI; that is explicitly **UI-assisted validation of a manual operator path**, not unattended acquisition.

Unattended acquisition remains blocked here: all five cookie-free public export-form POSTs returned403 challenge responses. A separate normal headed Playwright/Chromium148 Flagstaff test also returned403; prior isolated installed-Chrome155 chapter tests returned403. No stealth, profile/cookie transfer, CAPTCHA interaction, TLS weakening or repeated challenge attempts were used. The scripts retain these failures and do not parse them as legal exports.

## Verified current downloads and bounded parsing

| City | Actual downloaded scope | Parsed pilot chapters | Verified records |
|---|---|---|---:|
| Flagstaff | City Code → Title1 Administrative | 1-01 | 5 |
| Fremont | Title1 General Provisions | 1.05 and1.15 | 21 |
| San Carlos | Title1 General Provisions | 1.01 | 10 |
| Burien | Title1 General Provisions | 1.01 | 6 |
| Renton | TitleI Administrative | Chapter1 Seal | 1 |

These **43 records** include42 numbered provisions and one substantive Fremont chapter-history body. Fremont Chapter1.15 adds eight actual legal tables with32rows/72data cells/24header cells and134 complete paragraphs across the two selected chapters. Every selected body text and paragraph order, printed section number/order, actual publisher anchor ID, chapter TOC denominator and table/list/cell/span signature is compared against the downloaded source. CSV/JSON and clean/resumed outputs agree. This is a bounded pilot, not full-code extraction or import.

`publisher-downloads/<slug>/publisher-export.html` is the actual downloaded file, not transcribed DOM. Its `download-receipt.json` retains format, actual acquisition times, source URL, selection, bytes/SHA256, source module version and assistance classification. The file itself includes publisher currency: header attributes plus footer for four cities, footer for Flagstaff. Expected currency is pinned independently from earlier validated publisher markers in `operator-pilot-jobs.json`. The importer rejects missing/mixed/unexpected currency, wrong publication name, raw mutation, scope mismatch or missing legal layout. Downloaded scope can be larger than parsed scope; unparsed chapters and image assets remain outside the pilot qualification.

The existing E2E reports, `CODE-FREEZE.json`, old test logs, `historical/`, `current-cua/`, `current-pipeline/`, `README-V1.md`, `BASELINE-E2E-README.md` and `BASELINE-E2E-PACKAGE-SHA256.json` are **copied baseline evidence**. They refer to the earlier sealed package/parser1.1 and do not describe the new parser1.2 or certify this new package's current bytes. The original sealed E2E directory was untouched. The new `STANDALONE-CODE-FREEZE.json` and `PACKAGE-SHA256.json` bind this delivery.

## Install and reproduce the browser-free pilots

Python3.9+ and the two pinned Python dependencies are sufficient for local intake. No repository/cache path, Codex host, browser, Node or credential is needed. Use a normal OpenSSL-supported Python for optional live HTTP probing; the validation environment's Python3.9/LibreSSL warning is retained, with certificate checks enabled.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_publisher_pilots.py --out work/publisher-pilots
.venv/bin/python -m unittest discover -s . -p 'test_*.py' -v
.venv/bin/python verify_package.py
```

Windows uses `.venv\Scripts\python.exe`. Each pilot invokes the delivered importer and parser CLI using recorded argv/returncodes/stdout/stderr. `publisher-intake-final/<slug>/export/` contains the reviewed16-column BOM CSV, JSON fulltext/TOC, publication exports, original inputs, source-node/disposition/provenance sidecars and manifest. `source-lineage.json` binds the immutable original publisher file to explicit copied chapter ranges; neither source text nor publisher anchor IDs are rewritten. The importer processes at most three selected chapters and never silently broadens the request.

The observed new export-format issue was fixed in parser1.2: downloaded HTML uses child `<a id="a1x05x010">` inside headings. The parser now retains that actual ID and distinguishes it from `<a name>`. It previously recognized heading IDs and named child anchors only. No other parser changes were made in this phase.

## Manual publisher download, without Codex

The publisher's [current public help](https://www.codepublishing.com/help.html) describes selecting titles/chapters/sections, opening Print/Save Selections, choosing a format and saving. The following controls were exercised for all five cities:

1. Open the city's publication root in an ordinary browser. For Flagstaff, use the left Table of Contents frame and expand **City Code** using its plus sign; leave Charter and Employee Handbook outside this selection.
2. Check **Title1 General Provisions** (Fremont, San Carlos, Burien), **TitleI Administrative** (Renton), or **Title1 Administrative** under City Code (Flagstaff). You can instead expand a title and select individual needed chapters for a later qualified run.
3. Click **Print/Save Selections**. A **Print Preview** popup opens at the city's `/cgi/menuCompile.pl` path. Allow that ordinary publisher popup if the browser blocks popups.
4. In the format dropdown, change **RTF (Microsoft Word)** to **HTML**. Click **Save** and retain the downloaded HTML file. Do not substitute the preview page, a browser “Save Page” shell or a challenge response.
5. Record the actual download time with timezone, publication URL, selected scope and publisher currency shown in the export. Keep the original file unchanged.

Register the acquired file locally. This records an **operator attestation** of acquisition, not independently verified network provenance:

```sh
.venv/bin/python register_manual_export.py \
  --file /path/to/downloaded.html --slug fremont-ca \
  --source-url https://www.codepublishing.com/CA/Fremont/cgi/menuCompile.pl \
  --selection 'Title 1 GENERAL PROVISIONS' \
  --retrieved-at 'ACTUAL-ISO8601-TIME-WITH-TIMEZONE' \
  --out work/fremont-download
```

Then supply the expected currency explicitly, copied from the publisher edition you intend to process:

```sh
.venv/bin/python import_publisher_export.py \
  --receipt work/fremont-download/download-receipt.json \
  --chapter 1.05 --chapter 1.15 \
  --expected-currency 'The Fremont Municipal Code is current through Ordinance 02-2026, passed May 5, 2026.' \
  --out work/fremont-import
```

Use fresh output directories; existing acquisitions/intakes cannot be overwritten. The chapter selector uses the actual exported chapter heading number. The demonstrated selection layouts are these five Title1/I files; other publisher formats/layouts, final-chapter footer boundaries or missing locators fail closed for explicit qualification. The full export is retained even when only selected chapter ranges are parsed. No current corpus completeness is inferred from a title export.

## Acquisition evidence and remaining prerequisites

`publisher_export.py` derives endpoint, selected value and submit fields from hash-verified, retained actual publisher forms and makes one ordinary cookie-free request per city, without redirects/retries. `public-export-probes/` contains exact failed responses, headers, script revisions and receipts. It is delivered for normal supported environments; a403 stops qualification. The shared independent headed-browser diagnostic is linked from the report; its successful Gridics controls show the Code Publishing result was not a global browser/TLS failure, without identifying a precise publisher policy cause.

`retain_publisher_download.mjs` is the executed UI-assisted acquisition helper. It uses documented CUA selection/download APIs, arms the download event before clicking Save, then retains the actual downloaded file outside browser evaluation. It does not export browser state or cookies. The manual runbook above replaces that helper entirely for a Codex-free operator. `operator-export-cua/` records observed source menus/roots; the offline importer depends only on downloaded files and receipts.

No complete current municipal code hosted by a city was found in the bounded official-site review. Fremont's official page delegates online publication; Flagstaff's complete former land-development-code PDFs are explicitly repealed, and its procurement manual is partial. These are not substituted for current whole-code editions. Alternate-copy findings are recorded separately from the successful publisher export path.

A fully unattended fresh download requires a normal publisher-supported network/browser environment that permits the request, or a documented sanctioned export integration. Until that prerequisite is met, the qualified route is **operator download, unattended local verification and parsing**. No publisher authorization, account or payment was requested or assumed. Further title/family inventory, unlinked status nodes, uncodified ordinances, incorporated documents, images and coherent whole-corpus version checks remain outside this pilot.
