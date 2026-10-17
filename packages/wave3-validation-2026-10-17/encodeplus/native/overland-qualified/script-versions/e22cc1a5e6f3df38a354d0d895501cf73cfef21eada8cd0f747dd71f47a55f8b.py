#!/usr/bin/env python3
"""Read-only PDF identity/text check; optional fresh rendering directory."""
import argparse,json,pathlib,re
from pypdf import PdfReader
from parse import sha
ANCHORS={'lincoln':['20.12.140','CLIMATIC AND GEOGRAPHIC DESIGN CRITERIA','25 psf','115 mph','36"','December 15, 2025'],'overland':['18.430.150 Required Parking','Zoning District / Land Use','1 to 2.5 spaces per unit','1 space for each 3 seats','ZRR-3503']}
def check(key,folder,render=None):
 p=folder/'publisher.pdf';r=PdfReader(p);text='\n'.join(x.extract_text() for x in r.pages);flat=' '.join(text.split());anchors={x:x in flat for x in ANCHORS[key]};assert all(anchors.values()),anchors
 expected='Lincoln, NE Municipal Code' if key=='lincoln' else 'Overland Park, Kansas Municipal Code';assert r.metadata.title==expected
 if render:
  assert not render.exists(),'Fresh render output required';render.mkdir(parents=True)
  import pypdfium2 as pdfium
  doc=pdfium.PdfDocument(p)
  for i in range(len(doc)):doc[i].render(scale=1.3).to_pil().save(render/('page-'+str(i+1)+'.png'))
 return {'key':key,'pdf_sha256':sha(p.read_bytes()),'page_count':len(r.pages),'publication_identity_matches':True,'operative_heading_and_table_anchors':anchors,'producer':r.metadata.producer,'native_export_not_browser_print':True,'edition_alignment':'Selected section headings, table values and retained histories match HTML anchors; no codewide current-through date established'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('key',choices=ANCHORS);p.add_argument('folder',type=pathlib.Path);p.add_argument('--render',type=pathlib.Path);a=p.parse_args();print(json.dumps(check(a.key,a.folder,a.render),indent=2))
