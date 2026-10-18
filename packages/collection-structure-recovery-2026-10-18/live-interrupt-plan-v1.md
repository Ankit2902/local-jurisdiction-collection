# Current-code Flagstaff ordinary Chrome interruption/resume plan

Status: prepared, not started. Root must first signal that the integrated production family, registry/shared launcher, runtime receipt and configuration bytes are frozen. Existing stops remain authoritative. This plan does not authorize a stop reset or alternative publisher route.

## Exact operation

Run from the repository root, using a fresh output:

```sh
.collection-runtime/venv/bin/python -B collect.py --runtime .collection-runtime run --target original-flagstaff-az --out '/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/outputs/collection-readiness-next-2026-10-17/originals-integration/flagstaff-common-live-recovery-v1'
```

After the deliberately interrupted attempt terminates, repeat exactly the same command. The common launcher owns the existing job and appends `--resume` to the actual family command. Do not edit any checkpoint, job, code fingerprint, source identity, gate or source response. Do not request a code upgrade or use a replay source on this live job.

## Interruption and evidence

1. Record final production/shared/config/runtime hashes, exact command, common process handle/PID, host gate state and request-log byte offset. Check existing stop state using the normal common preflight. Keep the frozen v7 and old live evidence immutable.
2. Launch the common operation with its own process handle. Identify the descendant process whose argv exactly invokes `collectors/originals/cli.py collect` with the selected Flagstaff config and this fresh output. Record its parent chain back to the owned common process. Never signal a global browser, another task, a process group or a PID selected only by process name.
3. Poll the atomically written `source/checkpoint.json`. Require the actual opening currency marker and at least three distinct HTTP200 `content` receipts. Verify the corresponding body files against their retained hashes. The checkpoint must have no errors/blocks. A source refusal/challenge/429 immediately terminates this plan; preserve it and do not resume.
4. Save an immutable observation outside the collection output: source/main checkpoint copies and hashes, every existing artifact path/hash, opening inventory/currency, content count, exact owned PID/argv and process ancestry. Signal SIGINT once to that exact family child. The count may increase between observation and graceful shutdown; preserve the final observed count rather than forcing an exact three-body claim.
5. Wait for the common attempt to terminate. Preserve the incomplete common job and acquisition/verification logs. The family may propagate KeyboardInterrupt through the registry as a translated exit status; record actual statuses, not an assumed value. Confirm the family `finally` saved source state and closed its own context/browser. Record the owned browser/driver PID subtree before and after; do not restart while an owned browser remains active. No global quit/pkill is allowed.
6. Snapshot the terminated generation before resume, including the durable source checkpoint and cached-body hashes. No synthetic checkpoint changes are made. Record gate state after the interruption; do not clear it.
7. Repeat the exact common command. The real ordinary Chrome source path must perform its retained-source hash checks plus fresh root/18TOC/currency resume validation, skip every durable cached body, acquire the remaining source bodies, perform complete fresh closing checks, normalize and run the common verifier. Preserve any edition/inventory drift as a failure; do not relax gates to finish.
8. At terminal, compare every previously retained body hash, opening and closing inventories/roots/currency, source URLs, source body ownership, typed notes, tables, image placeholders and runtime/config hashes. Reconcile the publisher request-log slice and actual source receipt timestamps. Explicitly demonstrate no resumed content request for a body already durable at interruption. Do not require equality with the old publisher edition if the source has changed; report drift honestly.
9. Expect sound incomplete acceptance if the three current publisher broken-anchor occurrences persist. A full method/source-transport recovery can pass while publication acceptance remains false. Preserve the actual common terminal status, not a manufactured exit0. New source/record hashes need exact independent review or a proved byte bridge before reusing prior source-dimension passes.

## No-image controls

The ordinary browser blocks image/font/media resources. No separate image URL is fetched, no Word media member is read and no image is decoded/rendered/OCRed. Every normalized image position is exact `[IMAGE]`, with source IDs/captions retained and pixel payload metadata redacted. Audit actual raw MIME receipts and all delivered normalized records/notes/links/assets after terminal; native original HTML may intrinsically contain image references.

## Remaining earlier initialization boundary (do not change v7)

The current fresh `collect.main` writes `collection-start.json`, its executed runtime snapshot and the typed collection-root `checkpoint.json` before source acquisition starts. Thus a full collection-root marker exists before the first publisher network request.

However, `flagstaff_html.collect` then creates `source/inventory-origin` and calls `flagstaff_inventory.run`. The native inventory phase writes an executed source snapshot before its first request, but it does not have an incremental resumable inventory state. Its final receipt/selected-frame inventory is written only after the workflow unwinds/completes. The first `source/checkpoint.json` is written only after inventory returns and `roots_and_readers` validates it.

An actual interruption in this earlier phase can therefore leave a valid collection-root start marker and a nonempty partial `source/inventory-origin`, without `source/checkpoint.json`. On the next same-code common run, the family resumes its main marker, selects `flagstaff_html.collect(resume=False)` because the source checkpoint is absent, and safely refuses the nonempty source directory as `Fresh output required`. It neither resumes nor deletes that source. This is an operational recovery gap, not absence of all pre-network markers.

This live test intentionally interrupts after at least three durable bodies and does not claim the earlier boundary is fixed. After the real transport proof, a separate candidate must give initial inventory a durable phase/checkpoint and explicit safe generation recovery, preserving partial original responses and existing stops. It needs an actual process interruption in the initial inventory phase and same-command resume test, without checkpoint editing, before promotion. No v7 changes are proposed in this plan.

## Scope and platform

The earlier two completed actual process tests used the real collection state machine with an explicit recorded-source fake transport backend. They do not satisfy this new live Chrome/publisher recovery dimension. Only macOS26.6.2 arm64/Python3.12.14 with the recorded ordinary Chrome installation has been tested. This plan makes no cross-platform or whole-jurisdiction completion claim.
