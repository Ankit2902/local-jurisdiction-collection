# Required non-PDF document semantic acceptance candidate

This isolated candidate extends the reviewed PDF gate to all remaining required nonimage document entries. It is not promoted. Only `publication_acceptance()` changes from exact production launcher20055ae2… to candidate5e2e8544…. All unrelated launcher functions/top-level AST are identical. Production source, retained coverage, publisher stops and Git state remain untouched.

The EP integrity provider `collectors/encodeplus/documents.py`, exactSHAad9a481c…, is copied as `encodeplus-documents.py`. It performs strict PDF integrity checks, but every nonPDF path returns `format: non-PDF binary`, `qualification: nonempty bytes only; document semantics unqualified`. It does not parse DOCX/ZIP legal content or structure. A bounded search of retained next-phase EP coverage found no actual nonPDF integrity entry. The regression exercises this exact source provider with nonempty unit bytes at DOCX/ZIP-labeled URLs; these are synthetic provider-behavior controls, not acquired publisher documents or validated formats.

Every nonPDF/unknown-format entry in the required `asset_document_integrity` map must have `document_text_completeness_qualified` and `document_structure_completeness_qualified` explicitly true. Missing/false/nonboolean values prevent legal/publication acceptance and appear under URL-specific `nonpdf_document_structure_dimensions`. This evaluation follows family-specific aggregate handling, so a family-wide true flag cannot conceal a required document gap. Character conservation alone is not either dimension. Parent HTML text and required binary acquisition remain separately true where applicable.

Existing PDF per-document logic and `pdf_structure_dimensions` remain unchanged. Allfive actual Overland required PDFs still produce conservative incomplete semantic acceptance. No new DOCX/archive/PDF parser or semantic qualification is claimed. Current EP nonPDF integrity provider supplies neither generic true flag; its captured binaries therefore remain semantically incomplete.

Validation passed46tests:7focused candidate controls0.215seconds;30existing launcher acceptance/dependency/native-upgrade tests0.749seconds;4durable current-import nonPDF tests0.064seconds;5durable actual-PDF tests0.084seconds. No PDF/Office/archive extraction, publisher traffic, image fetch/decode/render/OCR, production writes or Git operations occurred.

Review `required-nonpdf-acceptance.patch`. Promotion whitelist:

- `launcher-candidate.py` to `collectors/ops/launcher.py` after root authorization/baseline assertion.
- Durable `test_required_nonpdf_acceptance_current.py` to `collectors/qa/test_required_nonpdf_acceptance.py`.

The durable test SHA is13d1262aaff911a8f1051406c58c782a86c47aa36f026bbe86acdb9e641fab01. It imports current production modules and requires no candidate snapshot. Its optional COLLECTION_TEST_REPO override supports external review. The actual-PDF durable fixture/test from the previous regression package are also exercised unchanged in `test-repository/`.

After promotion from repository root:

```sh
.collection-runtime/venv/bin/python -B -m unittest discover -s collectors/qa -p 'test_required_nonpdf_acceptance.py' -v
.collection-runtime/venv/bin/python -B -m unittest discover -s collectors/qa -p 'test_required_pdf_acceptance.py' -v
PYTHONPATH='collectors/qa:.' .collection-runtime/venv/bin/python -B -m unittest collectors.qa.test_ops_acceptance collectors.qa.test_ops_dependencies collectors.qa.test_native_dispatch_upgrade -v
```

Portable evidence/candidate checks:

```sh
python3 -B /path/to/required-nonpdf-acceptance-candidate-v1/verify_candidate.py
python3 -B /path/to/required-nonpdf-acceptance-candidate-v1/test_required_nonpdf_acceptance.py
```

The copied existing-suite runner and preparation/finalization scripts preserve development orchestration and actual development paths; portable commands above need no project. `run_current_style.py` exercises the durable tests in the included normal source-tree layout. No repeated full-publication tuple or heavy document parse was run.
