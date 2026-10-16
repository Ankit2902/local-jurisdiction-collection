#!/usr/bin/env python3
"""Offline prepare bounded real-source replay manifests and source-validation exports."""
from pathlib import Path
import datetime
from bs4 import BeautifulSoup
import municipal_codes_cli as m
ROOT=Path(__file__).resolve().parent

def main():
 for slug,(name,discovery,base) in m.ROUTES.items():
  d=ROOT/'evidence'/slug
  chapter=d/('live-chapter-ready.html' if (d/'live-chapter-ready.html').exists() else 'live-chapter.html')
  contents=d/'live-contents-full.html'
  contents_hash=m.sha(contents.read_bytes())
  html=chapter.read_text();rows,notes=m.parse_page(html,base+'/1.01.010',base)
  m.write_json(d/'live-parsed.json',{'records':rows,'notes':notes})
  soup=BeautifulSoup(html,'html.parser');currency=soup.select_one('.site-footer');currency=currency.get_text(' ',strip=True) if currency else ''
  m.write_json(d/'live-chapter-receipt.json',{'source_url':base+'/1.01.010','transport':'Codex IAB rendered DOM via CUA, own tab','http_status':None,'retrieved_at':datetime.datetime.fromtimestamp(chapter.stat().st_mtime,datetime.timezone.utc).isoformat(),'sha256':m.sha(chapter.read_bytes()),'section_cards':sum(r['node_kind']=='section' for r in rows),'parent_bodies':sum(r['node_kind']!='section' for r in rows),'raw_currency_text':currency,'legal_currency_normalized':None})
  # Current full DOM only; never substitute August inventory into a current replay.
  try:inv=m.inventory(contents.read_text(),base+'/contents',base,'main > ul.contents-toc')
  except m.QualificationError as e:
   m.write_json(d/'inventory-block.json',{'status':'blocked_or_shell','reason':str(e),'whole_corpus_complete':False});continue
  if not inv['nodes']:
   m.write_json(d/'inventory-block.json',{'status':'empty_inventory','whole_corpus_complete':False});continue
  inv.update(source_raw_path=contents.name,source_raw_sha256=contents_hash)
  for n in inv['nodes']:
   n.update(jurisdiction_slug=slug,publication_id='municipal-code',source_version='snapshot-2026-10-15:'+contents_hash,raw_artifact_path='raw/inventory-source.html',raw_sha256=contents_hash)
  m.write_json(d/'inventory.json',inv)
  publications=[]
  pubhtml=d/'live-publications.html'
  for anchor in BeautifulSoup(pubhtml.read_text(),'html.parser').select('main a[href]'):
   href=anchor.get('href','')
   if href.startswith('/') and href.count('/')==1 and '?' not in href and href not in [x['path'] for x in publications]:publications.append({'publication_id':('municipal-code' if href=='/'+base.split('/',3)[3] else 'publisher:'+href[1:]),'raw_artifact_path':'live-publications.html','raw_sha256':m.sha(pubhtml.read_bytes()),'path':href,'title':anchor.get_text(' ',strip=True),'source_url':base.split('/',3)[0]+'//'+base.split('/')[2]+href,'scope_disposition':'unresolved','evidence':'live-publications.html','reason':'Observed family retained; complete family inventory and substantive qualification pending'})
  m.write_json(d/'publications-discovery.json',publications)
  manifest={'jurisdiction_slug':slug,'jurisdiction':name,'publication_id':'municipal-code','publication_title':name+' Municipal Code','publication_base':base,'source_version':'snapshot-2026-10-15:'+contents_hash,'raw_currency_text':currency,'publication_families_scope':'unresolved; municipal-code only bounded validation','discovered_publications':publications,'retrieved_at':datetime.datetime.fromtimestamp(chapter.stat().st_mtime,datetime.timezone.utc).isoformat(),'inventory':{'path':'inventory.json','sha256':m.sha(m.canonical(inv)),'raw_path':contents.name,'raw_sha256':contents_hash},'snapshots':[{'path':chapter.name,'source_url':base+'/1.01.010','sha256':m.sha(chapter.read_bytes())}]}
  m.write_json(d/'replay-manifest.json',manifest)
  out=ROOT/'examples'/slug
  # Deliberately new output name required after parser/config changes; stale checkpoints must fail.
  m.replay(d/'replay-manifest.json',out)
  print(slug,len(inv['nodes']),len(rows))
if __name__=='__main__':main()
