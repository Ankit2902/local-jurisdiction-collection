# eCode360 standalone qualification — 2026-10-15

**The primary municipal-code standalone gap remains open for all 14 eCode jurisdictions.** The 13 previously untested current chapter URLs were tested with ordinary standalone Playwright and installed Chrome 155:12 initial responses were403 challenges and Santa Rosa returned429. No legal source was accepted or replaced with a retained source. Foster City's new headed test was deferred: the retained host throttle ledger refuses the command before browser launch. Its earlier headless403 result remains baseline evidence only.

The result is narrower than a claim that normal browsers can never work. The pilot stopped on initial access/challenge status. An already opened Foster City CUA page later completed passive security verification without interaction; that is current export metadata evidence, not a standalone acquisition pass. No further ecode360.com requests or export actions were made after the host stop instruction.

There is a useful **separate partial official Charter alternative** for Santa Clara. A fresh ordinary-HTTP Legistar download supplied a current29-page scanned Charter PDF. Local macOS Vision OCR processed one operative page into 27 lines; the rendered page and all lines were visually compared. The delivered bounded segmenter emitted five complete Charter paragraphs (§§100,200,300,301,302) as 16-column JSON/CSV. Section 303's heading has no body on page 1 and remains unresolved. **This does not close Santa Clara's municipal-code gap or qualify the whole Charter.** The companion official-alternatives package independently verified a separate bounded Emeryville Charter sample (2 records); neither Charter substitutes for the municipal code.

`STANDALONE-VALIDATION.json` is the authoritative14-city matrix. It provides best-method status, primary scope, source URL, format, evidence path, browser mode/version, outside-Codex qualification, record counts, blockers and next actions. `VALIDATION-REPORT.json` is its identical alias. Earlier `E2E-VALIDATION.json`, `BASELINE-E2E-*`, `live/` and `examples/` are copied prior-phase CUA/historical proof. Their 134 records are not new standalone records. The original sealed sibling packages were not modified.

## Portable local commands

Requires Python 3.9+, ordinary installed Chrome or Playwright Chromium, and dependencies in `requirements-browser.txt`. No Codex service, copied browser profile/cookies/storage state, credentials, TLS overrides or stealth modifications are used.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-browser.txt
.venv/bin/python -m unittest -v test_ecode360.py test_e2e.py test_standalone.py test_ocr_charter.py
node test_capture.mjs
.venv/bin/python validate_local.py --verify-bundle
```

Actual checks:34 Python tests and11 Node acquisition checks passed. The 34 include 26 inherited baseline regressions, 5 new standalone tests and 3 actual bounded CharterOCR checks. The standalone accepted-browser branch is tested with synthetic source only; it has no live success claim. Tests verify immutable acquisition-receipt hashes/copies, correct runtime labels, challenge rejection, overwrite refusal, host-wide429stop and retained throttle prevention before launch. Current runtime evidence records Python 3.9.6, Playwright 1.60.0, installed Chrome 155.0.8059.41 and Node 24.19.0. The Python build emitted an urllib3/LibreSSL compatibility warning; use a supported Python/OpenSSL build for deployment.

The final helper intentionally refuses new network jobs while `standalone-live/ecode360-host-throttle.json` remains active. Retry-After was not preserved by the first executed revision; the final code records it and stops the whole host queue immediately on 429. The executed first revision is retained as `standalone-live/standalone-executed-r1.py`, with its SHA in every actual pilot receipt. It continued the distinct-city queue after 429; this limitation is retained honestly rather than attributed to the corrected final code. No 429 or 403 request was automatically retried.

After an operator/publisher has resolved the throttle/access prerequisites, archive the stop ledger without destroying its evidence, then use a new empty output directory. Do not blindly rerun the batch. Examples for a separately authorized resumed qualification:

```sh
# One normal headless chapter probe, isolated fresh context.
.venv/bin/python standalone.py --slugs foster-city-ca --out NEW-OUTPUT

# Ordinary visible browser; no UA/fingerprint/profile changes.
.venv/bin/python standalone.py --slugs foster-city-ca --headed --out NEW-HEADED-OUTPUT

# Human uses the normal publisher interface; the program never solves challenges.
.venv/bin/python standalone.py --slugs foster-city-ca --headed --operator-assisted --out NEW-OPERATOR-OUTPUT
```

`--channel chrome` uses installed official Chrome; `--channel chromium` uses normally installed Playwright Chromium. The operator-assisted command is unvalidated here and prompts the human to resume only after legal content is readable. It does not borrow a CUA session or export cookies. A future successful run must retain source/customer/code/date/requested-node/TOC/body identity and stable source bytes; the runtime-independent standalone importer then writes parser/CSV/JSON/provenance outputs. The acquisition receipt remains immutable; pipeline status is a separate file. Missing bodies, changed versions, low readiness or failed text comparison cannot become a pass.

## Publisher export path and prerequisites

The [companion publisher-export report](../publisher-exports/README.md) describes the primary documentation and local intake CLI. eCode360's documented Print control creates a print preview; Download offers PDF/Word depending on publication and login. A browser Print→SavePDF artifact is distinct from a publisher PDF download. No current eCode export was acquired in this phase.

Fresh read-only Foster City metadata is retained at `standalone-live/export-metadata/foster-city-ca/metadata.json`: customer FO4449, code 337727, currency2026-01-26; PDF permission true but PDF login required true; Word permission false and export permission false. The current Print/Download buttons are visible and enabled. No click/download request followed the throttle. Other 12 retained subtree sources do not contain body permission flags, so absence means unknown, not denied. The companion report also records Santa Clara's earlier flags and the public-package limits.

The primary publisher documentation lists limited public PDF access, code/login-dependent downloads and a credentialed REST API requiring municipality-issued key/secret headers. No credentials were supplied or accounts/subscriptions acquired. Tech-team prerequisites are legitimate supported browser access, any required authorized publisher login, or a municipality-authorized export/API agreement. After obtaining a download, preserve the actual selected IDs/current-through notice, file/source/time/hash receipt and format, and run the companion `export_intake.py`. A readable file alone does not certify complete acquisition, semantic fidelity or publication inventory.

## Santa Clara Charter-only OCR proof

Files are self-contained under `standalone-live/official-alternatives/santa-clara/`. The PDF and ordinaryHTTP200receipt were copied byte-for-byte from the companion official-source agent's fresh acquisition, with origin hashes; they are not substituted prior-phase CUA source. The official June2026Legistar item separately identifies the current Charter attachment and proposed amendments. The PDF's first page visibly prints June5,2026. It is a Charter-only attachment, not a complete municipal-code export.

The first default Swift invocation failed because the installed SDK 27 required a newer compiler. A compatible SDK 26.5 invocation succeeded; both logs are retained. The path below is the tested localSDK, not an undocumented project dependency. Other Macs require a compatible Swift/SDKpair.

```sh
xcrun swift -sdk /Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk \
  vision_pdf_ocr.swift \
  standalone-live/official-alternatives/santa-clara/santa-clara-current-charter.pdf \
  1 NEW-OCR-OUTPUT

.venv/bin/python ocr_charter_review.py \
  --pdf standalone-live/official-alternatives/santa-clara/santa-clara-current-charter.pdf \
  --acquisition-receipt standalone-live/official-alternatives/santa-clara/santa-clara-current-charter.pdf.receipt.json \
  --ocr NEW-OCR-OUTPUT/ocr.json \
  --source-url 'https://santaclara.legistar.com/View.ashx?GUID=9FDBDA24-1C91-4A58-859B-2516966A0809&ID=15562338&M=F' \
  --out NEW-CHARTER-REVIEW-OUTPUT
```

This local OCR uses macOS PDFKit/Vision and no cloud OCR. It retains the page render, line text, confidence and bounding boxes. The parser binds the supplied200receipt/URL/PDFSHA, uses page/header-line identities rather than citation deduplication, refuses low-confidence bodies and preserves incomplete boundary nodes. Five complete bodies and one unresolved heading are recorded, with CSV/JSON parity and per-record provenance. `VISUAL-REVIEW.json` records the actual bounded comparison; confidence 1 alone was not treated as visual proof. The actual rendered page is at `vision-page1/page.png`; actual exports are in `final-ocr-review-exports/`.

This is a macOS-only, one-page OCR/segmentation pilot, not a general PDF parser. It does not prove cross-page assembly, tables/images, broader Charter inventory, whole-Charter completion or production readiness. Other layouts and lower-confidence OCR need human review. The companion official-alternatives package separately contains publicHTTP download/discovery commands and its Emeryville Charter proof.

## Deliverable limits

No primary municipal-code standalone source or publisher export passed. There are no full-corpus imports or production-ready collections. Complete publication/family inventories, end-to-end version reconciliation and broad source-sensitive review remain unverified. Every provisional export remains explicitly bounded and nonproduction. Browser profiles, authentication state, cookies and runtime installations are excluded from this bundle; only public source artifacts, receipts, review outputs and code are included.
