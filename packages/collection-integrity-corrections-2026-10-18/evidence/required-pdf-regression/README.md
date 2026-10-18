# Durable current-import required-PDF acceptance regression

Copy only `test_required_pdf_acceptance.py` to `collectors/qa/test_required_pdf_acceptance.py` and the exact fixture to `collectors/qa/fixtures/overland-required-pdf-coverage.json`. The test imports current production ops code and needs no candidate/baseline layout. Optional `COLLECTION_TEST_REPO` supports external review; installed layout discovers the repository itself.

The exact retained coverage fixture SHA is dd938b413c9753de5767c5af62d1f636c1ee46ae2489a1079799df4b6dd707dd. Five required PDF entries total636pages; parent HTML text and binary capture remain complete, while missing per-document semantics prevent publication acceptance. Tests also cover aggregate override refusal, character-conservation distinction, noasset HTML and nonPDF classification. The nonPDF control asserts no PDF semantic credit, not overall publication acceptance; nonPDF legal acceptance needs its own gate.

Actual current production launcher20055ae2… passed five focused checks and30existing launcher acceptance/dependency/native-upgrade tests. Sources remained unchanged. Logs and exact commands are in `validation-summary.json`. No network, image operations, production edits or Git activity occurred.

After installation from repository root:

```sh
.collection-runtime/venv/bin/python -B -m unittest discover -s collectors/qa -p 'test_required_pdf_acceptance.py' -v
PYTHONPATH='collectors/qa:.' .collection-runtime/venv/bin/python -B -m unittest collectors.qa.test_ops_acceptance collectors.qa.test_ops_dependencies collectors.qa.test_native_dispatch_upgrade -v
```

Source inspection also confirms that EP `documents.qualify_document` returns only `nonempty bytes only; document semantics unqualified` for nonPDF binaries; it does not semantically parse DOCX/ZIP. A bounded search of `coverage.json` files under the retained next-phase EP output found zero actual nonPDF integrity entries. This is a concrete provider limitation, not an invented acquired DOCX/ZIP witness. Parent assigned a separate all-required-document gate candidate; this receipt preserves the earlier PDF-only status.

Portable artifact integrity check: `python3 -B /path/to/verify_regression.py`. Production/runtime is not needed for that check. `run_current.py` preserves exact development commands and uses actual development paths.
