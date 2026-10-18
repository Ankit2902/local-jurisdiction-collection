# Dallas Chapter 51P and Fort Worth zoning source checks

The exact catalog routes were checked using the current official-source HTTP transport. These checks do not qualify a collector or establish publication completeness.

Dallas’s City Attorney landing page returned HTTP 200 but contains an organizational home page and no Chapter 51P publication anchors. The retained official city codes page explicitly links Volume 4 to `http://www.dallascityattorney.com/51P/COV.html`; that exact observed link returned HTTP 404 with an empty body and `WAFRule: 5`. No alternate scheme, path or browser was attempted. The response does not establish that the publication is absent.

Fort Worth’s exact zoning ordinance route returned HTTP 403. The standard transport persisted the host access stop. No retry or alternate route was attempted.

The first Dallas TLS attempt failed before an HTTP response. The same URL succeeded with the installed certifi trusted root bundle and certificate verification enabled. This is recorded separately from publisher refusals.

Original HTML and HTTP receipts are retained. No separate images were acquired, decoded, extracted, rendered or OCRed. Any eventual normalized publication output must use exact `[IMAGE]` placeholders. Both publication inventories and all legal completeness claims remain unqualified.
