# Required PDF semantic acceptance candidate

This isolated candidate corrects a reproduced common-launcher acceptance error. It is not promoted. Only `publication_acceptance()` in `collectors/ops/launcher.py` changes; AST comparison confirms all other launcher functions and top-level code are identical to the captured production source.

The exact retained fresh Overland coverage is copied under `fixtures/overland-coverage.json`, original SHA `dd938b413c9753de5767c5af62d1f636c1ee46ae2489a1079799df4b6dd707dd`. It reports complete parent HTML text and acquired required binaries. Its `asset_document_integrity` maps five PDFs totaling636pages, each explicitly qualified only as readable page-tree/content-stream integrity, with semantics not assessed. The existing launcher misses this map because it checks only three numeric PDF counters; it returns publication and legal-structure acceptance true.

The candidate recognizes PDF entries in that integrity map and requires each document's `pdf_semantic_text_completeness_qualified` and `pdf_table_completeness_qualified` to be explicitly true. Missing values are exposed as null under URL-specific keys in `pdf_structure_dimensions`; false/nonboolean values also fail. Parent aggregate flags cannot supply absent per-document qualification. Actual Overland now returns publication acceptance false and legal structure false, preserving parent HTML text complete and required nonimage document capture complete. No PDF semantics have been newly qualified. Character conservation alone is not either semantic dimension.

`actual-overland-acceptance-comparison.json` retains the exact before/after result using the original coverage bytes. All historical source files/receipts remain unchanged. Root's subsequent common importer successful BEFORE witness uses the same acceptance function revision and remains historical.

Validation: seven focused tests passed0.716seconds, including the actual false-acceptance reproduction, every required document/dimension independently missing/false/nonboolean, aggregate override refusal, no-asset/nonPDF controls, previous numeric PDF behavior and fixture immutability. Thirty existing launcher acceptance/dependency/native-upgrade tests passed0.764seconds against the isolated candidate functions. The synthetic all-explicit-true case tests the acceptance schema only; it does not qualify these actual PDFs. No PDF reparsing, network, image operations, production writes or Git operations occurred.

The promotion whitelist is **only** `launcher-candidate.py` to `collectors/ops/launcher.py`, after root authorizes and confirms the baseline SHA still matches `source-binding.json`. Review the minimal `required-pdf-acceptance.patch`. Production baseline SHA is `32f97985956f44aa7fe0b29996d2c8772ea3a988af9ad4303adad83a66beb8a9`; candidate SHA is `20055ae2ba65157b2acbe9ab04cfbfd8dbae147fbc1886d62cc657b26c0366e6`.

Portable offline checks:

```sh
python3 -B /path/to/required-pdf-acceptance-candidate-v1/verify_candidate.py
python3 -B /path/to/required-pdf-acceptance-candidate-v1/test_required_pdf_acceptance.py
```

The retained `run_existing.py`, `prepare.py` and `finalize.py` describe development orchestration and use actual project paths; the portable commands above need no project or runtime access. The existing suites executed via `run_existing.py` replace their imported launcher object with the isolated candidate, preserving current test code. No current full-publication verification loop was repeated.
