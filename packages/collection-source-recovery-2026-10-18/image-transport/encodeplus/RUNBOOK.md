This isolated candidate inserts `.strip()` at the two existing enCodePlus transport image MIME classifiers. Padded image MIME cannot trigger an error-body or successful-body read; ordinary text/PDF responses remain readable. Status/header/stop handling, request timing, locks and redirects are unchanged. No reset or retry option is added.

From this packet root:

```sh
python -B -m unittest candidate.collectors.encodeplus.test_transport_image_mime -v
```

The same durable test after parent-controlled promotion is:

```sh
python -B -m unittest collectors.encodeplus.test_transport_image_mime -v
```

The tests patch network access and use fresh automatically removed temporary gates; no existing real gate is consulted or modified. They use ASCII sentinels, not image pixels, and perform no image decoding/rendering/extraction/OCR. Baseline execution preserves four expected failure subcases; final four methods/eight cases pass. Promote only the two files in `PROMOTION-WHITELIST.json`; `util.py` and `__init__.py` copies are unchanged import context, not promotion deltas.
