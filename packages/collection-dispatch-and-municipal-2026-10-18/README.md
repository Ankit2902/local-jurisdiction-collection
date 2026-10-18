# Dispatch, native replay and municipal corpus handoff

This checkpoint carries the image rule into the next standalone handoff paths: exact `[IMAGE]` placeholders, with no separate image requests, extraction, decoding, rendering or OCR. Original publisher HTML/PDF files remain immutable and can intrinsically contain image markup or objects. Available legal text, captions, source identity and order remain part of the output contract.

The final bundle manifest binds the scripts, original source witnesses, independent reviews and exact validation receipts. Configuration qualification remains separate from full legal acceptance.

## Boston zoning discovery

The [source packet](boston/README.md) retains one successful official-page request. Its exact whole-code link points to `https://library.municode.com/ma/boston/codes/redevelopment_authority`. The existing Municode workflow stop applies; no request to that publisher route was made. This establishes routing only. Full code inventory, publisher product identity, edition, export options and acquisition cost remain unknown. The separate zoning-map link remains uncollected. No legal records or executable full-book configuration were inferred from the landing page.

Verify the retained routing packet without network access:

```sh
python3.12 -B packages/collection-dispatch-and-municipal-2026-10-18/boston/verify.py
```

Older sealed evidence packages remain unchanged. A new dispatch configuration or a successful normalized-output replay does not automatically establish current legal edition, full publication semantics or whole-jurisdiction completeness.

## Integrated handoff paths

| Path | Completed validation | Remaining limits |
|---|---|---|
| [Clark Title 30](clark/README.md) | Tested current official group connected to the shared launcher; 30 original PDFs / 381 pages, actual later acquisitions, exact source/config proof bridge and independent review | File/page coverage only; 196 cell disagreements, 43 review pages and legal structure/edition gaps remain |
| [Historical UPOC 2024](upoc-2024/README.md) | New pinned configuration and reusable offline native command; corrected guarded extraction of all 172 pages, 28,603 words and 46 `[IMAGE]` markers; independent review | Historical edition; 102 unresolved text/glyph-comparison pages; no new publisher acquisition or closing sweep |
| [Municipal.codes export](municipal/README.md) | Ordinary Python source-verification helper and 16-column export; all 73 acquired Phoenix Charter bodies and 279 inventory dispositions; independent original-source and portable-package review | 198 source nodes missing, retained 429 stop, no closing sweep; real sample has no images/tables, tested separately with synthetic controls |
| [Boston zoning discovery](boston/README.md) | Exact official page and its whole-code Municode route retained | Publisher workflow stop respected; no whole-code inventory, export or legal records acquired |

The [current method matrix](catalog/publication-method-matrix.json) covers 130 governments and 225 publication entries: **197 dispatchable configurations and 28 unqualified configurations**. The [unqualified list](catalog/unqualified-28.json) is only the configuration backlog. Dispatchable publications can still have access, text, edition or completeness gaps. The catalog contains 154 advisory entries; the new Boston routing observation separately records the existing Municode stop without pretending its unqualified catalog entry is a tested collector.

From a configured repository checkout, the shared launcher can plan the two newly qualified configurations:

```sh
python3.12 collect.py plan --target 96 --publication 96-7e8795b1baee
python3.12 collect.py plan --target 82 --publication 82-8fbdce15716d
python3.12 collect.py plan --all-publications
```

Collection uses `run`, with any global `--runtime` option placed before it. Follow the [owned runtime instructions](../../collectors/ops/README.md), existing publisher stops and the source-specific runbooks. A successful plan does not perform acquisition or certify legal completeness.

## Preserved corrections

The initial UPOC packet in `upoc-2024-initial/` is historical evidence, not the promoted script. An independent stubbed-decoder probe found that its guard missed inline image dictionaries without an explicit image subtype. The final `upoc-2024/` packet blocks those dictionaries before decoding, passes positive text/font controls, and includes a new full 172-page extraction under the corrected source. Its JSONL, CSV and coverage are byte-identical to the initial result; the peer retains the failed probe and correction. Neither the probe nor the corrected extraction decoded image pixels.

Clark's packet likewise retains the failed first catalog integration and an explicitly superseded UPOC composition preview. The promoted source is the eight-file Clark v2 whitelist plus the corrected six-file UPOC whitelist and merged configuration entry. Final combined validation uses that actual integrated source, not the earlier preview. Older sealed packages remain unchanged.
