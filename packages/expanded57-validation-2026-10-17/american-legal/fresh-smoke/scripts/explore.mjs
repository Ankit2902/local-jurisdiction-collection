import {createRequire} from 'node:module'; import fs from 'node:fs'; const req=createRequire(import.meta.url); const {chromium}=req(process.env.PLAYWRIGHT_MODULE||'playwright');const b=await chromium.launch({channel:'chrome',headless:false});const p=await b.newPage();
await p.goto('https://codelibrary.amlegal.com/codes/dallas/latest/dallas_tx/0-0-0-1',{waitUntil:'domcontentloaded'}); await p.waitForTimeout(3500);
console.log((await p.locator('body').innerText()).slice(0,18000)); fs.writeFileSync('raw/dallas-root.html',await p.content());
await p.getByRole('button',{name:'Download',exact:true}).last().click(); await p.waitForTimeout(1000);console.log('MODAL',await p.locator('body').innerText()); fs.writeFileSync('raw/dallas-download-modal.html',await p.content());await b.close();
