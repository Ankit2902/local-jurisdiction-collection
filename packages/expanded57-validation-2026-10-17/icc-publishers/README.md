# Five ICC publisher validation targets — 2026-10-17

This portable package validates **bounded substantive samples**, not complete jurisdiction corpora. All five targets passed fresh standalone ordinary headed Chrome acquisition → retained HTML → normalized JSONL/CSV. No Codex CUA, operator assistance, imported browser state, database write or old-package runtime dependency was used.

| Jurisdiction | Live normalized records | Native publisher download |
|---|---:|---|
| Phoenix | 6, City Code chapter 1 | HTML chapter export; same six citations/bodies as live DOM |
| Bakersfield | 10, Municipal Code chapter 1.01 | Blocked during later qualification: HTTP429 on publisher images; no export acquired |
| Newark NJ | 10, chapter 1:1 | PDF of one selected provision; readable text and complete selected-body word coverage |
| Municipality of Anchorage AK | 15, chapter 1.05 | PDF of one selected provision; readable text and complete selected-body word coverage |
| Burlington VT | 13, chapter 1 | HTML of three expanded leaf selections,1-1 through1-3; operative text equals live DOM |

`results.json` is the canonical five-row handoff, with commands, acquisition timestamps, raw hashes, checks, evidence paths, separate download statuses and limitations. `publication-inventory.json` identifies separate charter, zoning and development families; none of those inventories is a completeness assertion. `runtime.json` records the tested macOS/Python/Chrome/Playwright versions.

## Setup

Python3.12 was tested on macOS arm64 with an installed Google Chrome155.0.8059.84 and a normal graphical desktop. The driver uses Playwright's ordinary `channel='chrome', headless=False`; no browser executable path, Codex API or shared profile is required. File locking uses `fcntl`, so the current driver targets macOS/Linux. Browser installation/display configuration must be supplied on other machines.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
```

`requirements.txt` gives supported major version ranges; the lock file records the exact tested packages. `.venv` is a local convenience only and excluded from the package manifest. All imports needed for acquisition/parsing are copied into `lib/`, relative to this package. All commands must run from the `icc-publishers/` package root. Every `evidence_paths` and `script_paths` entry in this group’s results, including nested publisher-download evidence, is relative to that group root; the aggregate handoff may prefix those paths with `icc-publishers/`.

## Offline verification — no network

```sh
.venv/bin/python verify.py
.venv/bin/python verify_exports.py
.venv/bin/python build_results.py
```

`verify.py` verifies retained raw hashes and reparses each selected sample into a temporary directory, requiring byte-identical normalized JSONL and CSV and a CSV round-trip. It also compares Newark's two source layout tables with semantic output, including row/cell structure, text and spans, after normalizing the documented image placeholder. Those are layout tables (the seal and a cross-reference), not a complex numeric schedule.

`verify_exports.py` verifies native download hashes, reparses Phoenix and Burlington native HTML, and compares their substantive bodies with the corresponding live DOM. It retains normalized native HTML exports. It reads the Newark/Anchorage PDFs with pypdf, retains extracted text and verifies selected-provision binding and100% substantive word coverage. PDF layout fidelity and corpus extraction are outside this check.

A single retained sample can be replayed without any network or browser:

```sh
.venv/bin/python collect.py --job newark --offline --out evidence/newark-live
```

The canonical sample directories used by `verify.py` are `phoenix-final`, `bakersfield-browser`, `newark-live`, `anchorage-browser`, and `burlington-leaf-export`, all under `evidence/`.

## Fresh live runs

`results.json` stores reusable live commands in `command`, historical capture commands in `recorded_acquisition_command`, and retained-source replay commands in `offline_command`. Historical commands point to already populated evidence folders and are provenance only; do not execute them again. Use a **new empty output directory** for each browser acquisition. `jobs.json` supplies observed substantive routes. These commands perform a bounded sample and, where available, ordinary publisher UI export:

```sh
.venv/bin/python collect.py --job newark --browser --export --out fresh/newark
.venv/bin/python collect.py --job anchorage --browser --export --out fresh/anchorage
.venv/bin/python collect.py --job burlington --browser --export --out fresh/burlington
```

The equivalent commands are `.venv/bin/python collect.py --job phoenix --browser --export --out fresh/phoenix` and `.venv/bin/python collect.py --job bakersfield --browser --export --out fresh/bakersfield`. They remain implemented, but **municipal.codes live work is stopped for this run** after a later Bakersfield browser received HTTP429 on images. The retained `evidence/BROWSER-STOP.json` causes the driver to refuse that family. Do not remove that stop merely to retry. Earlier successful sample evidence is separate from that later failure. There were no retries after the rate limit. The stop contains no Retry-After header. All original public requests403 and browser failure evidence are retained.

Browser jobs acquire a package-wide file lock and pause3seconds before launch. Each context is fresh and is closed by its owner. A429 immediately stops further publisher requests in that context and persists a family stop. Ordinary redirects/assets are browser-managed. No challenge solving, proxy rotation, fingerprints, authentication or access-control bypass is implemented.

The browser waits up to45seconds for substantive content. It captures the full HTML, screenshot, source hash, runtime and observed response chronology. Export actions use observed controls: municipal.codes Share → This Page → Save → Web Page (HTML); eCode360 one observed section checkbox → Download selected content → PDF; CodePublishing expand chapter1 → select first three observed leaf checkboxes → Print/Save Selections → HTML → Save. These are publisher downloads, not browser print-to-PDF.

## Scope and evidence cautions

- Phoenix officially routes to municipal.codes and exposes separate City Code, Zoning Ordinance and Charter publications. Only City Code chapter1 is tested.
- Bakersfield's official Our Government page routes to `/Code`; the initial suggested `/BMC` request returned403. Only `/Code/1.01` is qualified. The separate Charter tab is observed; zoning/development scope still needs inventory review.
- Newark's captured full TOC exposes a Charter and TitleXLI Zoning and Land Use Regulations in the current eCode360 publication. Only chapter1:1 was collected. One cross-reference in the source seal-section table contains an empty span after “see Section”; output preserves that source condition instead of inventing a citation. Image pixels are not transcribed; ordered placeholders and image URLs remain in parse details.
- Anchorage's official May27,2026 announcement points to eCode360 AN6998 as the replacement platform. Charter and land-use planning scope are separate from this chapter1.05 test.
- Burlington's original official DocumentCenter lead and current Government route returned404 to standalone requests. Search-visible primary official material still corroborates CodePublishing, whose live chapter and download work. Charter/Related Laws and Comprehensive Development Ordinance AppendixA are additional families.
- **CodePublishing checkbox scope matters:** the first actual HTML download in `evidence/burlington-final/` contains a chapter TOC only. That real file is retained as a partial experiment. A substantive download pass is supported solely by `evidence/burlington-leaf-export/`, after expanding chapter1 and selecting three observed leaf checkboxes. It reparses to exactly three provisions.
- Early successful Bakersfield and Anchorage browser captures record driver hashes and exact versions but predate executed-driver snapshot retention. Their original driver bytes are not present. The reviewed parser copies are hash-bound, offline replay is deterministic, and the current rerunnable driver snapshots are retained for later Phoenix/Newark/Burlington captures. Do not imply stronger historical driver provenance.
- The driver evolved during validation; `executed-collect.py` in later evidence folders is the exact script at that run. Acquisition receipts record that script hash. Current `collect.py` adds the family stop/serial lock and fresh-directory safeguards. No old package is imported or modified.

Live output includes `source.html`, `source.png`, `acquisition.json`, `parse-details.json`, `records.jsonl`, `records.csv`, and `checks.json`; export attempts additionally retain menu snapshots, download observation and native files. Output paths are relative; evidence timestamps and script/parser/content hashes are in the JSON receipts. `MANIFEST.json` excludes local venv/bytecode and binds all delivered files.
