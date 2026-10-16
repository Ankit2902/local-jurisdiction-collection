#!/usr/bin/env python3
"""Render the reviewed table/transcription outputs for source visual comparison."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--package',required=True);p.add_argument('--out',required=True);args=p.parse_args();package=Path(args.package);out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
blocks=[json.loads(x) for x in next((package/'layout').glob('*/blocks.jsonl')).read_text().splitlines()];selected=[b for b in blocks if b.get('review_id')]
import html
body=''.join('<h2>'+html.escape(b['review_id'])+'</h2>'+(b['html'] if b['kind']=='table' else '<p>'+html.escape(b['text'])+'</p>') for b in selected)
doc='<!doctype html><meta charset="utf-8"><style>body{font:18px serif;max-width:1000px;margin:30px}table{border-collapse:collapse;width:100%}td,th{padding:8px;border:1px solid #333}h2{margin-top:32px}</style>'+body
(out/'reviewed-output.html').write_text(doc)
with sync_playwright() as pw:
 browser=pw.chromium.launch(channel='chrome',headless=True);page=browser.new_page(viewport={'width':1100,'height':1400});page.set_content(doc);page.screenshot(path=str(out/'reviewed-output.png'),full_page=True);browser.close()
