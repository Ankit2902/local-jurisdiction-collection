# Standalone runtime diagnostics

`RUNTIME-FINDINGS.json` distinguishes observed requester/mode-dependent responses from runtime failures. No sealed acquisition package was changed.

The successful controls are fresh, ordinary standalone sessions: Gridics returned HTTP 200 and its expected publisher UUID containers with both Playwright's bundled Chromium 148 and installed Chrome 155 in headless mode. Each context started with zero cookies. The one distinct CodePublishing experiment used ordinary bundled Chromium 148 headed and still received HTTP 403 / Cloudflare challenge, with zero cookies before and after. This is evidence of a conditional site/platform response, not a global inability to run a browser or complete TLS. It does not establish the underlying denial cause or prove every headed/browser version is blocked.

Separate family-agent receipts show ordinary installed Chrome headed could acquire municipal-code pages where earlier headless/HTTP attempts failed. They also show actual advertised downloads can work through normal UI clicks when direct `page.goto` produces download-related errors. Bellingham later returned 429, so its earlier success is a single capture, not a stable repeated success. `prior-evidence/` holds sanitized, source-hash-bound summaries of those receipts; those experiments were not repeated here.

## Portable setup and commands

Python 3.12 is the current tested review environment. The retained older control used Python 3.9.6 / Playwright 1.60.0. Installed package metadata says Playwright 1.64.0 requires Python >=3.10; keep the browser installation matched to the chosen library release. Use external runtime/cache directories:

```sh
python3 -m venv /tmp/standalone-runtime-venv
/tmp/standalone-runtime-venv/bin/python -m pip install -r requirements.txt
PLAYWRIGHT_BROWSERS_PATH=/tmp/standalone-browser-cache \
  /tmp/standalone-runtime-venv/bin/python -m playwright install chromium
/tmp/standalone-runtime-venv/bin/python runtime_diagnostics.py inspect --out environment.json
```

For Linux provision the required OS browser dependencies with the vendor's `python -m playwright install --with-deps chromium` instructions. Headed execution needs a graphical session; Linux CI can use an administrator-provisioned Xvfb environment. Windows/macOS need a supported desktop installation; `--engine chrome` additionally requires the ordinary installed Chrome channel. No browser/profile is bundled. The official [browser documentation](https://playwright.dev/python/docs/browsers) explains matched binaries, branded channels and their differing headless implementations; see [supported systems](https://playwright.dev/python/docs/intro#system-requirements) and [CI setup](https://playwright.dev/python/docs/ci). Only macOS arm64 was actually tested here; Windows/Linux are documented provisioning paths, not live qualifications.

Read-only environment inspection requires only the standard library. It records versions, proxy/CA presence and TLS backend without printing proxy URLs, credential values or CA paths. It does not inspect the user's browser profile, cookie store or private keychain. Browser probes create isolated contexts, inspect only their own fresh cookie names/counts, and close them. No cookie values, storage state, authentication profile, custom user agent, stealth flag, proxy rotation or disabled certificate check is used.

A single explicitly approved public-source diagnostic can be run as follows, into a new output folder:

```sh
PLAYWRIGHT_BROWSERS_PATH=/tmp/standalone-browser-cache \
  /tmp/standalone-runtime-venv/bin/python runtime_diagnostics.py probe \
  --url 'https://codehub.gridics.com/us/ca/cupertino#/90d493fe-25f4-4aef-a519-710b1e0055c6' \
  --engine chromium --expect-selector 'div.section[data-path]' \
  --out /tmp/runtime-probes/approved-control
```

Use `--engine chrome` for the installed ordinary channel, or `--headed` for an explicitly approved distinct display-mode experiment. The script never runs a runtime matrix or retries automatically. It stops on 401/403/429/503 and challenge/denial documents. A successful navigation status without the expected source selector is not source acceptance. Diagnostic exit code 0 means a receipt was written; read `result`, `http_status`, and `expected_selector_found` for the outcome. This helper tests ordinary documents; download responses need a download handler rather than a DOM-navigation selector.

Run diagnostic jobs sequentially. All jobs in a diagnostic batch must share `--host-ledger` (default: output parent `HOST-STOP.json`). HTTP 429 records the exact `Retry-After` header if present and stops every later job on that requested hostname. There is **no automatic retry after the indicated time**. A repeated identical URL/engine/mode experiment is also refused. The retained ledger already stops ecode360.com, sonoma.municipal.codes and bellingham.municipal.codes based on family-agent 429 evidence. Missing original `Retry-After` values remain unknown; no request was made to recover them. Do not reset the ledger to retry a challenged or throttled publisher.

## Offline independent verification

```sh
python3 -m unittest discover -s . -p test_runtime_diagnostics.py -v
python3 build_findings.py
```

The four regressions verify credential/proxy redaction, transient URL-query redaction, a full fake-browser HTTP 429 path capturing `Retry-After`, and refusal of a different route on the stopped host before a browser request/import. These tests make no network requests. `build_findings.py` reruns them, verifies retained live raw hashes and executed-source hashes, and regenerates `RUNTIME-FINDINGS.json` from this self-contained evidence folder. No workspace/project absolute path is a runtime dependency. `experiment-commands.json` retains the exact execution paths used for this investigation; portable installation commands are above.

`executed-runtime_diagnostics-v1.py` is the source that performed the three actual live experiments. The final `runtime_diagnostics.py` adds metadata URL-query redaction; its network, browser and host-stop behavior is unchanged and covered by offline tests. The CodePublishing receipt's transient challenge query was transparently redacted after capture, retaining the original receipt hash and exact title/status/body hash. That metadata adjustment is not a new live qualification of a different browser configuration.

## Operator initialization and downloads

None of the successful standalone controls or cited municipal headed captures required operator actions, imported cookies or a persistent browser profile. There is no evidence here that manual initialization is generally necessary. A dedicated persistent profile might be an operator workflow, but challenge completion, authentication initialization and session portability remain **unvalidated**. No such profile or challenge interaction was implemented. Managed CUA success must not be converted into a claim that copying its user profile would yield a legitimate standalone route.

For publisher downloads, ordinary UI-triggered attachment handling should use the [documented download event](https://playwright.dev/python/docs/downloads) and save the received file before closing its context. A `Download is starting`/navigation error is not, by itself, a publisher denial. Source-specific export scripts and their byte/parser verification remain owned by the family packages.

Package exclusions are `__pycache__/`, any optional `.venv/`, `.browsers/`, `node_modules/`, browser cache or persistent-profile/storage-state directory. None of those runtimes/profiles were created inside this diagnostics folder.
