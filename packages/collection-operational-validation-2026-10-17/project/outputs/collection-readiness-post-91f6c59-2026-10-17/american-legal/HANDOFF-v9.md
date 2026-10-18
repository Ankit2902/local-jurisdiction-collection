American Legal v9 is frozen under `executed-v9`. The production source is
`collectors/american-legal`. The old v8 freeze is retained in `prior-freeze-v8`.
`v9-final-tests.json` records129 passing cases from the promoted production files.
`v9-source-delta.json` identifies every changed file; publisher transport, browser,
rate gate, PDF source parsers and all v8 image metadata guards are unchanged.

Dallas's original live v7 run remains failed and immutable. It retained the
44,379,988-byte native HTML export SHA256
`05062096efe74785be55c8a0198c9734894ce7b02265ef45b53b28118174f35e`.
Its independent start inventory has4,542 nodes and588 expanded branches. v9's
offline source normalization retains all53,570 rich blocks plus two Notes headings
and their two source-bound footnote tables. The independent original-DOM Python
audit matches all583 tables/70,000 cells. Separate inert-Chrome QA is pending and
must not be inherited from this Python audit.

The source and full normalized output directories are listed by relative path in
`v9-promotion.json`. Its normalized sections hash is
`91b4e6b2f3a4ec5f4a2528a79e7432260d9d0c2ce6bf3dbf18143f6c07e2208a`.
`v9-image-policy-actual.json` binds123 literal `[IMAGE]` text placeholders, no
active image elements/data-image payloads, and no transport/image-decode calls.
Original native HTML may contain images; no separate image bytes are acquired,
decoded, extracted, rendered or OCRed. Available nonimage text remains retained.

Dallas is **not complete**:339 required nonimage references still need genuine
acquisition/qualification, followed by the independent closing inventory/edition
check. `dallas-operator-v9` is a fresh prepared clone only; verification must fail
until it finishes. No new publisher requests were sent by this v9 proof work.

The original serial queue continues from immutable v7, with runner78376 and
FortWorth child85179 alive at23:51:27UTC. FortWorth had491 start-inventory
requests; Dallas was the only earlier terminal job and12 primaries had not started.
Do not restart the queue, reset its shared gate or run a duplicate publisher job.

After that queue finishes and the persistent gate permits normal work, resume the
already prepared Dallas clone using the frozen v9 source. From the project root:

```sh
python outputs/collection-readiness-post-91f6c59-2026-10-17/american-legal/executed-v9/collect.py \
  --url https://codelibrary.amlegal.com/codes/dallas/latest/dallas_tx \
  --jurisdiction Dallas --state TX --publication dallas_tx --identity-alias Dallas \
  --strategy native --assets download \
  --out outputs/collection-readiness-post-91f6c59-2026-10-17/american-legal/dallas-operator-v9 --resume
python outputs/collection-readiness-post-91f6c59-2026-10-17/american-legal/executed-v9/verify.py \
  outputs/collection-readiness-post-91f6c59-2026-10-17/american-legal/dallas-operator-v9 --offline
```

For another original run, `resume_copy.py --from ORIGINAL --out FRESH` checks raw
hashes/current image policy, preserves the original directory/history, and performs
the copy plus ordinary live resume. `--prepare-only` issues no requests and prints
the exact command. Original source edition drift is rejected. No access-stop bypass
or retry is implicit; explicit nonimage unavailable-response retry remains gated.

The isolated `title33-index-folio-v1` directory records33 exact source chapter-row
associations on physical page10 only, preserving the source526/525-1 mismatch.
It is not integrated into official production, and never qualifies all1,855 pages,
reconstructs rejected table cells, or waives source disagreement.
