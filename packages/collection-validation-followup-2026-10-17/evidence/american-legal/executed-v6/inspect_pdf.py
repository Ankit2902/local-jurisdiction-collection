#!/usr/bin/env python3
"""Offline native-PDF geometry qualification. Original PDF retained; no image binaries extracted."""
import argparse,json,sys,datetime
from pathlib import Path
sys.dont_write_bytecode=True
from model import pdf_pages,digest
from transport import atomic,save

def analyze(data,owner,url,cache_dir=None):
 rows=pdf_pages(data,owner,url,cache_dir);report={'schema_version':2,'kind':'offline native PDF parser qualification; not a fresh publisher acquisition','source_sha256':digest(data),'source_bytes':len(data),'pages':len(rows),'positioned_pages':sum('layout' in p for p in rows),'text_engine_agreeing_pages':sum(p.get('layout',{}).get('independent_text_characters_equal',False) for p in rows),'qualified_reading_order_pages':sum(p.get('source_qualification',{}).get('source_reading_order_qualified',False) for p in rows),'unqualified_reading_order_pages':[p['page'] for p in rows if not p.get('source_qualification',{}).get('source_reading_order_qualified',False)],'table_candidate_count':sum(len(p.get('layout',{}).get('table_candidates',[])) for p in rows),'tagged_source_table_count':sum(len(p.get('tagged_document',{}).get('tables',[])) for p in rows),'qualified_ruled_grid_count':sum(p.get('source_qualification',{}).get('profile')=='single-closed-native-grid-source-wide-v1' and p['source_qualification']['source_tables_qualified'] for p in rows),'policy_NA_no_text_glyph_pages':[p['page'] for p in rows if p.get('source_qualification',{}).get('policy_not_applicable_to_text_glyph_fidelity',False)],'source_text_completeness_qualified':bool(rows) and all(p.get('source_qualification',{}).get('source_text_qualified',False) for p in rows),'table_completeness_qualified':bool(rows) and all(p.get('source_qualification',{}).get('source_tables_qualified',False) for p in rows),'semantic_legal_section_completeness_qualified':False,'image_binary_extraction_count':0,'image_policy':'literal-[IMAGE]-no-image-fetch-v1'}
 return b''.join(json.dumps(p,ensure_ascii=False,sort_keys=True).encode()+b'\n' for p in rows),report

def main():
 p=argparse.ArgumentParser();p.add_argument('--pdf',type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--owner-id',default='publication-pdf');p.add_argument('--source-url',default='retained-native-pdf');p.add_argument('--verify',action='store_true');p.add_argument('--resume',action='store_true');a=p.parse_args()
 if a.verify:
  meta=json.loads((a.out/'source.json').read_text());data=(a.out/'source.pdf').read_bytes();assert digest(data)==meta['sha256'];body,report=analyze(data,meta['owner_id'],meta['source_url']);assert (a.out/'pdf-pages.jsonl').read_bytes()==body and json.loads((a.out/'analysis.json').read_text())==report,'PDF parser output drift';print(json.dumps(report,indent=2));return
 names=['inspect_pdf.py','model.py','pdf_layout.py','pdf_tags.py','pdf_native.py','pdf_grid.py'];hashes={n:digest((Path(__file__).parent/n).read_bytes()) for n in names}
 if a.resume:
  meta=json.loads((a.out/'source.json').read_text());data=(a.out/'source.pdf').read_bytes();assert digest(data)==meta['sha256'] and hashes==meta['executed_source_sha256'],'Source/parser binding changed';a.owner_id=meta['owner_id'];a.source_url=meta['source_url']
 else:
  assert a.pdf and not a.out.exists(),'Supply --pdf and a fresh --out';data=a.pdf.read_bytes();a.out.mkdir(parents=True);atomic(a.out/'source.pdf',data)
  save(a.out/'source.json',{'sha256':digest(data),'bytes':len(data),'owner_id':a.owner_id,'source_url':a.source_url,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,'executed_source_sha256':hashes})
  for n in names:atomic(a.out/'scripts'/n,(Path(__file__).parent/n).read_bytes())
 body,report=analyze(data,a.owner_id,a.source_url,a.out/'pdf-tag-cache');atomic(a.out/'pdf-pages.jsonl',body);save(a.out/'analysis.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
