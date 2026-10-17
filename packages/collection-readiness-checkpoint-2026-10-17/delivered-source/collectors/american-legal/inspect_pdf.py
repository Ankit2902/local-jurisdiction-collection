#!/usr/bin/env python3
"""Offline native-PDF geometry qualification. Original PDF retained; no image binaries extracted."""
import argparse,json,sys,datetime
from pathlib import Path
sys.dont_write_bytecode=True
from model import pdf_pages,digest
from transport import atomic,save

def analyze(data,owner,url):
 rows=pdf_pages(data,owner,url);report={'schema_version':1,'kind':'offline native PDF parser qualification; not a fresh publisher acquisition','source_sha256':digest(data),'source_bytes':len(data),'pages':len(rows),'positioned_pages':sum('layout' in p for p in rows),'text_engine_agreeing_pages':sum(p['layout']['independent_text_characters_equal'] for p in rows),'qualified_reading_order_pages':sum(p['layout']['reading_order_qualified'] for p in rows),'unqualified_reading_order_pages':[p['page'] for p in rows if not p['layout']['reading_order_qualified']],'table_candidate_count':sum(len(p['layout']['table_candidates']) for p in rows),'qualified_ruled_grid_count':sum(t['qualification']=='ruled-grid-geometry' for p in rows for t in p['layout']['table_candidates']),'table_completeness_qualified':False,'semantic_legal_section_completeness_qualified':False,'image_binary_extraction_count':0,'image_policy':'literal-[IMAGE]-no-image-fetch-v1'}
 return b''.join(json.dumps(p,ensure_ascii=False).encode()+b'\n' for p in rows),report

def main():
 p=argparse.ArgumentParser();p.add_argument('--pdf',type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--owner-id',default='publication-pdf');p.add_argument('--source-url',default='retained-native-pdf');p.add_argument('--verify',action='store_true');a=p.parse_args()
 if a.verify:
  meta=json.loads((a.out/'source.json').read_text());data=(a.out/'source.pdf').read_bytes();assert digest(data)==meta['sha256'];body,report=analyze(data,meta['owner_id'],meta['source_url']);assert (a.out/'pdf-pages.jsonl').read_bytes()==body and json.loads((a.out/'analysis.json').read_text())==report,'PDF parser output drift';print(json.dumps(report,indent=2));return
 assert a.pdf and not a.out.exists(),'Supply --pdf and a fresh --out';data=a.pdf.read_bytes();a.out.mkdir(parents=True);atomic(a.out/'source.pdf',data)
 save(a.out/'source.json',{'sha256':digest(data),'bytes':len(data),'owner_id':a.owner_id,'source_url':a.source_url,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'executed_source_sha256':{n:digest((Path(__file__).parent/n).read_bytes()) for n in ['inspect_pdf.py','model.py','pdf_layout.py']}})
 for n in ['inspect_pdf.py','model.py','pdf_layout.py']:atomic(a.out/'scripts'/n,(Path(__file__).parent/n).read_bytes())
 body,report=analyze(data,a.owner_id,a.source_url);atomic(a.out/'pdf-pages.jsonl',body);save(a.out/'analysis.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
