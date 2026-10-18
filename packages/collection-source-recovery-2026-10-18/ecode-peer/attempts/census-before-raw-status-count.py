"""Independent original response census: every explicit GUID_content owner.

No producer imports or `.content .content` deletion. Definition/list wrappers
remain owned by their nearest numeric, explicitly identified document body.
"""
import sys
sys.dont_write_bytecode=True
import collections,hashlib,json,re,time
from pathlib import Path
from bs4 import BeautifulSoup,NavigableString,Comment,ProcessingInstruction,Declaration
ROOT=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');SOURCE=ROOT/'outputs/collection-readiness-post-91f6c59-2026-10-17/ecode/albany-image-context-replay-v2';OUT=Path(__file__).resolve().parent
ID=re.compile(r'^([0-9]+)_content$')
def owner(el):
 for a in [el]+list(el.parents):
  if getattr(a,'attrs',None) and ID.fullmatch(a.get('id','')) and 'content' in a.get('class',[]):return ID.fullmatch(a['id'])[1]
 return None
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compact(s):return ''.join(c for c in s if not c.isspace())
start=time.time();cp=json.loads((SOURCE/'checkpoint.json').read_text());valid=[a for a in cp['artifacts'] if a['role'] in ['root-start','content'] and a['status']==200];assert len(valid)==401
ledger={};classes=collections.Counter();totals=collections.Counter();all_witnesses=[];problems=[]
for ai,a in enumerate(valid):
 raw=SOURCE/a['path'];assert sh(raw)==a['sha256'];s=BeautifulSoup(raw.read_bytes(),'html.parser');code=s.find(id='codeContent');assert code is not None
 roots=[e for e in code.find_all(True) if ID.fullmatch(e.get('id','')) and 'content' in e.get('class',[])]
 for e in roots:
  ident=ID.fullmatch(e['id'])[1];text=[];features=collections.Counter();source_ids=[];table_desc=[];image_shapes=[];list_labels=[];legal_nested_content=[];notes=[]
  for item in e.descendants:
   if isinstance(item,NavigableString) and not isinstance(item,(Comment,ProcessingInstruction,Declaration)):
    if owner(item.parent)==ident and not any(getattr(p,'name',None) in ['script','style','button'] or set(p.get('class',[]))&{'actions','selection-control'} for p in item.parents if getattr(p,'attrs',None) is not None):text.append(str(item))
   elif getattr(item,'attrs',None) is not None and owner(item)==ident:
    name=item.name;features['tag:'+name]+=1
    if item.get('id'):source_ids.append(item['id'])
    if 'content' in item.get('class',[]) and not ID.fullmatch(item.get('id','')):legal_nested_content.append({'tag':name,'id':item.get('id'),'classes':item.get('class',[])});classes.update(item.get('class',[]))
    if name=='table':
     rows=[]
     for tr in item.find_all('tr'):
      if tr.find_parent('table') is item:rows.append([{'tag':c.name,'rowspan':str(c.get('rowspan','1')),'colspan':str(c.get('colspan','1')),'source_text':c.get_text()} for c in tr.find_all(['td','th'],recursive=False)])
     table_desc.append({'rows':rows,'source_id':item.get('id')})
    if name in ['img','picture','svg','canvas','image','source','object','embed','input'] or item.get('background') or item.get('poster') or re.search(r'url\s*\(',item.get('style',''),re.I):image_shapes.append({'tag':name,'id':item.get('id'),'type':item.get('type'),'src':item.get('src'),'href':item.get('href'),'style':item.get('style')})
    if name=='a' and re.search(r'\.(png|jpe?g|gif|svg|webp|avif|bmp|ico|tiff?)([?#]|$)',item.get('href',''),re.I):image_shapes.append({'tag':'image-anchor','id':item.get('id'),'href':item['href'],'label':item.get_text()})
    if name=='a' and set(item.get('class',[]))&{'defitem_number','litem_number'}:list_labels.append(item.get_text())
    if set(item.get('class',[]))&{'history','footnote','footnotes','note'}:notes.append({'tag':name,'id':item.get('id'),'classes':item.get('class',[]),'text':item.get_text()})
  body=''.join(text);entry={'owner_id':ident,'raw_path':a['path'],'raw_sha256':a['sha256'],'source_body_id':e['id'],'source_text':body,'source_nonwhitespace_sha256':hashlib.sha256(compact(body).encode()).hexdigest(),'source_nonwhitespace_chars':len(compact(body)),'source_ids':source_ids,'features':dict(features),'tables':table_desc,'nested_legal_content':legal_nested_content,'image_shapes':image_shapes,'list_labels':list_labels,'notes':notes}
  if ident in ledger:
   # Every acquired raw occurrence must agree; no first-witness overwrite hides drift.
   for key in ['source_nonwhitespace_sha256','tables','nested_legal_content','image_shapes','list_labels','notes']:
    if ledger[ident][key]!=entry[key]:problems.append({'id':ident,'field':key,'first':ledger[ident]['raw_path'],'current':a['path']})
  else:ledger[ident]=entry
  all_witnesses.append({'id':ident,'raw_path':a['path'],'source_nonwhitespace_sha256':entry['source_nonwhitespace_sha256']})
 for key in ['img','picture','svg','object','embed','input']:
  totals[key]+=sum(1 for x in code.find_all(key) if owner(x))
 summary={'passed':not problems,'raw_response_count':len(valid),'unique_owner_bodies':len(ledger),'raw_body_occurrences':len(all_witnesses),'nested_legal_content_classes':dict(classes),'raw_image_tag_occurrences':dict(totals),'source_table_count_unique_owners':sum(len(x['tables']) for x in ledger.values()),'source_cells_unique_owners':sum(len(row) for x in ledger.values() for t in x['tables'] for row in t['rows']),'source_note_elements_unique_owners':sum(len(x['notes']) for x in ledger.values()),'owners_with_nested_legal_content':sum(bool(x['nested_legal_content']) for x in ledger.values()),'duplicate_witness_differences':problems,'seconds':time.time()-start,'producer_imports':False,'network_image_decode_pixel_operations':0,'input_checkpoint_sha256':sh(SOURCE/'checkpoint.json'),'census_source_sha256':sh(Path(__file__))}
(OUT/'raw-owner-ledger.json').write_text(json.dumps({'owners':ledger,'all_body_witnesses':all_witnesses},ensure_ascii=False,indent=2)+'\n');(OUT/'raw-census.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));assert not problems
