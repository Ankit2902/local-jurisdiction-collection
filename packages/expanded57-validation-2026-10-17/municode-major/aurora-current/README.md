# Aurora current publisher validation

This is a self-contained bounded general City Code validation collected2026-10-17 in one authorized ordinary headed Chrome session. The official city page labels its link “Unified Development Ordinance” and links the publisher root. The live root is **Aurora City Code** and separately exposes `/Code`, `/UDO` and `/Charter`. The tested substantive sample is **general City Code chapter1 articleI**, not a UDO substitute.

The source and native publisher HTML both state: **The Aurora City Code is current through Ordinance2026-42, passed August10,2026.** Fifteen operative sections1-1 through1-15 normalize to JSONL/CSV. The reserved1-16 through1-35 heading has no body; it is retained in raw evidence and parser notes and is explicitly excluded from the operative record count. No full-corpus claim is made.

`result.json` is an integration-ready sequence35 result object. All paths are relative to this Aurora package root; prefix them when copying into another package. The major group should add its prior Municode Product-not-found and empty/disabled ClientContent evidence to the integrated row. The old five-target ICC package was left unchanged.

For read-only offline verification, install the two extra parser dependencies if needed. Root’s bundled Python already has lxml/pypdf, but this copied reviewed parser uses **beautifulsoup4 and requests**. Playwright/pypdf are not needed for offline replay.

```sh
python -m pip install -r requirements-offline.txt
python verify_aurora.py
```

The verifier writes only to a temporary directory, verifies raw/native hashes, requires byte-identical replay of `evidence/sample/records.jsonl` and `records.csv`, and verifies all fifteen native HTML citations/bodies equal their live DOM counterparts. Expected output includes `records:15`, `live_replay_byte_equal_jsonl_csv:true`, `native_html_citations_bodies_equal:true`, `table_count:0`, `complete_corpus:false`.

`evidence/sample/native-export-records.jsonl` and `.csv` contain the normalized native HTML export. They are identical to the fifteen live records after offline equivalence qualification. The original native file is `publisher-export-0.html`; `publisher-export.json` binds its filename, size, SHA256 and the source-observed publisher endpoint.

For a future authorized live repeat, work in a fresh copy of this package and install `requirements.txt` (or the exact tested `requirements-lock.txt`). A graphical desktop and installed Google Chrome are required. The command validates both follow-up URLs against links observed in that same fresh browser session:

```sh
printf '%s\n' 'https://aurora.municipal.codes/Code/1' 'https://aurora.municipal.codes/Code/1_ArtI' | python aurora_probe.py --out fresh/aurora
```

A new empty output directory is mandatory. There is one browser launch, root discovery, then two observed document navigations with at least3seconds explicit pause. Ordinary publisher assets/redirects are browser managed. A429 persists `CURRENT-HOST-STOP.json` and stops further same-host requests. A persistent challenge stops the single attempt. No challenge solving, proxy, profile reuse, imported browser state or CUA is used. `evidence/executed-aurora_probe.py` is the exact executed driver. The runtime and final response chronology are retained. The initial HTTP403 and official city route evidence are copied with receipts from the major group. `resumption-authorization.json` records root’s explicit new phase after the earlier Bakersfield429 cooldown.

Additional publication families `/UDO` and `/Charter` are discovered only. Tables do not occur in this sample, so complex table geometry is not tested. Images and no-body/reserved source nodes follow the reviewed parser’s existing conservative behavior. `collect.py` and `lib/` are copied portable helpers; no prior package is imported at runtime.
