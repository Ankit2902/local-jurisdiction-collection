# eCode360 publisher-download qualification

Thirteen actual unattended publisher PDFs passed file intake and complete operative-text/title comparison against their fresh source. The PDF-native exporter produced 13 selected-section JSON/CSV records: 12 bounded text semantic passes and 1 San Leandro map-review record. Santa Clara current toolbar lacks Download; no file is claimed. These 13 PDF records are separate from the family 134 DOM records.

This package is an offline companion to the sole live worker in `../ecode360`. It makes no ecode360.com requests and opens no publisher pages. `DOWNLOAD-VALIDATION.json` records the actual qualification result. Earlier sealed packages are read-only inputs. Files from October 15 are clearly retained evidence or test fixtures; they are not new acquisition successes.

`CONTROL-OBSERVATIONS.json` records source hashes, the exact observed controls and legal section text. A fresh October 16 Foster City sentinel returned substantive legal content in ordinary isolated headed Chrome. Offline inspection of its final DOM confirms enabled **Download selected content** and **Print selected content** buttons. Foster's body flags simultaneously say PDF permission true and PDF login required true, Word permission false/login required true, and export permission false. Those flags describe the observed publication/session state. A visible enabled Download button does not demonstrate that anonymous download is available. A subsequent actual Santa Rosa Download dialog exposes an enabled PDF option and disabled Word option, with the displayed login restriction applying to Word only. Therefore the PDF-login-required body flag alone also cannot establish anonymous PDF denial; the actual PDF action/file outcome must be tested.

## Ordinary observed workflow

The sole live worker owns publisher requests and browser actions. The following observations guide an ordinary operator; this helper does not run a browser acquisition workflow.

1. Open the current chapter in an ordinary browser and verify jurisdiction, publication/customer, code ID, current-through date and substantive legal content.
2. Select one section through its observed content checkbox. On the inspected Foster City chapter, `input#guid_51404438_content_checkbox` selects **§1.01.020 Prior code repealed**, the smallest retained section. `input#guid_51404445_content_checkbox` selects **§1.01.060 Effective date**; `input#guid_51404427_content_checkbox` selects the more substantive **§1.01.010 Adoption – Secondary codes adopted**. A TOC checkbox has a separate `_toc_checkbox` ID. Reconfirm the actual current city's ID/label; these Foster GUIDs do not apply to another city.
3. Click `button[aria-label="Download selected content"]` and inspect the actual dialog. Follow an observed format option only. No generated download URL or format selector was qualified in the prior retained DOM, so none is constructed here.
4. If the publisher requires login, a subscription or payment, retain that displayed requirement and stop without creating an account or purchasing access. Record a click that was not attempted as not tested, rather than treating a body flag as an observed authentication dialog.
5. For an actual file, retain original bytes, filename, exact source/action URL, selected IDs, timestamp, browser/runtime, acquisition receipt and the actual executed acquisition script.
6. Keep publisher Download, publisher Print preview, and browser **Print → Save as PDF** separate. Browser-created PDFs do not qualify as publisher-generated downloads.
7. Run local file qualification below. Compare selected legal content, history and currentness with the source. Render PDF pages when a legal PDF is actually obtained. A file pass is not whole-code extraction.

The publisher's previously inspected primary toolbar help at <https://ecode360.com/help/tools> describes selected-content PDF/Word downloads with availability depending on code and login. The separately retained current pricing page at <https://www.icccodesolutions.org/subscription-services/> lists limited public PDF access and professional full PDF/Word access. The documented API at <https://developer.ecode360.com/> requires municipality-issued key and secret. These known references are not being requested again by this helper. No account, purchase, credentials, copied browser profile, or bypass is used.

## Install and run

Python 3 with the packages below is sufficient for offline intake. Validation uses Python 3.12.14, BeautifulSoup4 and pdfplumber0.11.9 from the existing agent-owned environment; it does not alter a shared environment.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s . -p 'test_*.py' -v
```

The 29 tests cover file signatures, corrupt PDF rejection, sparse/scanned PDF review classification, text/citation expectations, legal definitions, HTML table spans, challenge/login pages, overwrites, external receipt hashes, executed acquisition script hashes, artifact length/hash mismatch, and browser-print rejection. One retained publisher documentation PDF exercises real PDF parsing. It is a historical feature chart, not a new legal-code download; other basic intake fixtures are explicitly synthetic. Six added native-PDF regressions include all 13 actual files, complete source comparison, actual Emeryville heading without§, and preservation of operativeheadingwords/history.

`qualify_download.py` requires a canonical JSON receipt that links to the actual acquisition receipt and executed script. The field contract is described in `canonical-receipt.schema.json`. Both referenced files are local paths resolved relative to the canonical receipt. Required artifact hash and byte count must match the actual file. Expected jurisdiction and selected citations must be present in extracted text. Optional expected export currentness text is checked literally; an independent source before/after reconciliation is still necessary.

```sh
.venv/bin/python qualify_download.py \
  --file /absolute/path/to/actual-publisher-file.pdf \
  --receipt /absolute/path/to/canonical-receipt.json \
  --out /absolute/path/to/new-empty-qualification-directory
```

No ready-to-run eCode export endpoint is supplied because the live worker must first observe and acquire the actual export. The example command names local files only. Output retains the original bytes and writes `verification.json`, `sample.txt`, `download-checks.json` and the canonical receipt. Supply a new or empty output directory; existing evidence is never overwritten.

Exit 0 means file integrity and specified identity/citation text samples passed. Exit 2 means the file was acquired/retained but sampled text needs review. Exit 1 rejects the file/receipt qualification. A visible button, sign-in modal or print preview cannot satisfy `download_status=acquired`. The tool validates local evidence links; it does not independently authenticate an externally supplied receipt or browser session.

The generic `export_intake.py` supports HTML, UTF-8 text and bounded PDF samples. PDF defaults to first/last page and permits up to 20 selected pages via the canonical `sample_pdf_pages` list. Sparse pages require OCR/visual review; mixed image/text pages retain an explicit review gate. Source text and detected table cells are retained. Running headers and page continuations are not automatically certified as legal section assembly. RTF is preserved but requires a reviewed converter; ZIP/DOCX is explicitly unsupported and cannot silently pass as Word content. Any obtained Word file must therefore receive a separate reviewed converter before semantic qualification.

## Visual review and remaining limits

For an actual legal PDF, use Poppler to render the selected pages and compare legal body, tables, footnotes, page continuations and source-currentness notice. The PDF skill applies when such a file is received. Retain both images and a specific spot-check log. The package does not claim PDF legal layout coverage from a documentation fixture or text-only parse.

For a local HTML export, optional `render_html_sample.py` performs offline screenshots with JavaScript disabled and all network requests blocked. Install Playwright separately and choose its bundled Chromium explicitly (`--channel chromium`, with `python -m playwright install chromium`) or installed Google Chrome (`--channel chrome`, optionally `--executable-path /absolute/path/to/browser`). Its receipt records actual runtime versions. This is offline visual QA, not acquisition or browser-print export.

No whole publication, all 14-city legal corpus, legal effect, new-law incorporation or production import is established by local intake. Keep all observed permission flags, actual modal requirements, downloaded file checks and not-tested routes separate in the final report.

## PDF-native selected-section export

`export_selected_section.py` supports only the observed one-page publisher layout. It reads citation/title/body directly from PDF bytes, independently matches complete operative text and title against the hash-bound selected DOM body, and writes `section.json`, `section.csv`, `native-pdf-text.txt` and comparison/intake evidence. Only NFC Unicode normalization and whitespace collapse are used for text comparison. Legal punctuation, definitions, history and footnotes are not removed. The specific first-line city header and final publisher download footer are parsed separately; legal prose about headings is retained.

```sh
.venv/bin/python export_selected_section.py \
  --file downloads/south-san-francisco-ca/publisher-download-0.pdf \
  --receipt downloads/south-san-francisco-ca/canonical-receipt.json \
  --source-html downloads/south-san-francisco-ca/source.html \
  --out /tmp/ssf-native-section-recheck
```

Use a new output directory. Exit0 is a bounded text-semantic pass; exit2 retains parsed output with a text/nontext layout review gate; exit1 rejects an unobserved layout or broken evidence link. No general PDF parser, table semantics, multipage assembly or whole-code coverage is claimed. `final-export-commands.json` records all 13 actual CLI executions after final source freeze. `aggregate-pdf-sections.json/.csv` combine 13 native PDF records. San Leandro includes the incorporated 2022 district map in the originalPDF and rendered page; its JSON has image-region/sourcehash provenance and remains explicitly review-required.

`VISUAL-QA.json` records full page1 inspection for all 13 PDFs. All visual page-integrity checks passed; San Leandro map meaning/geometry remains manual. Sourcecurrency and code IDs come from the acquisition's before/after DOM receipt, because PDF footers show customerbacklink/download date but no immutable codeeditiontoken. Santa Clara is an observed absentcurrentcontrol, not a generic host-access failure.
