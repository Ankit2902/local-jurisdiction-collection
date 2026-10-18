# Repository-ready named enCodePlus configuration regression

`test_named_encodeplus_binding.py` is ready to copy to `collectors/qa/test_named_encodeplus_binding.py`. It imports current repository modules and current actual enCodePlus target/Overland registry data. It requires no candidate/baseline snapshot layout. All configuration mutations are confined to a temporary repository; a socket tripwire prevents network use in the focused suite.

Seven checks cover the exact named configuration source/key and argv, selected entry plus whole-file SHA, actual `overland.scope` mutation using an unchanged plan, changes to another entry, missing file/key/nonobject configuration, unexpected or ambiguous source, and unaffected other-family component input scope.

The focused test failed against production before promotion as expected (`current-prepromotion.stderr`), passed in a normal installed-layout staging tree, and passed against actual promoted production (7 tests in 1.257 seconds). Six existing ops/readiness/dispatch suites also passed against actual production; their exact command, source hashes and logs are retained in `current-production-validation.json` and `production-existing.stderr`. The earlier `validation-summary.json` records prepromotion preparation; it is historical, not the current status receipt.

No production files were written by these checks. No publisher collection, image access/decoding/rendering/OCR, Git operations or readiness promotion occurred. Root owns copying the single durable test into the repository. The previous candidate package remains immutable.

After copying, from repository root:

```sh
.collection-runtime/venv/bin/python -B -m unittest discover -s collectors/qa -p 'test_named_encodeplus_binding.py' -v
```

The tested existing suite command, from repository root:

```sh
PYTHONPATH="collectors/qa:." .collection-runtime/venv/bin/python -B -m unittest collectors.qa.test_ops_acceptance collectors.qa.test_ops_dependencies collectors.qa.test_readiness_binding collectors.qa.test_native_dispatch_upgrade collectors.qa.test_originals_dispatch collectors.qa.test_readiness_catalog -v
```

To run the uninstalled durable test against a current repository, set `COLLECTION_TEST_REPO=/path/to/repository` and execute the test file with `python -B`. This override is optional and used only for external review; an installed test locates the normal repository from its own location.

The read-only artifact verifier runs with `python3 -B /path/to/verify_regression.py`. `prepare_and_run.py` and `run_current.py` preserve development orchestration provenance and use development paths; portable commands above do not depend on those paths.
