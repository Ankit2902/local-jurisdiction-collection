# Wave 3 official-source validation — 17 October 2026

This self-contained package validates seven assigned local governments with real live legal bodies, retained native downloads and deterministic offline replay. It contains **42 normalized records**: Arlington TX 7, St. Louis 3, Spokane 4, Worcester 8, Chattanooga 6, Savannah 4, Arlington County VA 10. All jurisdiction corpus-completeness flags are false. Inventories and TOCs contribute zero records.

| Sequence | Scope proved | Native download | Scope and currency limit |
|---|---|---|---|
|58 Arlington city, Texas | Alarm Systems Article II §§2.01–2.07, seven complete provisions | Official 59-page chapter PDF, 1,483,595 bytes | Chapter cover amended May 27, 2014. Official site calls online code a convenience and lists newer uncodified ordinances. Charter and Unified Development Code are separate and unparsed. |
|71 St. Louis independent city, Missouri | Three primary code sections 1.01.010–1.01.030 | Full 3406-page publisher PDF, 23,540,094 bytes | Supplement 11 June 2026; codified through Ord 72042 enacted October 30, 2025. Excludes St. Louis County. Charter, Title 26 zoning and 28 uncodified ordinances not normalized. |
|78 Spokane city, Washington | Four actual Chapter 01.02 provisions .010/.020/.030/.950 | Native one-section print HTML corroborates .010; separate whole charter print HTML retained | Chapter print returned only a TOC and is explicitly rejected. Separate Charter and embedded UDC Titles 17A–17I inventoried; not segmented. |
|80 Worcester city, Massachusetts | Eight Chapter 1 provisions of Part One | Whole 659-page Part One PDF, 4,062,588 bytes | Cover amended September 8, 2026. Part Two organization, Salary, Zoning, Charter and other regulations are separate scopes. |
|85 Chattanooga city, Tennessee | Three Charter provisions 1.1/1.2/2.1 and three Part II City Code provisions 1-1/1-2/1-3 | Full 2292-page publisher PDF, 23,986,481 bytes | Supplement 40 September 2026; through Ord 14374 enacted June 16, 2026. Flattened publisher tree initially selected Charter sections; separate observed Code leaves were then acquired and labeled. 48 uncodified ordinances unparsed. |
|87 Savannah city, Georgia | Three code-adoption provisions and one development-impact fee attachment | Native **four-page selected fee attachment PDF** passed | Current official Clerk route leads to enCodePlus; assigned historical book page is not current code. Fee attachment effective July 1, 2023; publisher null archive sentinel 1901 dates excluded. Export is one fee attachment, not whole code. Charter/zoning inventory is not full collection. |
|99 Arlington County, Virginia | All 10 operative sections of posted Chapter 1 | Whole 3-page official chapter PDF, 148,607 bytes | Current 80-document portal independently lists Chapter 1 “Updated September 2011.” Official warning: not all chapters are current. County scope excludes Arlington TX. Zoning separate. |

`publication-families.json` records source-bound publication families and limits. `parsed/*-official-inventory.json`, publisher inventories and County’s 80-document current portal inventory retain the observed links. A successful full-file download is separate from fully segmented legal content.

## Offline verification

From this directory on POSIX/macOS/Linux, with Python 3.10 or later:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -B scripts/verify.py
```

The retained test venv is available for root’s independent replay. Exact tested runtimes are in `runtime.json`: Python 3.12.14, Node 24.19.0, Playwright 1.62.1 and Chrome 155.0.8059.84. The host’s default Node is old; use a current Node explicitly. Offline verification needs no Node/browser/network. It hashes all sealed artifacts, checks schema/proof paths/counts, regenerates all parsed outputs into a temporary directory and byte-compares them, then independently replays the final generic collector’s fresh Arlington TX acquisition. It checks that the final portable Municode collector bytes exactly equal the fresh Chattanooga executed snapshot. It writes no package inputs or outputs. Use `-B` to suppress Python bytecode. No old package, database or Codex API is needed after relocation.

To write an additional replay to a new directory:

```sh
.venv/bin/python -B scripts/normalize_all.py --offline --out replay-new
```

`parsed/<sequence>/records.jsonl` and `.csv` are the common normalized outputs. Municode `sections.*` retains the collector’s initial three-record sample separately; for Chattanooga those are the three Charter records, and `records.*` combines them with the three independently acquired City Code records. Do not sum both files.

## Fresh live acquisition

Use unpopulated output names; collectors refuse existing receipt names. Retained receipts identify exact commands, request/response URLs, timestamps, headers, source hashes, runtime and copied executed script bytes. `raw/executed/`, `raw/script-versions/`, each Municode acquisition directory and `fresh/58/executed/` preserve the versions actually run. The final generic collector was exercised in `fresh/58`; the final shared Municode collector was exercised in `raw/85-final`.

Install dependencies and an ordinary installed Chrome (not a downloaded stealth browser):

```sh
npm install
```

Arlington TX native download expands the official chapter accordion before selecting the observed Alarm Systems PDF. This exact final generic script completed a fresh run:

```sh
node scripts/browser_capture.cjs --out fresh-new/58 --jobs arlington-tx-native-job.json
.venv/bin/python -B scripts/replay_one.py --sequence 58 --raw fresh-new/58 --out fresh-new/58-parsed
```

Shell commands are written explicitly to avoid a hidden cache. County’s corresponding recipe is `arlington-county-native-job.json` and sequence 99. Ordinary urllib returned 403 on these government hosts; the successful ordinary headed browser download follows an official link, without importing state or challenge interaction. Retained portal-file 403 attempts are not native successes.

Worcester uses serial native HTTP:

```sh
.venv/bin/python scripts/fetch.py --out fresh-new/80 --batch worcester-jobs.json
.venv/bin/python -B scripts/replay_one.py --sequence 80 --raw fresh-new/80 --out fresh-new/80-parsed
```

Spokane uses its ordinary documented public GET pages and observed native print POST. Include the negative chapter-print fixture so replay verifies it is TOC-only:

```sh
.venv/bin/python scripts/fetch.py --out fresh-new/78 --batch spokane-jobs.json
.venv/bin/python -B scripts/replay_one.py --sequence 78 --raw fresh-new/78 --out fresh-new/78-parsed
```

St. Louis and Chattanooga use copied final shared ordinary-browser public-API collectors. **Direct Municode HTTP remains stopped after the coordinated wave 3 challenge.** Root separately authorized an ordinary browser availability check, then this gated browser-only workflow after a normal page succeeded. `gate_cli.py` requires POSIX `fcntl`; it defaults to the same cross-process `/tmp/compliSolv-municode-rate-gate` and a configured 3.5-second guard. Never delete a stop flag to force a retry. A new challenge/403/429 stops the workflow and coordinates a browser-family stop; honor Retry-After. No proxy, state import, fingerprint change, challenge interaction or mocked legal response is used. Application bundles and unrelated assets are omitted; publisher security scripts remain enabled. The screenshot is a **document shell**, not legal-body proof. Actual legal evidence is retained exact-node API bodies.

```sh
MUNICODE_EXPECTED_CLIENT_NAMES='["St. Louis"]' MUNICODE_EXPECTED_STATE=MO node scripts/municode/collect_browser.cjs https://library.municode.com/mo/st._louis/codes/code_of_ordinances fresh-new/71 3
.venv/bin/python -B scripts/replay_one.py --sequence 71 --raw fresh-new/71 --out fresh-new/71-parsed
MUNICODE_EXPECTED_CLIENT_NAMES='["Chattanooga"]' MUNICODE_EXPECTED_STATE=TN node scripts/municode/collect_browser.cjs https://library.municode.com/tn/chattanooga/codes/code_of_ordinances fresh-new/85 3
node scripts/acquire_chattanooga_code.cjs fresh-new/85 fresh-new/85-code
.venv/bin/python -B scripts/replay_one.py --sequence 85 --raw fresh-new/85 --supplement fresh-new/85-code --out fresh-new/85-parsed
```

The final command above combines the generic three-record Charter sample and three supplemental City Code provisions. The supplemental City Code wrapper reads exact observed leaves from that run’s live TOC, binds product/job/client/state and separately acquires each body; both replay entrypoints verify all three supplemental bodies against the retained batch provenance. Fresh publication IDs/jobs are resolved live. Signed PDF links in old receipts expire; never reuse one as a permanent download URL. `MUNICODE_GATE_DIR` may be configured only for an independently coordinated deployment; all simultaneous processes must share it. `PYTHON` can select a Python interpreter for the main collector’s gate. `NODE_PATH` or `PLAYWRIGHT_MODULE_ROOT` may point to an existing Playwright install; ordinary `npm install` at this package root also resolves correctly.

Savannah’s shared adapter uses the separate 3.5-second `/tmp/compliSolv-encodeplus-rate-gate`, respects Retry-After, records raw bodies and exact executed scripts. Run the following once for each observed URL, then replay:

```sh
.venv/bin/python scripts/encodeplus/fetch_one.py 'https://online.encodeplus.com/regs/savannah-ga/doc-view.aspx' fresh-new/87/87-encodeplus-toc.html
.venv/bin/python scripts/encodeplus/fetch_one.py 'https://online.encodeplus.com/regs/savannah-ga/doc-view.aspx?secid=499&ajax=0' fresh-new/87/87-section499.html
.venv/bin/python scripts/encodeplus/fetch_one.py 'https://online.encodeplus.com/regs/savannah-ga/doc-view.aspx?secid=500&ajax=0' fresh-new/87/87-section500.html
.venv/bin/python scripts/encodeplus/fetch_one.py 'https://online.encodeplus.com/regs/savannah-ga/doc-view.aspx?secid=501&ajax=0' fresh-new/87/87-section501.html
.venv/bin/python scripts/encodeplus/fetch_one.py 'https://online.encodeplus.com/regs/savannah-ga/doc-view.aspx?secid=7137&ajax=0' fresh-new/87/87-impact-fee7137.html
.venv/bin/python -B scripts/replay_one.py --sequence 87 --raw fresh-new/87 --out fresh-new/87-parsed
```

These exact observed IDs fail closed if a publisher migration changes the contract; first rediscover from the current official route/TOC rather than silently substituting another publication.

## Parser and PDF checks

PDF segmentation excludes opening TOCs, asserts exact expected section IDs/counts and substantive bodies, joins the wrapped County 1-6 heading, removes known running headers/footers and preserves page citations. PDFs are native files, not browser print. Selected PDF chapters have no legal tables; paragraphs/lists and cross-references survive as extracted text, while typography, diagrams, page images and linked annotation semantics are not reconstructed. Visual PDF QA images and source-page text are retained in `qa/`; operative boundaries were visually inspected. These bounded checks do not qualify arbitrary multi-column/table extraction across a full PDF.

For St. Louis and Chattanooga the normalizer reads the PDF itself, verifies magic/hash, printed supplement/date/ordinance/jurisdiction against the selected publisher job/banner, and corroborates selected legal prose against actual operative pages (St. Louis 171; Chattanooga 157,163–168,319–321). Distinct four-or-more-letter word coverage must be≥90%, permitting hyphenation differences. This is bounded prose corroboration, **not exact PDF body or table reconstruction**. The St. Louis printed name “Saint Louis” is an explicit alias of API“St. Louis”; Missouri comes from independently checked client metadata. Chattanooga TOC pages 155/317 are not body evidence.

Chattanooga Charter§1.2 contains an appended Home Rule amendment table:97 rows/291 cells, all source text/rowspan/colspan values independently compared using BeautifulSoup against the separate stdlib normalizer. Source date`5/9/000` is preserved verbatim. Savannah’s actual fee attachment has 79 rows/555 cells, including merged 8-column heading; every cell text and span is independently checked and the eight-cell single-family fee row is explicitly asserted. Headings, selected container IDs, hierarchy/citations, links, HTMLlists and sup/subboundaries are retained. Publisher’s hidden/null 1901 archive dates are not treated as enactment dates.

Failures remain visible: initial government 403 s, early unmatched native-link timeouts, an interrupted full Municode bootstrap, TOC-only Spokane chapter export and County portal-file 403 s. None contributes legal records. Source inventories are bounded observations from 17 October 2026; every separately listed family requires its own acquisition/currentness validation before production ingestion.

`qa/shared-browser-gate-window.json` retains the shared reservation log during these Municode runs, including co-running groups. Its minimum adjacent wall-clock timestamp delta is 3.4607 seconds despite the configured 3.5-second guard; this package does not claim every observed timestamp interval met exactly 3.5 seconds. The final helper uses one shared POSIX lock and stop state.

## Savannah selected native export

`savannah-native-export/` is the copied self-contained, separately qualified assist. Its observed fee attachment Export PDF control maps through the current linked publisher script to the normal status-page/polling/File-token flow. The genuine four-page PDF is 99,580 bytes, SHA256 `901acca77699f1e70316a6a780a0aa470eb909c92547043cb7e5aa84af77b607`. Native publication identity, heading and 7/1/2023 effective date match; all 555 HTML table-cell texts occur in native PDF text, and the ordered eight-cell single-family row matches. This text check does not establish every PDF row/column layout relationship. It adds zero unique legal records.

The main read-only verifier invokes the assist verifier and checks that its source fee HTML bytes equal the original parsed source. See [its README](savannah-native-export/README.md) for the exact observed control, acquisition commands, statuses, provenance and fresh native workflow; all source snapshots, requests and four page renders remain intact. The assist was copied only after its owner froze it. Its own verifier is independently runnable from any cwd:

```sh
.venv/bin/python -B savannah-native-export/scripts/verify.py
```
