"""Independent raw DOM owner/text/table/note/ID conservation; no collector imports."""
import sys
sys.dont_write_bytecode=True
import json,re,hashlib,collections
from pathlib import Path
from bs4 import BeautifulSoup,Tag,NavigableString,Comment,Declaration,ProcessingInstruction
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return [json.loads(x) for x in p.read_text().split('\n') if x]
def characters(text):return re.sub(r'\s+','',text.replace('[IMAGE]',''))
def text(el):return characters(el.get_text('',strip=False))
def excluded(el):
 for n in [el]+list(el.parents):
  if not isinstance(n,Tag):continue
  if n.name in ['script','style','button','input','noscript','img','picture','svg','image','canvas']:return True
  if set(n.get('class',[]))&{'actions','selection-control'}:return True
  if n.name in ['object','embed'] and (n.get('type','').strip().lower().startswith('image/') or re.search(r'\.(png|jpe?g|gif|svg|webp|avif|tiff?)(?:[?#]|$)',n.get('data') or n.get('src') or '',re.I)):return True
  if n.name=='source' and (n.find_parent('picture') or n.get('srcset') or n.get('type','').strip().lower().startswith('image/')):return True
 return False
def owner(el,known):
 for n in [el]+list(el.parents):
  if isinstance(n,Tag) and n.get('id') in known:return n['id'][:-8]
 return None
def signature(el):return (el.name,el.get('id'),tuple(el.get('class',[])),el.get('rowspan'),el.get('colspan'),el.get('scope'),el.get('headers'))
def table_profile(t):
 return [(n.name,n.get('rowspan'),n.get('colspan'),text(n)) for n in t.find_all(['table','caption','thead','tbody','tfoot','tr','th','td'])]
def main():
 root=Path(sys.argv[1]);out=Path(sys.argv[2]);allow='--expect-incomplete' in sys.argv
 cp=json.loads((root/'checkpoint.json').read_text());records=lines(root/'records.jsonl');by={r['id']:r for r in records};seen={};checks=[];raws=0
 for a in cp['artifacts']:
  assert sha(root/a['path'])==a['sha256']
  if a['role'] not in ['root-start','content'] or a['status']!=200:continue
  raws+=1;s=BeautifulSoup((root/a['path']).read_bytes(),'html.parser');code=s.select_one('#codeContent');assert code is not None
  bodies={e['id'][:-8]:e for e in code.find_all(id=re.compile(r'^[0-9]+_content$')) if 'content' in e.get('class',[])};known={k+'_content' for k in bodies}
  for ident,body in bodies.items():
   if ident not in by:continue
   r=by[ident];assert a['path'] in r['raw_witnesses'];assert ident not in seen;seen[ident]=a['path']
   # Assign each raw node to the nearest explicitly identified body. Legal
   # .content classes without independent GUID IDs remain in their own parent.
   elements=[n for n in [body]+body.find_all(True) if owner(n,known)==ident and not excluded(n)]
   strings=[str(n) for n in body.descendants if isinstance(n,NavigableString) and not isinstance(n,(Comment,Declaration,ProcessingInstruction)) and owner(n,known)==ident and not excluded(n.parent)]
   expected_text=characters(''.join(strings));normal=BeautifulSoup(r['content_html'],'html.parser');normal_elements=[n for n in normal.find_all(True) if not excluded(n)];actual_text=text(normal)
   ids=collections.Counter(n['id'] for n in elements if n.get('id'));actual_ids=collections.Counter(n['id'] for n in normal_elements if n.get('id'))
   source_tables=[n for n in elements if n.name=='table'];normal_tables=normal.find_all('table');table_equal=len(source_tables)==len(normal_tables)==len(r['tables_html']) and all(table_profile(x)==table_profile(y)==table_profile(BeautifulSoup(z,'html.parser').find('table')) for x,y,z in zip(source_tables,normal_tables,r['tables_html']))
   note_classes={'history','footnote','footnotes','note'};source_notes=[n for n in elements if set(n.get('class',[]))&note_classes];normal_notes=[n for n in normal_elements if set(n.get('class',[]))&note_classes];notes_equal=len(source_notes)==len(normal_notes)==len(r['notes_html']) and all(text(x)==text(y)==text(BeautifulSoup(z,'html.parser')) for x,y,z in zip(source_notes,normal_notes,r['notes_html']))
   semantic=BeautifulSoup(r['semantic_html'],'html.parser');check={'id':ident,'raw_path':a['path'],'raw_sha256':a['sha256'],'source_legal_text_characters':len(expected_text),'normalized_legal_text_characters':len(actual_text),'text_equal':expected_text==actual_text,'canonical_semantic_text_equal':expected_text==text(semantic),'legal_DOM_signature_equal':[signature(x) for x in elements]==[signature(x) for x in normal_elements],'source_ID_count':sum(ids.values()),'normalized_ID_count':sum(actual_ids.values()),'ID_multiset_equal':ids==actual_ids,'source_tables':len(source_tables),'tables_equal':table_equal,'source_notes':len(source_notes),'notes_equal':notes_equal,'source_nonGUID_content_nodes':sum('content' in n.get('class',[]) and not re.fullmatch(r'[0-9]+_content',n.get('id','')) for n in elements)};checks.append(check)
 assert set(seen)==set(by),'Some acquired rich body has no raw source owner'
 failures=[c for c in checks if not all(c[k] for k in ['text_equal','canonical_semantic_text_equal','legal_DOM_signature_equal','ID_multiset_equal','tables_equal','notes_equal'])]
 report={'schema':1,'passed':not failures,'input':str(root),'raw_successful_HTML_artifacts':raws,'owned_records':len(checks),'source_tables':sum(c['source_tables'] for c in checks),'source_note_elements':sum(c['source_notes'] for c in checks),'source_ID_occurrences':sum(c['source_ID_count'] for c in checks),'nonGUID_legal_content_nodes':sum(c['source_nonGUID_content_nodes'] for c in checks),'failed_owner_count':len(failures),'checks':checks,'failures':failures,'policy':'Graphics/UI omitted only as explicit sourcepolicy; whitespace projected away for character conservation, DOM/table/note/ID order compared separately. No rendered-layout/wordspacing or browser audit added.','collector_imports':0,'image_or_network_operations':0};out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['checks','failures']}));assert allow or not failures
if __name__=='__main__':main()
