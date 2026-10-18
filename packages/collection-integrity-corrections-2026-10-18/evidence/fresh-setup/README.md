# Fresh shared macOS setup qualification

Current root `collect.py` successfully created a new owned runtime in `runtime-v1`, installed the requirements, launched ordinary headed Google Chrome against a local DOM with all browser requests blocked, then passed `doctor --browser`. No existing `.collection-runtime`, publisher gate, production source or Git state was changed by these commands. No publisher acquisition, image acquisition/decoding/rendering/OCR or gate reset occurred.

Actual commands and exit codes are in `commands.json`. Setup completed exit0 in40.68 seconds; doctor with the independent second local headed Chrome smoke completed exit0 in10.13 seconds. Standalone `pip check` and `pip freeze --all` also completed exit0. There were no setup/doctor failures. This host does not expose `python3.12` on PATH; the documented absolute interpreter option was used with installed Python3.12.14. Ordinary Google Chrome was already installed. These are documented host prerequisites, not a setup defect.

The exact executed shared wrapper/lock/browser-check sources and documentation are retained under `executed-source/`; source hashes before and after are identical. `fresh-runtime-receipt.json` preserves the actual setup receipt, including installed distributions, shim/driver hashes and browser versions. `installed-pip-freeze.stdout` is the observed complete resolved package snapshot, while `executed-source/collectors/ops/requirements.txt` is the authoritative direct-dependency input. The direct requirements are exactly pinned; transitive versions are resolved by pip, then recorded and checked by doctor. Installation used pip's package cache where available; the virtual environment itself was fresh.

Independent local validation in `independent-runtime-audit.json` confirms all11direct pins, all23installed distribution versions matching the setup receipt, and alias-object identity against the actual bundled official API. The fresh profile is Python3.12.14, Python Playwright1.64.0, bundled API build1.64.0-beta-1791568591000, Nodev24.21.0, ordinary Chrome155.0.8059.84. Setup and doctor both report headedtrue, passedtrue and zero publisher requests. The check only displayed local nonimage text; it did not exercise image decoding or publisher transport.

The American Legal standalone profile is distinct. Its package pin is Node Playwright1.62.1; its captured Python lock pins SoupSieve2.8.4 while this fresh shared environment resolves3.0.3. This audit does not claim the profiles are equivalent or supply a new live American Legal transport proof. The family owner is independently qualifying the parser-lock difference.

To reproduce from repository root on a macOS graphical host with Python3.12 and ordinary Chrome installed, choose a new runtime path:

```sh
COLLECTION_PYTHON=/absolute/path/to/python3.12
COLLECTION_RUNTIME=/absolute/path/to/new/collection-runtime
"$COLLECTION_PYTHON" -B collect.py --runtime "$COLLECTION_RUNTIME" setup --python "$COLLECTION_PYTHON"
"$COLLECTION_PYTHON" -B collect.py --runtime "$COLLECTION_RUNTIME" doctor --browser
"$COLLECTION_RUNTIME/venv/bin/python" -B -m pip check
"$COLLECTION_RUNTIME/venv/bin/python" -B -m pip freeze --all
```

The runtime directory is an operational environment, not a relocatable deliverable. `MANIFEST.json` intentionally excludes `runtime-v1/`; compact copied receipts, package snapshots, source bytes and command outputs are included. Preserve the runtime locally as evidence; recreate it with setup on another host rather than moving the virtual environment.

Read-only compact artifact verification works without the runtime or project layout:

```sh
python3 -B /path/to/fresh-setup/verify_evidence.py
```

`run_fresh_setup.py` and `audit_runtime.py` preserve the exact development orchestration and use the actual development paths. Do not rerun `run_fresh_setup.py` over this existing runtime: it deliberately requires a new directory. The generic commands above are the portable runbook. Linux graphical-host and Windows qualification were not attempted; no full-publication completeness claim is made.
