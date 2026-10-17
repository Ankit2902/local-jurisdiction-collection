# Technical handoff: first 57 expanded local jurisdictions

This package contains standalone acquisition scripts, fresh live evidence, bounded normalized samples and offline replay checks for the first 57 entries in the 100-jurisdiction expansion shortlist. Validation date: 17 October 2026. Six Sol agents performed the publisher/source-specific work; the coordinating agent independently checked the finished packages.

**Final result: 56 of 57 jurisdictions passed standalone acquisition through normalized output for a bounded sample. Milwaukee is partial because rotated PDF table headers and figures still need parsing work; its native download succeeded. Native publisher download outcomes are 49 passed, two partial, five unavailable and one blocked. No jurisdiction is claimed to be a complete ingested corpus.** All six group packages passed the coordinator's offline replay after copying to fresh temporary locations.

Start with [summary.json](summary.json) for final counts, [JURISDICTIONS.md](JURISDICTIONS.md) for the 57-row index, and [results57.json](results57.json) for each jurisdiction's exact method, tested scope, command, evidence, limitations and next action. The frozen input is [scope57.json](scope57.json). This is a method-validation handoff, not a completed corpus ingestion.

## Run the tested methods

Each group directory is a self-contained source-family package. Follow its README to install dependencies and execute its acquisition and verification entrypoints. Commands in the aggregate results run from the stated `working_directory`; aggregate `evidence_paths` and `script_paths` are relative to this package root. Other provenance paths remain relative to their group unless explicitly stated otherwise.

| Package | Targets | Principal method |
|---|---:|---|
| [municode-core](municode-core/README.md) | 13 | Ordinary headed Chrome with public code API requests, native publication PDF resolution, offline HTML normalization |
| [municode-major](municode-major/README.md) | 13 | Public HTTP API, browser fallback, native publication PDFs and official zoning sources; Aurora's current municipal.codes route |
| [municode-states](municode-states/README.md) | 12 | Public HTTP API, native publication PDFs and official zoning documents |
| [american-legal](american-legal/README.md) | 11 | Ordinary headed Chrome, public code navigation and publisher export workflow |
| [icc-publishers](icc-publishers/README.md) | 5 | Ordinary headed Chrome for municipal.codes, eCode360 and Code Publishing; native HTML/PDF exports |
| [official-sources](official-sources/README.md) | 3 | Official full-title HTML, recommended bulk ZIP, and native PDF link downloads |

Use a separate virtual environment for each group to preserve its tested dependency versions. Browser scripts use ordinary Playwright and installed Chrome; they do not require Codex, CUA, a Codex login, imported browser cookies or an existing user profile. Optional environment variables can point to an existing Node/Playwright installation, but the documented package-local installation is the handoff route. Tested host and exact runtime versions are recorded in group evidence. Live macOS success is not a Windows or Linux certification. The shared `fcntl` rate gate requires a POSIX host; see group instructions before adapting it to Windows.

Use fresh output directories where supported. Historical acquisition commands are provenance and may target populated evidence folders; do not overwrite retained validation evidence with a later run. Export URLs can expire: rerun the publisher's normal export resolution instead of reusing a signed URL from a receipt.

## What the results mean

- `standalone_e2e_pass` means the stated bounded sample completed live acquisition, parsing and normalized output with the reported checks. It does not certify an entire jurisdiction or every publication family.
- `standalone_partial` means some usable standalone work completed but an acquisition or parsing limitation remains. Read the exact scope and next action.
- Native publisher download outcomes are separate from sample outcomes. A successful selected-section export is not a whole-code export. A successfully downloaded whole PDF or ZIP is not a fully segmented and verified corpus.
- HTML legal-section records, table-heading records and PDF page records have different units. Do not add their counts and report the sum as legal-section coverage.
- Native PDF editions can lag current online code. Houston and Des Moines provide concrete examples in the retained evidence. Check supplement/ordinance dates before choosing the download over online sections.

The group inventories distinguish general code, charter, zoning/development, regulations and other separate sources. These boundaries matter: Charlotte's current UDO, Aurora's separate UDO, Miami 21, Raleigh's UDO and other additional publications cannot be inferred complete from a primary municipal-code sample. The per-jurisdiction inventories retain current routes and unresolved work.

Aurora's former Municode publication is inactive. Its current municipal.codes site presents Code, UDO and Charter separately; the successful sample and matching native HTML export cover 15 operative general City Code sections. The prior failed route is retained. Detroit's current published code also reports 74 uncodified adopted ordinances outside the tested sample.

The primary-publication PDF feature is unavailable for Austin, Indianapolis/Marion County, Oklahoma City, Kansas City and Bridgeport; their bounded section acquisition still passed. Bakersfield's later native-export attempt was blocked by HTTP 429 after its earlier successful sample. Portland and Milwaukee have genuine native downloads qualified as partial because the tested publication/normalization coverage is limited; read their group report for the exact boundaries.

## Verification and production next steps

Run `python3 verify_handoff.py` from this directory for the 57-target scope check, required evidence paths and package SHA-256 manifest. This standard-library check does not contact a publisher. Then run the group README's offline verifier for deterministic parsing and source-specific checks. Independent coordinator checks are retained in [qa](qa/).

Before extending from these bounded tests to full ingestion, use each publication inventory to enumerate its complete scope, preserve source/version identifiers and raw responses, reconcile supplement dates and uncodified updates, and check table/attachment coverage. Expand using the tested transport and parser with new run receipts. A retained TOC is an inventory, not acquired section bodies.

All Municode collectors must share the same gate directory when running concurrently. The final rate gate uses a guarded spacing interval and a shared cooldown; early timing observations and failed trials remain in evidence. Honor publisher rate limits and stop on challenges. Bakersfield's later municipal.codes export trial received HTTP 429 after its valid section sample; that failed export is not reported as a successful download.

The package retains diagnostic failures alongside successes so the team can understand why a browser route or native download was selected. Error-response bodies are not normalized as legal text. Do not run exploratory probes as a retry loop. The source-specific README identifies the production-facing entrypoint and any remaining limitations.
