# Thirteen expansion jurisdictions: standalone acquisition validation

This package validates bounded live acquisition, parsing, and normalization. `assignment.json` defines the thirteen targets; `results.json` gives exactly one result per assignment, with precise tested scope, primary and supplemental publisher downloads, evidence paths, and limitations. **No jurisdiction is claimed to be a complete legal corpus.**

Final bounded outcome: all13 primary targets pass standalone E2E, with83 normalized records:67 legal provision records and16 explicitly labelled supplemental PDF page records. There are5 structurally preserved HTML sample tables; detected PDF table fragments are reported separately. Eleven primary publisher PDFs and Aurora’s native HTML export were acquired; Kansas City’s primary PDF download is disabled. Omaha, Virginia Beach, Miami, and Tulsa PDF cover supplements differ from the current API jobs, so download success does not establish current full-text equivalence.

The tested target list is Fresno CA, Atlanta GA, Kansas City MO, Mesa AZ, Raleigh NC, Miami FL, Omaha NE, Virginia Beach VA, Long Beach CA, Tulsa OK, Aurora CO, Wichita KS, and New Orleans LA. Virginia Beach is an independent city; City of Miami is separate from Miami-Dade County. Official code routes and separately published code families are inventoried in `route-inventory.json` and `code-families.json`. Some city routing pages returned HTTP403 while publisher APIs remained usable; retained routing failures do not imply unavailable municipal law.

## Setup after relocation

Direct HTTP acquisition and offline replay require Python3.10+ with the listed dependencies. The optional browser method additionally requires Node22+, a normal graphical desktop, and installed Google Chrome. Create a dedicated virtual environment and install the pinned Python dependencies for supplemental HTML/PDF parsing:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm install
```

The core Municode normalizer and HTTP gate use Python's standard library. `lxml`, `pypdf`, and `pdfplumber` are needed for the additional native exports. `pdftoppm` is optional for reproducing the source PDF visual check. `curl` with the system certificate store is used as a normal TLS-verified fallback for New Orleans CZO; `--insecure` is never used.

Use `./run.sh --offline` for the combined verification wrapper, or `./run.sh --target mesa` for a direct public HTTP run into a new timestamped `fresh/` directory. Explicit `--out fresh/<new-name>` is supported by `collect_http.py`; populated output directories are refused. Historical acquisition commands are provenance, not instructions to overwrite retained evidence. The direct collector `scripts/collect_http.py` resolves the observed public organization route to ClientID, then Products/name, Jobs/latest, full TOC, three section bodies, ClientContent and an enabled publication PDF. It shares the same publisher rate gate and needs no browser.

No Codex, CUA, previous package, machine-specific profile, or absolute path is required. The tested machine/runtime details are in `runtime.json` and per-run browser receipts. During this validation, the bundled Node v24.19.0 and Python3.12.14 were selected through environment variables. Those installation paths are historical provenance only.

## Reproduce live acquisition

From this package root:

```sh
export PYTHON="$PWD/.venv/bin/python"
node scripts/collect_browser.cjs \
  'https://library.municode.com/ca/fresno/codes/code_of_ordinances' \
  browser/fresno-rerun 3
.venv/bin/python scripts/normalize.py browser/fresno-rerun --offline
```

Use a new output directory to preserve an earlier run. `scripts/collect_all.py` serially visits all assignment URLs and skips targets that already have a receipt. It supports `NODE`, `PYTHON`, `BROWSER_CHANNEL`, and `PLAYWRIGHT_MODULE_ROOT`; ordinary npm installation needs no module-root override. `PLAYWRIGHT_MODULE_ROOT` is a package.json path used only when Playwright lives outside this package. The collector uses ordinary headed Chrome, a fresh context, and observed public application APIs. It imports no cookies and performs no login or challenge interaction. Later versions stop downloading image/font/media assets; linked illustrations remain outside these samples. Every execution preserves its script and gate versions alongside its receipt. Initial versions are retained in `script-versions/`.

```sh
.venv/bin/python scripts/route_audit.py
.venv/bin/python scripts/native_samples.py
.venv/bin/python scripts/build_results.py
```

The native-export script acquires the publisher-generated full CZO HTML from `https://czo.nola.gov/print-all/` and the current official planning-library Tulsa zoning/subdivision PDFs. The CZO download is publisher HTML; it is not browser print-to-PDF. Only bounded sections/pages are normalized. The first indexed Tulsa zoning URL was an older uploaded copy; the final retained PDF uses the current link from the official planning-library page and visibly states October21,2025. The separate subdivision PDF's printed date must be checked independently of the website's amended-date label.

`recover_bootstrap.py NAME` is a documented continuation for an initial browser run that retained successful Products/name and Jobs/latest responses but timed out on page rendering. It reads identifiers only from retained successful application responses and continues through the same shared public HTTP mechanism. The prior browser failure remains unchanged. This is a mixed browser-bootstrap/ordinary-HTTP standalone method.

## Offline replay and verification

No network or browser is used by:

```sh
.venv/bin/python scripts/offline_replay.py
```

Offline replay verifies retained response hashes, reparses the primary requested section bodies and bounded native exports into temporary directories, and compares normalized JSONL/CSV hashes without modifying the retained package. `build_results.py --offline` is an explicit authoring/rebuild command that regenerates derived reports; it is not the routine read-only verification entry point. `verify_package.py` checks output hashes, references, assignment cardinality, source signatures, and substantive known source/table anchors. Offline replay proves reproducibility of the retained evidence; it does not re-establish live currency.

Each primary provision contains exact source node ID, heading, TOC path, body text and HTML, links, source citation URL, product/job version identifiers, and body hash. Tables preserve HTML and parsed cell-span metadata. Supplemental CZO records preserve numbered headings and HTML tables. Supplemental PDF records explicitly use `record_type=pdf_page`; no page is misrepresented as a legal section.

## Rate controls and blockers

The shared Municode acquisition module uses a process-safe filesystem lock. All simultaneous collectors must share `MUNICODE_GATE_DIR`, which defaults to `/tmp/compliSolv-municode-rate-gate`. The initial gate reserved nominal3second intervals; the shared audit found small logged timestamp undershoots (minimum2.899seconds) due to reservation/logging timing. No HTTP429 was observed. After Raleigh completed, the direct driver was restarted and both shared helpers were updated to a3.5second guard for subsequent requests. Exact prior executed module versions and an interrupted Miami bootstrap are retained; no historical pacing claim is retroactively strengthened. HTTP429 creates a shared cooldown of at least300seconds or longer Retry-After. No rotating IPs, retries during cooldown, authentication bypass, or challenge solving is implemented. On Windows, use a POSIX runtime or replace the `fcntl` gate with an equivalent process-safe gate before live use.

Representative additional live provisions include Fresno15-902 (58table rows), Mesa11-5-2 (97rows), and Atlanta16-18A.006 (two tables of4and68rows). Independent offline Chrome DOM checks compare every source cell’s rendered text, tag, rowspan and colspan:1,086cells, zero mismatches. Saved reports bind source HTML and complete normalized JSONL hashes; read-only replay verifies those bindings.

The initial Fresno browser run reached HTTP200 public APIs but failed the120second application-readiness wait. It is preserved in `browser/fresno/`; a separate `recovery/fresno/` path records continuation if it succeeds. The package retains failed primary attempts and all response receipts. Valid PDF response bytes are retained as `publisher-export.pdf`; direct HTTP request receipts preserve the original capture name `publisher-export-response.bin`. `publisher-export.validation.json` maps that original receipt to the retained filename and rechecks its hash. Publisher-native publication PDF availability is measured independently from HTML acquisition. ClientContent controls publication download eligibility; Products/name can conflict (as Fresno did). A PDF feature disabled in ClientContent metadata is `unavailable`; a failed download is `blocked`; a download from a separate code family is recorded separately and does not prove the primary publication was downloadable.

PDF table detection is a quality probe. Tulsa Table5-2 spans merged headers and multiple page regions. `pdfplumber` returns three fragments on the checked page and omits some row labels. The retained PDF, page image, and plain text support review, but those fragments are **not a certified rectangular table dataset**. New Orleans Table3-1 retains the native HTML structure and fifteen rows in the sample. Raleigh's standalone UDO, Miami21 CodeHUB, Aurora's https://aurora.municipal.codes/ UDO, and Wichita-Sedgwick County's joint zoning code are separately inventoried additional families whose coverage is not proved by the municipal-code sample. Recent uncodified ordinances, external incorporated standards, maps, specific plans, separately hosted zoning, and all additional code families require explicit follow-up before any complete-jurisdiction assertion.

## Aurora source migration and final replay environment

The assigned Aurora Municode product is no longer active: Products/name returned Product not found, and ClientContent1111 returned an empty publication inventory. Current official city routing leads to `aurora.municipal.codes`, whose root independently exposes General City Code `/Code`, UDO `/UDO`, and Charter `/Charter`. The self-contained `aurora-current/` validation captures fifteen operative sections1-1 through1-15 from general Code chapter1 articleI and a genuine native HTML export with identical bodies/citations. The source and export state Ordinance2026-42, passed August10,2026. Reserved sections1-16 through1-35 have no operative body and are separately dispositioned. Prior Municode and direct403 failures remain in this group.

Aurora was coordinated with the ICC publisher agent using one ordinary headed browser session after root authorized resumption. Its portable Python collector and source/export equivalence verifier are included under `aurora-current/`; the routine group replay invokes that verifier read-only and requires the requests/BeautifulSoup dependencies pinned in the updated root requirements. Python Playwright is included for optional Aurora live reruns; Node Playwright remains the shared Municode browser dependency. A validation `.venv` was created with the bundled Python and system-site packages plus the added Aurora dependencies. Exclude `.venv`, `node_modules`, and `__pycache__` from relocation or handoff archives; recreate dependencies from requirements.
