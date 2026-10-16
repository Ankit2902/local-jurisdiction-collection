import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {sha256Browser} from './sha256_browser.mjs';
for(const value of ['', 'abc', 'Unicode 🏛 café', '\ud800 lone\udfff', 'a'.repeat(100000)])assert.equal(sha256Browser(value),createHash('sha256').update(value).digest('hex'));
const html='a'.repeat(39999)+'🏛'+'z'.repeat(100);const chunks=[];for(let i=0;i<html.length;i+=40000)chunks.push(html.slice(i,i+40000));assert.equal(createHash('sha256').update(chunks.join('')).digest('hex'),sha256Browser(html));
console.log('6 SHA256 / UTF16 chunk regression cases passed');
