Current production is frozen v10, containing the tiny declared-image anchor fix.
`v10-final-integrity.json` verifies all46 production/snapshot file hashes and exact
runtime identity with the131-case tested candidate. Frozen v9 remains unchanged.

The only runtime delta is `model.py`'s a/link image normalization context:
declared image MIME types now cause `[IMAGE]` replacement even for opaque or
`data:application/octet-stream` image URLs. Available label text and source IDs are
retained. Ordinary nonimage document links remain required. No transport/PDF/gate
change, image fetching/decoding/extraction/rendering/OCR or new live work occurred.

Evidence is under `image-context-v10-candidate`: all131-case results, the two new
real `html_record` tests, expected old-v9 failing negative control, and complete
original-native source exposure scan. The Dallas file has24,168 anchors/links;
Cleveland has17,461. Neither contains an anchor/link with the changed declared
image predicate. The hash-bound added branch is therefore unreachable on those
exact inputs, giving unchanged-output equivalence without claiming a fresh replay
or acquisition. Every original proof keeps its original executed revision.

Dallas's separate independent inert Chrome audit now passes583 tables/70,000 cells
with zero mismatches/resource requests; the original source and normalized hashes
remain unchanged. The report is `../qa/dallas-original-native-browser-v3.json`.
339 required nonimage references and the independent closing inventory/edition
check remain actual completion gaps. None of the image policy fixes changes that.

The original serial v7 publisher queue remains untouched. After it finishes and
the persistent gate allows normal work, use frozen current source for a fresh
operator resume of the original failed Dallas run. From the project root, using
the installed collector Python/runtime:

```sh
python outputs/collection-readiness-post-91f6c59-2026-10-17/american-legal/executed-v10/resume_copy.py \
  --from outputs/collection-readiness-followup-2026-10-17/american-legal/primary-4-dallas_tx-v7 \
  --out outputs/collection-readiness-post-91f6c59-2026-10-17/american-legal/dallas-operator-v10
python outputs/collection-readiness-post-91f6c59-2026-10-17/american-legal/executed-v10/verify.py \
  outputs/collection-readiness-post-91f6c59-2026-10-17/american-legal/dallas-operator-v10 --offline
```

That new output must not already exist. The prior `dallas-operator-v9` preparation
is retained as preparation evidence; it has not been executed or promoted as a
complete source run. No current source can bypass persistent403/429/challenge
stops, ignore edition drift, or qualify incomplete attachments by byte retention.
