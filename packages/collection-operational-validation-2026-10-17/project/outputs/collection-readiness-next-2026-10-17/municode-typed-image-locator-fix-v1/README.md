# Narrow Municode typed image locator metadata fix

Root identified a concrete policy failure: a known `<img>` whose src is a data:application/octet-stream URI becomes literal [IMAGE], but its encoded bytes remained in normalized omission attributes. The isolated regression reproduced that failure before the patch. It also confirmed the same already-classified image locator could survive in source-reference/coverage metadata, including a split opaque srcset payload and video poster reference.

The change is limited to image_policy.py/model.py plus the new test_typed_image_locators.py:

- Already-classified image omissions redact data URIs in typed src/data/srcset/href/xlink:href/style/background/poster attributes, regardless of MIME spelling. Metadata keeps original string SHA256, MIME, locator and character count; no payload decoding occurs.
- Source references pass image context into the same helper. Opaque data:srcset references stay whole instead of inventing a second URL from the comma-separated encoded bytes. Poster/background reference attributes are typed image context.
- Alt/caption/prose and ordinary nonimage metadata retain their previous values. Generic nonimage data URI metadata and document references remain unchanged. Source API bytes and raw source hashes remain original. No scanner, transport, access-stop or image-acquisition path was added or changed.

Before-patch negative logs are retained. The final isolated suite passed34tests12.976seconds: three new targeted tests,27existing fault/pipeline tests, and four existing Notes regressions. Exact production promotion copied only three owned Municode files after checking baseline hashes. The new three tests then passed against production in1.032seconds. No Git, database, other-family file, prior package, or original source was changed.

The new tests call the actual sanitizer for all named typed locators and CSS/poster paths; assert payload absence plus exact source locator hashes; preserve alt/prose/nonimage metadata; and exercise real reconcile/write/verify behavior while checking raw source still contains the original fixture bytes. They use fake transport and no publisher network, image decoding, image rendering, extraction or OCR. This finite fix is not a fresh full-publication acquisition claim.

`promotion.json` gives exact before/after source hashes. `runtime.patch` is the narrow runtime delta. The executable candidate includes the unchanged supporting modules and one existing source-bound Jacksonville fixture for the reused fault suite.

Readonly proof verification from this directory: `python -B verify_fix.py`. To reproduce the finite suite with the existing Python3.12.14/pypdf6.21.1 environment, run from candidate: `python -B -m unittest -v test_typed_image_locators test_faults test_note_image_boundaries`.
