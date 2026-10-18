# Independent collector QA

This directory audits configuration coverage, raw-source ownership, completeness guards, resume integrity and the user’s literal `[IMAGE]` policy across the five adapters. It does not turn bounded samples, synthetic fixtures, full native PDFs or one representative publication into 100 full live publication passes.

The exact target configurations are in [the registry](../registry/README.md). `findings.json` records the material review issues and their closure. `offline-report.json` records the final tested source hashes, runtime and command outcomes. `validation-matrix.json` separates exact selected primary live proofs from family implementation tests and historical mapping/sample evidence. Parent integration may add its independent relocated `integration-review.json` after these files freeze.

## Portable offline suite

From the repository root, with Python 3.12:

```sh
python3 -m venv /fresh/qa-venv
/fresh/qa-venv/bin/python -m pip install -r collectors/qa/requirements.txt
/fresh/qa-venv/bin/python -B collectors/qa/run_offline.py
```

The routine command writes no reports into the source tree. It uses temporary synthetic run directories, disables Python socket connections in child tests, and invokes mocked production transports. No browser or publisher connection is needed. Nonzero means a test command or machine-readable `passed` assertion failed. For fresh external diagnostic logs:

```sh
python3 -B collectors/qa/run_offline.py --out /fresh/qa-replay-logs
```

The suite includes exact-100 registry faults, wrong-target same-family and wrong-product same-client verification, independent parser edge cases, required nonimage attachment checks, normalized image placeholders, nested image-in-table cells, no-image-fetch production probes, binary/MIME audit faults and all five families’ missing/duplicate/corrupt/wrong-edition/interruption/resume tests. American Legal tests remove a middle branch while retaining all top-level roots; official-source tests crosswire same-byte PDF caches; enCodePlus tests rehash a same-ID body from the wrong publication base.

`test_municode_edges.py` is standard-library-only and returns 2 for any failing probe. The remaining parsers use the dependencies in `requirements.txt`. Exact tested dependency versions are recorded by the suite; family acquisition requirements remain in each adapter directory. Node, Playwright and ordinary Chrome are required for applicable live collection, not these offline tests.

## Image acceptance

The [image policy](../IMAGE-POLICY.md) governs the final scripts. Synthetic tests pass images through real parser entry points and assert source ID/heading retention, literal `[IMAGE]` in text and normalized HTML, inert image markup/data URIs/CSS/poster attributes, preserved nested table cells and no separate known-image acquisition calls. Image-only provisions remain records. Intentional image omission does not make required nonimage attachments optional.

Raw publisher HTML/PDF/ZIP files remain original source evidence and may inherently contain images. Earlier acquisitions made before the policy was reaffirmed are historical and are not final-policy transport proof. `audit_images.py` checks explicitly selected final run directories for nonempty image MIME bodies and PNG/JPEG/GIF/TIFF/WebP/BMP/ICO/AVIF/HEIF/SVG signatures, including files named `.bin`:

```sh
python3 -B collectors/qa/audit_images.py /retained/current-policy-run
```

That read-only audit does not extract native-file internals or render pages. A PDF placeholder count records detected raster image objects without saving pixels. It cannot establish vector illustration coverage, exact reading order, OCR, table fidelity or graphic transcription. These remain format-specific limits.

## Interpretation and limits

- `runnable` means a source-bound, dispatchable configuration. A known government landing page without a qualified inventory/content adapter remains unsupported.
- `family_implementation_tested` means the reusable adapter passed offline production/fault tests. It does not assert a full live run of that target.
- Exact full live text and attachments may be qualified for a selected book while edition currency or all jurisdiction families remain unresolved. The matrix keeps those dimensions separate.
- Full native PDF acquisition and complete page extraction are file/page outcomes. They do not establish legal-section, table, image, OCR or incorporated-standard equivalence.
- Required nonimage refusals, DNS gaps, publisher access stops and explicit limits remain incomplete. The municipal.codes 429 stop and the Syracuse external-host failure are preserved, with no retry or route substitution by QA.
- Jurisdiction coverage remains false. Separate charter/zoning/development/manual families, uncodified legislation and incorporated standards require explicit scope and evidence.

`build_validation_matrix.py` is an authoring tool over explicitly listed retained run directories. It is not part of routine verification and never sends requests. The selected-run ledger records relative evidence-root paths; large source acquisitions stay outside Git, while compact fixtures and proofs remain with the adapters.
