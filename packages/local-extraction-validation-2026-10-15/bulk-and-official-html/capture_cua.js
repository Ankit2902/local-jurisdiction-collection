// Run in the supported Codex CUA REPL, after binding an authorized observed tab.
// Inputs: existing tab handle, absolute output filename chosen by operator.
// No network fetches, hidden application state, access bypass, or new tab management.
async function captureOfficialDOM(tab, absoluteFilename) {
  const fs = await import('node:fs/promises');
  const metadata = await tab.playwright.evaluate(() => ({
    url: location.href, title: document.title,
    chars: document.documentElement.outerHTML.length,
    encoding: document.characterSet
  }));
  const parts = [];
  for (let offset = 0; offset < metadata.chars; offset += 60000) {
    parts.push(await tab.playwright.evaluate(({start}) =>
      document.documentElement.outerHTML.slice(start, start + 60000), {start: offset}));
  }
  const html = parts.join('');
  if (html.length !== metadata.chars || !html.endsWith('</html>') || html.includes('[Truncated]')) {
    throw new Error('Incomplete DOM capture; no output written');
  }
  await fs.writeFile(absoluteFilename, html, {encoding:'utf8', flag:'wx'});
  await fs.writeFile(absoluteFilename + '.capture.json', JSON.stringify({
    ...metadata, retrievedAt: new Date().toISOString(), transport:'Codex CUA DOM',
    retainedEncoding:'UTF-8', originalHttpBytesRetained:false, chunkChars:60000
  }, null, 2), {encoding:'utf8', flag:'wx'});
  return metadata;
}
