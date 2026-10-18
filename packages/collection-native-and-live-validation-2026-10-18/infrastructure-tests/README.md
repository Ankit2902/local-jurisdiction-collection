# Production-shaped Infrastructure tests

This companion adds no runtime parser change. It adapts the reviewed canonical packet's24 tests only to normal repository module/fixture paths. The same exact reviewed five runtime hashes are asserted by `run_tests.py`.

Promotion payload:

- `test_infrastructure_contents.py` → `collectors/encodeplus/test_infrastructure_contents.py`
- `fixtures/infrastructure-four-region/selected-ir.json.gz` → the same relative path under `collectors/encodeplus/`

The deterministic gzip fixture is594,578bytes of source text/glyph/query geometry and original selected-page record metadata. It contains no native PDF/image payload or separately acquired image. Raw source remains in the sealed evidence packet. `PROVENANCE.json` binds its exact uncompressed IR/source/query packet and runtime hashes.

The production-shaped companion passed24 tests in13.541seconds against the exact reviewed canonical runtime. Before promotion, repeat from any working directory:

```
<python> -B <companion>/run_tests.py --runtime <canonical-v2>/candidate
```

After promoting the reviewed runtime and these two payloads, run from repository root:

```
<python> -B -m unittest collectors.encodeplus.test_infrastructure_contents -v
```

The tests make no PDF parse or network/image request. They check actual known source fixtures, canonical JSON/CSV, exact old44failed-cell/five-field diagnostic restoration, source ownership/pins/namespaces, atomic refusal, query/spacing faults, and image preservation. They do not assert whole-book semantics.
