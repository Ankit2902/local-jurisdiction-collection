"""Exact source-bound Word/HTML literal variants; does not guess glyph meaning from font names."""
import argparse,collections,json,re,sys,zipfile,xml.etree.ElementTree as E
from pathlib import Path
from bs4 import BeautifulSoup
from source_common import *
from king_normalize import blocks
from model import dom_text
from word_model import W,NS
PAT=re.compile(r'\[SYMBOL ([0-9A-Fa-f]+)\]')
def matching(word_text,html_text):
 parts=PAT.split(word_text)
 if len(parts)==1:return None
 expression='^'+''.join(re.escape(x) if i%2==0 else '(.)' for i,x in enumerate(parts))+'$';m=re.fullmatch(expression,html_text,re.S)
 if not m:return None
 return [{'word_char_hex':parts[2*i+1],'published_html_character':ch,'html_unicode':'U+'+format(ord(ch),'04X')} for i,ch in enumerate(m.groups())]
def run(html_source,word_source,normalized,out):
 hs=Path(html_source).resolve();ws=Path(word_source).resolve();norm=Path(normalized).resolve();out=Path(out).resolve()
 if out.exists():raise ValueError('Fresh symbol-audit file required')
 hc=load(hs/'checkpoint.json');wc=load(ws/'checkpoint.json');hh={a['source_url']:a for a in hc['artifacts'] if a['role']=='content'};ww={a['document_id']:a for a in wc['artifacts'] if a['role']=='native-word'}
 rows=[];html_cache={};word_cache={};table_counter=collections.Counter();comparison_count=0
 for line in (norm/'records.jsonl').open():
  record=json.loads(line);doc=record['source_document_id']
  if record['kind']=='table':table_index=table_counter[doc];table_counter[doc]+=len(record['tables'])
  if not PAT.search(record.get('text','')):continue
  if doc not in hh or doc not in ww:raise ValueError('Wrong native/HTML source identity')
  if doc not in html_cache:
   a=hh[doc];raw=(hs/a['path']).read_bytes()
   if sha(raw)!=a['sha256']:raise ValueError('Corrupt original HTML')
   bs=BeautifulSoup(decode(raw)[0],'html.parser');html_cache[doc]=([(n,dom_text(n)) for n in blocks(bs.body)],bs.body.find_all('table'))
   a=ww[doc];raw=(ws/a['path']).read_bytes()
   if sha(raw)!=a['sha256'] or record['source_native_sha256']!=a['sha256']:raise ValueError('Corrupt/wrong native Word')
   with zipfile.ZipFile(__import__('io').BytesIO(raw)) as z:body=E.fromstring(z.read('word/document.xml')).find('w:body',NS)
   word_cache[doc]=list(body)
  node=word_cache[doc][record['source_ordinal']]
  if sha(E.tostring(node))!=record['source_xml_sha256']:raise ValueError('Record XML source binding mismatch')
  fonts=[{'font':e.get('{'+W+'}font'),'char_hex':e.get('{'+W+'}char')} for e in node.iter('{'+W+'}sym')]
  result={'record_id':record['record_id'],'source_document_id':doc,'native_source_sha256':ww[doc]['sha256'],'html_source_sha256':hh[doc]['sha256'],'source_xml_sha256':record['source_xml_sha256'],'word_source_ordinal':record['source_ordinal'],'word_literal':record['text'],'original_symbol_metadata':fonts,'status':'unresolved_literal_pair','glyph_semantics_qualified':False,'pairs':[]}
  candidates=[]
  if record['kind']=='table':
   if len(record['tables'])!=1:raise ValueError('Nested symbol table unprofiled')
   ht=html_cache[doc][1][table_index];hrows=ht.find_all('tr',recursive=False) or ht.select(':scope > tbody > tr')
   wt=record['tables'][0]['rows'];pairs=[];valid=len(hrows)==len(wt)
   for ri,wrow in enumerate(wt):
    hcels=hrows[ri].find_all(['td','th'],recursive=False) if ri<len(hrows) else []
    if len(hcels)!=len(wrow):valid=False;continue
    for ci,wcell in enumerate(wrow):
     if not PAT.search(wcell['text']):continue
     hcell=hcels[ci];m=matching(wcell['text'],dom_text(hcell));comparison_count+=1
     if m is None:valid=False
     else:pairs.append({'table_index':table_index,'row_index':ri,'cell_index':ci,'html_literal':dom_text(hcell),'html_cell_sha256':sha(str(hcell).encode()),'source_html_fragment':str(hcell),'variants':m})
   if valid and pairs:candidates=[{'pairs':pairs}]
  else:
   prefix=PAT.split(record['text'])[0]
   for i,(hnode,htext) in enumerate(html_cache[doc][0]):
    if hnode.name=='table' or prefix and not htext.startswith(prefix):continue
    m=matching(record['text'],htext)
    if m is not None:candidates.append({'html_block_index':i,'html_literal':dom_text(hnode),'source_html_fragment':str(hnode),'html_block_sha256':sha(str(hnode).encode()),'variants':m})
   comparison_count+=1
  result['candidate_count']=len(candidates)
  if len(candidates)==1:result.update(status='exact_same_document_literal_variant_bound',pairs=candidates)
  rows.append(result)
 result={'schema':'king-font-literal-source-pair-1','complete':False,'literal_variant_binding_complete':bool(rows) and all(r['status']=='exact_same_document_literal_variant_bound' for r in rows),'font_glyph_semantics_complete':False,'scope':'Exact same-document source XML and HTML unit/cell conservation only. Literal variants and source declared fonts retained; no font-name-only Unicode glyph substitution, no image/member rendering. Does not waive source publication/update/dependency gaps.','records_with_symbols':len(rows),'comparisons':comparison_count,'bound_records':sum(r['status']=='exact_same_document_literal_variant_bound' for r in rows),'unresolved_records':sum(r['status']!='exact_same_document_literal_variant_bound' for r in rows),'image_members_opened':0,'rows':rows,'code_fingerprint':{n:sha((Path(__file__).parent/n).read_bytes()) for n in ['king_symbol_audit_v3.py','model.py','king_normalize.py','word_model.py','source_common.py','source_dispositions.json']}};save(out,result);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--html-source',required=True);p.add_argument('--word-source',required=True);p.add_argument('--normalized',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=run(a.html_source,a.word_source,a.normalized,a.out);print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2));sys.exit(2)
