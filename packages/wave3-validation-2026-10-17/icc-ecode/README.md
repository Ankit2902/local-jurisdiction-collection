# Wave3 ICC/eCode validation —2026-10-17

This package validates six **bounded live samples**, with actual native publisher downloads and deterministic offline replay. It does not collect complete jurisdiction corpora. All work used standalone Python and ordinary headed Chrome; no CUA, human assistance, browser state import, database write, Git action or old-package runtime import was used.

| Sequence | Jurisdiction | Normalized records | Native publisher export |
|---:|---|---:|---|
|73|Buffalo NY|5 section records, chapter175 Fees;39tables|Selected §175-1 PDF,73pages;source word coverage100%|
|79|Tacoma WA|14 section records, chapter1.07 Equity in Contracting;includes one repealed-section history body|Selected §1.07.120 PDF,1page;source word coverage100%|
|81|Rochester NY|14 section records, chapter1 General Provisions|Selected §1-11 PDF,1page;source word coverage100%|
|86|Eugene OR|8 section records, chapter1 General|NativeHTML of all8 sections;citations/bodies equal live DOM|
|92|Albany NY|16 content nodes:14sections plus2article history bodies;1table|Selected §1-13 PDF,1page;source word coverage100%|
|98|Allegheny County PA|13 section records, chapter203 Adoption of Code|Selected §203-13 PDF,1page;source word coverage100%|

There are **70 normalized content-node records**, comprising68section records and2independently owned article history bodies. One Tacoma section record preserves a repealed heading/history. `results.json` records units and types explicitly. Albany article rows have blank `section_number` and a populated `article` field. `complete_corpus` is false for every jurisdiction.

`results.json` contains exactly one row per assignment, current source/edition bindings, commands, scope, separate publisher-download statuses, hashes, evidence and limitations. `samples.json` identifies the six canonical sample folders. All evidence and script paths are relative to the **`icc-ecode/` package root**, including nested download paths. Prefix those paths when integrating into a root aggregate.

## Setup and supported runtime

The tested runtime is Python3.12.14 on macOS arm64, Playwright1.64.0 and installed Google Chrome155.0.8059.84. Exact OS/runtime data are in each `acquisition.json`. The driver uses ordinary `channel='chrome',headless=False`, with a fresh isolated browser/context. It uses `fcntl` locking and currently targets macOS/Linux; an installed Chrome and graphical desktop are required for live acquisition.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
```

`requirements.txt` gives supported version ranges. `requirements-lock.txt` contains exact tested versions. A test venv is retained here until root verification and excluded from the manifest/Git. All helper modules are copied into `lib/`; no previous package or machine-specific path is imported.

## Read-only offline verification

Run from this package root:

```sh
.venv/bin/python verify.py
```

The verifier writes only into temporary directories. It verifies source and native-export hashes, requires byte-identical normalized JSONL/CSV replay, verifies eCode customer/code/date and requested chapter bodyGUID, checks source cross-reference anchor targets, and compares native exports with source content. It also verifies that altered raw evidence and a wrong publication edition are rejected. Its retained successful output is `evidence/offline-verification.json`.

The test environment remains available at this path for root’s independent replay, including a temporary copy of this package:

```text
/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/outputs/wave3-validation-2026-10-17/icc-ecode/.venv/bin/python
```

All parsing dependencies, including requests, beautifulsoup4 and pypdf, are declared. Playwright is imported only by live browser functions. `collect.py --offline` also reparses one retained sample, but it writes its normalized output into the specified folder; use `verify.py` for sealed read-only checks.

```sh
.venv/bin/python collect.py --job buffalo --offline --out evidence/buffalo/sample
```

## Source-backed table and export checks

Buffalo has39tables across the selected chapter; Albany has1table. The read-only tests cover **1,735rows,6,112cells and1,080cells with row/column spans**, comparing table/row/cell structure, span attributes, scope/headers and cell characters while ignoring whitespace differences introduced by removed presentation spans. Source images are represented by intentional ordered placeholders. Numeric amounts and punctuation participate in the DOM character comparison. Exact eCode anchor targets in each owned content body are retained in semanticHTML. Other selected chapters do not contain tables; no table coverage is implied for them.

The publisher PDFs are **native UI downloads**, not browser print-to-PDF. Their hashes, selected source IDs, pages and source-body word coverage are verified. The Buffalo fee export covers one dense provision across73pages. PDF word matching is not a claim of exhaustive numeric-cell equivalence, PDF layout fidelity, OCR or corpus completeness; the detailed table checks independently cover DOM→semantic output. Native PDFs and extracted text remain in the evidence folders.

Eugene’s publisherHTML export reparses to identical eight citations/bodies. `native-export-records.jsonl` and `.csv` retain the qualified normalized native output.

## Fresh live commands

Every live `command` in `results.json` uses a new `fresh/<job>` path. That path must be empty/uncreated. These commands use already observed substantive routes in `jobs.json` and acquire a bounded sample plus ordinary UI export:

```sh
.venv/bin/python collect.py --job buffalo --browser --export --out fresh/buffalo
.venv/bin/python collect.py --job tacoma --browser --export --out fresh/tacoma
.venv/bin/python collect.py --job rochester --browser --export --out fresh/rochester
.venv/bin/python collect.py --job eugene --browser --export --out fresh/eugene
.venv/bin/python collect.py --job albany --browser --export --out fresh/albany
.venv/bin/python collect.py --job allegheny --browser --export --out fresh/allegheny
```

Expected eCode identities are frozen to the tested edition. A future publisher update should fail qualification until its edition is reviewed and the job binding is deliberately updated. Publisher signatures, source pages and UI controls may change; an old output/get URL is retained download provenance and is not treated as a permanent acquisition API.

The CLI serializes browser jobs with a package file lock and pauses3seconds before launch. The supplied serial runner also pauses3seconds between jobs.429 stops publisher requests immediately and persists a publisher-family stop. An access-challenge document persists a family stop without solving/retrying it. Every acquisition retains the exact executed driver bytes, runtime, requested URL, response chronology, raw HTML, screenshot and source hash. Export UI snapshots and native files are retained. The driver closes only the browser/context it launched.

## Current routes, editions and limitations

- Buffalo’s current publisher identity is BU1237/code336421/date2026-03-31. The official city page corroborates this route and warns that eCode may lag recent legislation. Standalone official request403 is retained; no retry to that government host was attempted. The Charter and Unified Development Ordinance are separately visible families and remain uncollected.
- Tacoma’s official current page routes to TA6977 and lists individual titles, a scanned Charter attachment, Land Use Regulatory Code and Shoreline Master Program. Publisher identity is code337831/date2026-09-30. The old official title1 PDF has a moved-to-eCode notice; this sample uses current chapter1.07.
- Rochester’s official Charter/Code page routes to RO0104. Current identity is code337515/date2026-06-16. Charter, zoning, planned-development districts, amendment tables and prior zoning codes need separate scope review.
- Eugene’s current publisher root exposes `/EC`, with chapter9 LandUse within the Code. The official code-page request403 is retained, and indexed primary official content corroborates the route. Charter scope was not independently located or collected; the retained publisher root alone cannot prove a complete jurisdiction inventory. The observed live currency label is recorded in `publication-inventory.json`.
- Albany’s current identity is AL0934/code336787/date2026-07-06. The complete discovery TOC exposes the Charter and Unified Sustainable Development Ordinance, alongside the Code/appendices. The attempted official Find route404 is retained; an official residential guide corroborates AL0934. Two article history-body records are distinguished from the14sections.
- Allegheny’s official county legislative-resources page links AL1955 and the Charter. **The publisher explicitly includes legislation only throughJune4,2024** (code332273). Subsequent laws/current legal completeness are not established. County enactments are a separate layer from Pittsburgh and other cities, with provision-specific applicability.

Earlier discovery captures are inventory candidates, not substantive passes. One initial Albany sample attempted the root TOC and emitted no provisions; it is retained separately and excluded from the pass, which uses `sample-current`. An added conservative eCode node guard initially expected chapterGUIDs inside section-header markup and rejected valid chapter parses. The corrected normalizer verifies authoritative `body[data-guid]`; exact original drivers, failure log and corrected normalizer bytes/hashes remain retained. Those valid raw captures were parsed offline without repeating network acquisition. The legal parser helpers themselves were copied unchanged from prior reviewed packages.

`official-routing.json` distinguishes raw official route evidence from primary official content corroborated through web lookup. `publication-inventory.json` distinguishes observed charter/zoning/development families from tested sample scope. No full collection, database ingestion or production completeness claim is made.
