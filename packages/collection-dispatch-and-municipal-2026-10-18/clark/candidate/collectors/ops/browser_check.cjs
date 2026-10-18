// Local-only headed Chrome check. Every browser network request is refused.
const {chromium} = require('playwright');
(async () => {
  let browser;
  try {
    browser = await chromium.launch({channel: 'chrome', headless: false});
    const context = await browser.newContext();
    await context.route('**/*', route => route.abort());
    const page = await context.newPage();
    await page.setContent('<html><body><p id="check">collector-runtime-ready</p></body></html>');
    if (await page.locator('#check').innerText() !== 'collector-runtime-ready') throw Error('Local DOM check failed');
    console.log(JSON.stringify({passed: true, headed: true, publisher_requests: 0, chrome: browser.version(), node: process.version}));
  } catch (error) {
    console.error(JSON.stringify({passed: false, error: String(error), action: 'Install Google Chrome and run from a graphical desktop session.'}));
    process.exitCode = 1;
  } finally { if (browser) await browser.close(); }
})();
