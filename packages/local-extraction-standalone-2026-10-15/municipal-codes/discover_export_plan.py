#!/usr/bin/env python3
"""Construct only advertised public export routes from retained fresh share DOM."""
from pathlib import Path
from urllib.parse import urljoin,urlsplit
import municipal_codes_cli as m
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parent

def discover(root=R/'export-discovery'):
 jobs=[]
 for slug,(_,_,base) in m.ROUTES.items():
  d=root/slug;rp=d/('share-dialog-stable.receipt.json' if (d/'share-dialog-stable.receipt.json').exists() else 'share-dialog.receipt.json');r=m.read_json(rp);raw=d/r['raw_artifact_path'];html=raw.read_text()
  if m.sha(raw.read_bytes())!=r['sha256'] or not r['accepted']:raise m.QualificationError('Unqualified share discovery '+slug)
  soup=m.soup_ok(html);links=[]
  for a in soup.select('a[href]'):
   u=urljoin(r['job']['url'],a['href'])
   if '/export.' not in urlsplit(u).path or u in [v['url'] for v in links]:continue
   if urlsplit(u).netloc!=urlsplit(base).netloc:raise m.QualificationError('Export leaves publisher')
   links.append(dict(url=u,label=a.get_text(' ',strip=True)))
  htmlurl=next((v['url'] for v in links if '/export.html?' in v['url']),None)
  if not htmlurl:raise m.QualificationError('No advertised HTML export')
  jobs.append(dict(slug=slug,section_url=base+'/1.01.010',expected_id='1.01.010',export_url=htmlurl,advertised_exports=links,discovery_receipt=str(rp.relative_to(R)),discovery_raw_sha256=r['sha256']))
 return jobs
if __name__=='__main__':m.write_json(R/'standalone-plan.json',dict(jobs=discover()))
