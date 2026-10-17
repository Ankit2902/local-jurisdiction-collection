import {createRequire} from 'node:module';
const req=createRequire(import.meta.url); const {chromium}=req(process.env.PLAYWRIGHT_MODULE || 'playwright');
import fs from 'node:fs';
const b=await chromium.launch({channel:'chrome',headless:false}); const p=await b.newPage();
p.on('response',r=>{if(r.url().includes('amlegal')) console.log(r.status(),r.url())});
await p.goto('https://codelibrary.amlegal.com/codes/dallas/latest/overview',{waitUntil:'domcontentloaded'}); await p.waitForTimeout(8000);
console.log((await p.locator('body').innerText()).slice(0,15000)); fs.writeFileSync('raw/dallas-browser-probe.html',await p.content()); await p.screenshot({path:'raw/dallas-browser-probe.png',fullPage:true}); await b.close();
