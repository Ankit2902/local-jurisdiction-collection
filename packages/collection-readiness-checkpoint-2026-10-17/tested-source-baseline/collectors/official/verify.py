#!/usr/bin/env python3
"""Read-only offline source/inventory/output verification, including incomplete-run detection."""
import sys
sys.dont_write_bytecode=True
import argparse,csv,json,pathlib
import collect,model

def verify(run):
 run=pathlib.Path(run).resolve();coverage=collect.reconcile(run);state=collect.load(run/'checkpoint.json');expected=[]
 for item in state['items']:
  p=run/'items'/(model.sha(item['id'].encode())[:24]+'.json')
  if p.exists():expected+=collect.load(p)['records']
 stored=(run/'records.jsonl').read_bytes()
 if stored!=collect.lines(expected):raise ValueError('Global normalized output missing/duplicate/corrupt records')
 with (run/'records.csv').open(newline='') as f:
  csv.field_size_limit(32_000_000);rows=list(csv.DictReader(f))
 if len(rows)!=len(expected) or any(row['id']!=r['id'] or row['text']!=r['text'] for row,r in zip(rows,expected)):raise ValueError('CSV/JSONL roundtrip mismatch')
 if (run/'coverage.json').exists() and collect.load(run/'coverage.json')!=coverage:raise ValueError('Stored coverage differs from recomputed evidence')
 qualified=[r['pdf_qualification'] for r in expected if r.get('pdf_qualification')]
 if qualified:
  coverage['pdf_text_table_qa']={'qualified_page_count':len(qualified),'all_pdf_pages_have_coordinate_qa':len(qualified)==sum(r['unit']=='pdf_page' for r in expected),'extractable_text_reconciled':all(q['source_word_ownership_complete'] and q['normalized_source_word_characters_agree'] and q['independent_text_engine_characters_agree'] and not q['unmapped_or_private_use_codepoints'] for q in qualified),'source_word_count':sum(q['source_word_count']for q in qualified),'detected_table_count':sum(q['detected_table_count']for q in qualified),'detected_table_cells':sum(q['detected_table_cells']for q in qualified),'independently_agreeing_table_cells':sum(q['independent_table_cells_agree']for q in qualified),'all_detected_table_cells_independently_agree':all(q['detected_table_cells']==q['independent_table_cells_agree'] for q in qualified),'recovered_invalid_decoder_glyphs':sum(len(q['invalid_decoder_glyph_resolutions'])for q in qualified),'page_review_conditions':{r['id']:r['pdf_qualification']['review_conditions'] for r in expected if r.get('pdf_qualification',{}).get('review_conditions')},'reading_order_manual_review_required':True,'all_tables_detected_or_semantically_complete':False,'legal_semantic_coverage_complete':False,'qualification_limit':'Two independent text engines, physical word ownership and detected table cells reconciled; arbitrary borderless tables, diagrams, legally correct reading order and section interpretation remain review. No pixels/render/OCR.'}
 return coverage
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run',type=pathlib.Path);a=p.parse_args()
 try:
  r=verify(a.run);print(json.dumps({'offline':True,'read_only':True,'coverage':collect.brief(r),**({'pdf_text_table_qa':r['pdf_text_table_qa']} if 'pdf_text_table_qa' in r else {})},indent=2));raise SystemExit(0 if r['requested_coverage_complete'] else 3)
 except Exception as e:print(json.dumps({'offline':True,'read_only':True,'error':str(e)}));raise SystemExit(3)
