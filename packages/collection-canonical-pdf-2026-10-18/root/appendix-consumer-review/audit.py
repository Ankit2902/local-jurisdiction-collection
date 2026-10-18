"""Independent Appendix B canonical consumer audit; no parser/native/network imports."""
import collections,csv,hashlib,json,sys
from pathlib import Path
F=['tables','ordered_blocks','text','ordering','pdf_qualification']
def demand(v,m):
 if not v:raise AssertionError(m)
def audit(rows,base,csvrows):
 c=collections.Counter(); changed=[]
 demand(len(rows)==len(base)==len(csvrows)==636,'record count')
 for r,b,cr in zip(rows,base,csvrows):
  demand(r['id']==b['id']==cr['id'],'ordered identity')
  demand(all(cr[k]==str(r.get(k,'')) for k in cr),'CSV differs')
  demand(r['image_placeholder_count']==b['image_placeholder_count'],'image count')
  demand([x for x in r['ordered_blocks'] if x['kind']=='image_placeholder']==[x for x in b['ordered_blocks'] if x['kind']=='image_placeholder'],'image positions')
  c['image_placeholders']+=r['image_placeholder_count']
  if r.get('canonical_structure_selection',{}).get('profile')!='sto_appendix_b':
   demand(r==b,'unselected changed');c['unchanged_records']+=1
  else:
   c['selected_records']+=1; changed.append(r['physical_page']);s=r['canonical_structure_selection'];z=r['source_appendix_b_schedules'][0]
   demand(s['authoritative_fields']==F and s['source_evidence_id']==z['id'],'selection fields/evidence')
   demand(s['source_sha256']==r['raw_sha256']==b['raw_sha256'] and s['source_url']==r['source_url'] and s['physical_page']==r['physical_page'],'source binding')
   demand(r['superseded_detector_diagnostics']['original_record_fields']=={k:b[k] for k in F},'old fields changed')
   demand(all(r[k]==b[k] for k in b if k not in F),'original other fields changed')
   demand(len(r['tables'])==1 and s['canonical_table_ids']==[r['tables'][0]['id']],'canonical table selection')
   t=r['tables'][0];cells={x['id']:x for x in z['cells']};tablelines=[x for x in z['physical_lines'] if x['kind'] in ['header_top','header_bottom','printed_data_line']]
   expectedids=[i for x in tablelines for i in x['cell_ids']]
   demand([x['id'] for x in t['cells']]==expectedids,'source cells/order')
   demand(t['header_rows']==[i for i,x in enumerate(tablelines) if x['kind'] in ['header_top','header_bottom']],'physical headers reordered')
   demand(t['header_rows']==([0,1] if r['physical_page']==198 else [1,2]),'preheader data lost')
   for i,x in enumerate(t['cells']):
    sc=cells[x['id']]
    demand((x['row'],x['column'],x['rowspan'],x['colspan'])==(i//3,i%3,1,1),'invented span/order')
    demand(x['text']==sc['text'] and x['word_ids']==sc['source_word_ids'] and x['source_glyph_ids']==sc['source_glyph_ids'],'cell source text/owners')
    demand(x['extraction_bbox']==sc['extraction_bbox'] and x['independent_pdfium_text']==sc['independent_native_text'],'cell query geometry/text')
    demand(x['kind']==sc['kind'] and x['role']==sc['role'],'cell role')
   demand(t['source_description_is_reference_only_not_legal_description'] is True and t['logical_rowspan_generated'] is False,'source caveat/blank policy')
   sourceblocks=[];table_seen=False
   for line in z['physical_lines']:
    if line in tablelines:
     if table_seen:continue
     sourceblocks.append(('table','\n'.join('\t'.join(cells[i]['text'] for i in q['cell_ids']) for q in tablelines),expectedids));table_seen=True
    else:
     demand(len(line['cell_ids'])==1,'non-table source shape');i=line['cell_ids'][0];sourceblocks.append(('text',cells[i]['text'],[i]))
   demand([(x['kind'],x['text']) for x in r['ordered_blocks']]==[(k,v) for k,v,ids in sourceblocks],'block physical order/text')
   demand(r['text']=='\n'.join(v for k,v,ids in sourceblocks),'canonical page text')
   for block,(kind,value,ids) in zip(r['ordered_blocks'],sourceblocks):
    demand(block['word_ids']==[i for cellid in ids for i in cells[cellid]['source_word_ids']],'block word order')
    demand(block['source_glyph_ids']==[i for cellid in ids for i in cells[cellid]['source_glyph_ids']],'block glyph order')
   w=[i for x in r['ordered_blocks'] for i in x['word_ids']];g=[i for x in r['ordered_blocks'] for i in x['source_glyph_ids']]
   demand(collections.Counter(w)==collections.Counter(x['id'] for x in z['source_words']),'word ownership')
   demand(collections.Counter(g)==collections.Counter(x['id'] for x in z['source_glyphs']),'glyph ownership')
   c['words']+=len(w);c['glyphs']+=len(g);c['table_cells']+=len(t['cells']);c['source_physical_cells']+=len(cells)
   c['context_blocks']+=sum(x['kind']=='text' and x.get('source_kind')=='printed_context_line' for x in r['ordered_blocks'])
   c['folio_blocks']+=sum(x['kind']=='text' and x.get('source_kind')=='printed_folio' for x in r['ordered_blocks'])
   q=r['pdf_qualification'];demand(q['detected_table_count']==1 and q['detected_table_cells']==q['independent_table_cells_agree']==len(t['cells']),'canonical counts')
   for k in ['unmapped_or_private_use_codepoints','undecoded_cid_literals','independent_text_engine_characters_agree']:demand(q[k]==b['pdf_qualification'][k],'decoding diagnostic altered')
  original=r.get('superseded_detector_diagnostics',{}).get('original_record_fields',r)
  c['all_original_false_cells']+=sum(not x['independent_character_agreement'] for t in original['tables'] for x in t['cells'])
  c['canonical_false_cells']+=sum(not x['independent_character_agreement'] for t in r['tables'] for x in t['cells'])
 demand(changed==list(range(198,204)),'selected page scope')
 demand(c['all_original_false_cells']==795 and c['canonical_false_cells']==44 and c['image_placeholders']==201,'total diagnostics/images')
 return dict(c)
def main():
 records,baseline,export,out=map(Path,sys.argv[1:]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p):sha(p) for p in [records,baseline,export]}
 rows=[json.loads(x) for x in records.read_text().split('\n') if x];base=[json.loads(x) for x in baseline.read_text().split('\n') if x]
 with export.open(newline='') as f:csvrows=list(csv.DictReader(f))
 c=audit(rows,base,csvrows);demand(before=={str(p):sha(p) for p in [records,baseline,export]},'inputs changed');demand(not out.exists(),'fresh report required')
 out.write_text(json.dumps({'passed':True,'counts':c,'input_hashes':before,'script_sha256':sha(Path(__file__)),'scope':'Independent actual JSON/CSV consumer audit; finite source proofs and full-publication acceptance separate','image_or_network_operations':False},indent=2)+'\n');print(json.dumps(c))
if __name__=='__main__':main()
