# Official alternatives for the 24 standalone publisher gaps

`OFFICIAL-ALTERNATIVES.json` covers all 24 jurisdictions in the sealed E2E source matrix: 14 eCode360, five Code Publishing and five municipal.codes jurisdictions. This is a bounded search for practical official downloads and first-party text. **No complete current Municipal Code gap was closed by this alternatives work.** A separate Charter result does not qualify the rest of its jurisdiction's Municipal Code.

The useful positive results are:

- **Emeryville Charter:** the official city website embeds its entire small eight-section Charter. A fresh standalone HTTP acquisition, source inventory and bounded two-section JSON/CSV export pass through `qualify_charter.py`. The city page presents the Charter adopted in 2014; it does not supply a current-through amendment marker.
- **Santa Clara Charter:** the official June 2026 Legistar item separately labels the current Charter and proposed revisions. Its current attachment downloads through ordinary verified HTTPS: 29 pages, 10,200,857 bytes. Rendered first/last pages show the June 5, 2026 snapshot, Title CHA and Article XVIII. Selected pages contain no extractable text, so this is **download qualified; OCR still required**, not a text-parser pass or a current complete Municipal Code substitute.
- **Emeryville Title 8:** its official Building Division still links a 41-page PDF. Inspection identifies Ordinance 22-013 adopted November 15, 2022. The landing page now discusses the 2025 codes effective January 2026. Treat the linked PDF as a historical partial adoption ordinance.

Other material remains explicitly limited. Santa Rosa offers a full Charter HTML page, but ordinary HTTP returned 403 here. Flagstaff's former land-development code is expressly repealed, and its separate procurement manual does not replace the City Code. Tukwila's complete old February 2024 code is historical; its observed PDF URL returned an empty HTTP 200 body twice, which is rejected as unusable. Berkeley's publisher entry labelled “Full Code PDF” proved to be an ordinance-disposition table, not a verified PDF download. Official Foster City and Sonoma pages retain legacy Code Publishing links, so the provider migration needs reconciliation rather than assuming those pages designate the newer publisher route.

Every jurisdiction record lists its observed official pages, exact URLs, currentness limits, retained HTTP receipts and the result of the bounded check. **“Not verified” does not mean “does not exist.”** Web search excerpts were used for discovery and are distinguished from downloaded source bytes. There was no full-jurisdiction extraction, import, purchase or access/TLS bypass.

## Portable setup and commands

Use Python 3.9+; Python 3.11+ with modern OpenSSL is recommended. No absolute user directory or pre-existing temporary environment is required. From this directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest test_discovery -v
.venv/bin/python build_report.py
```

Run a fresh bounded discovery of the 28 declared city pages, with a maximum of six concurrent requests to different city sources:

```sh
.venv/bin/python discover.py discover --routes routes.json --out /tmp/official-discovery-new
```

Run the first-party Charter pilot from live HTTP, or replay its retained raw source into an arbitrary new output directory:

```sh
.venv/bin/python qualify_charter.py --out /tmp/emeryville-charter-live-new
.venv/bin/python qualify_charter.py --input discovery-current/emeryville-ca/1.html --out /tmp/emeryville-charter-replay-new
```

The pilot exports the 16 fields, CSV/JSON equality check, independent eight-node inventory, explicit included/excluded sample dispositions, article hierarchy, original HTML and paragraph locators. It rejects changed section membership and unknown operative paragraphs instead of silently dropping content. Only sections 100 and 200 are exported.

Download and inspect an explicitly observed public PDF:

```sh
.venv/bin/python discover.py download --url 'https://santaclara.legistar.com/View.ashx?GUID=9FDBDA24-1C91-4A58-859B-2516966A0809&ID=15562338&M=F' --out /tmp/santa-clara-charter-new.pdf
.venv/bin/python inspect_pdf.py --input /tmp/santa-clara-charter-new.pdf --out /tmp/santa-clara-charter-inspection.json
```

`inspect_pdf.py` checks original PDF magic, page count, encryption and bounded selected-page text; it records `ocr_required` if those pages have no text. It makes no full-document layout-fidelity or legal-currentness claim. Optional visual review uses ordinary Poppler:

```sh
pdftoppm -f 1 -singlefile -scale-to 1400 -png /tmp/santa-clara-charter-new.pdf /tmp/santa-clara-first
```

The PDF skill was used for read-only source inspection. No PDFs were authored or edited. Retained PNGs document visual review of the Santa Clara first/last pages and Emeryville first page.

## Evidence and limitations

`discovery-current/INDEX.json` records 28 initial live city-page attempts. Most failures were ordinary 403 or obsolete-route 404 responses. `supplemental/` retains exact official Legistar attachment-label evidence and two city redirects. `downloads/` retains PDFs and download receipts; `inspected/` holds bounded PDF text/structure results and rendered pages. `final-emeryville-charter/E2E-VALIDATION.json` is the final frozen-code live Charter pilot. `FINAL-VALIDATION.json` records final code hashes, commands, tests and final download/inspection checks.

The initial discovery utility followed normal HTTP redirects. After the parent stopped eCode host probes, one city route incidentally redirected to eCode and returned 403; this was reported immediately. The final utility disables all automatic redirects and rejects explicit eCode host requests. A redirect is retained for review, never automatically followed. No 429 retries occurred in this alternatives task. The first Tukwila empty HTTP 200 was incorrectly labelled downloaded by the initial utility; the corrected recheck records failure and there is no usable PDF file or content claim.

Final code uses normal Requests certificate verification, fresh output paths, bounded bytes and timeouts. It rejects empty HTTP 200 responses, HTML masquerading as PDF and changed Charter profiles. Existing outputs are never treated as fresh live acquisition. The original sealed E2E package and other agents' files were not modified.
