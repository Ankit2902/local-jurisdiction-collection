# Everett currency correction

The sealed earlier E2E package remains unchanged. Its combined footer selector selected the article statutory footnote before the site footer. The wrong `currency_before` and `currency_after` value was:

> 1 For statutory provisions authorizing cities to codify their ordinances, see RCW 35.21.500 — 35.21.570 . For the Charter provisions requiring the mayor to cause the annual codification of ordinances, see § 15.6 .

The corrected before and after site-footer notice, also present in the new standalone publisher HTML export, is:

> The Everett Municipal Code is current through Ordinance 4203-26, passed September 16, 2026.

All three notices are equal. This corrects which text supports the sampled edition comparison; it does not qualify whole-corpus completion. The new helper prefers explicit `#site-footer` and refuses missing current-through text.

| Evidence | Raw SHA256 |
|---|---|
| live-final/everett-wa/chapter.html | 2026231800da47b12aa80ddfa99f205848c47a611de7e4aec54a2e8d75b31677 |
| live-final/everett-wa/version-after.html | 7409d3d486c6180afabbcf1eb979f3260f1ea3d1a050814ac559bce12d0b2907 |
| headed-ui-export/everett-wa/download.html | 68072312db8eb594a55b15f73f6f746bbaeac0fba3a121ed7760f5b5705c51df |

Exact prior report fields, acquisition receipt paths and original report hash are recorded in `CURRENCY-CORRECTION.json`.
