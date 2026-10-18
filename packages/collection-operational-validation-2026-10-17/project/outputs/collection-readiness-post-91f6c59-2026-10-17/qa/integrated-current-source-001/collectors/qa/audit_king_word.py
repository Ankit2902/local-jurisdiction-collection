"""Independent actual OOXML run joins/tables/notes; never open embedded media members."""
import argparse,collections,hashlib,io,json,re,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def sha(b):return hashlib.sha256(b).hexdigest()
def clean(s):return ' '.join(s.split())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--normalized',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh report required')
 records_raw=(a.normalized/'records.jsonl').read_bytes();groups=collections.defaultdict(list)
 for line in records_raw.splitlines():r=json.loads(line);groups[r['source_url']].append(r)
 cp=json.loads((a.source/'checkpoint.json').read_text());errors=[];symbols=[];results=[];opened=[];counts=collections.Counter()
 def text(node):
  tag=node.tag.removeprefix(W)
  if tag in ('drawing','pict','object'):counts['image_occurrences']+=1;return '[IMAGE]'
  if tag=='t':return node.text or ''
  if tag=='tab':return '\t'
  if tag in ('br','cr'):return '\n'
  if tag=='noBreakHyphen':return '\u2011'
  if tag=='softHyphen':return '\u00ad'
  if tag=='sym':
   code=node.get(W+'char');font=node.get(W+'font','');symbols.append({'font':font,'code':code})
   if font.lower().replace(' ','')=='couriernew' and code in ('0022','002D'):return chr(int(code,16))
   return '[SYMBOL '+code+']'  # Exact typed source code; Unicode meaning remains unqualified.
  value=''.join(text(c) for c in node)
  if tag in ('p','tr','tc'):value+='\n'
  return value
 def table(node):
  rows=[]
  for tr in node.findall(W+'tr'):
   row=[]
   for tc in tr.findall(W+'tc'):
    grid=tc.find('./'+W+'tcPr/'+W+'gridSpan');merge=tc.find('./'+W+'tcPr/'+W+'vMerge');row.append({'text':clean(text(tc)),'colspan':grid.get(W+'val') if grid is not None else '1','vertical_merge':merge.get(W+'val','continue') if merge is not None else None})
   rows.append(row)
  return {'rows':rows}
 for item in cp['artifacts']:
  if item['role']!='native-word':continue
  raw=(a.source/item['path']).read_bytes();assert sha(raw)==item['sha256'];rs=groups[item['source_url']];assert all(r['source_native_sha256']==item['sha256'] for r in rs)
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   # Explicit allowlist: embedded media and OLE members are never read/extracted.
   xml=z.read('word/document.xml');opened.append({'native_sha256':item['sha256'],'member':'word/document.xml','sha256':sha(xml)});body=ET.fromstring(xml).find(W+'body');units=list(body);owned={r['source_ordinal']:r for r in rs if 'source_ordinal' in r}
   if set(owned)!=set(range(len(units))):errors.append({'url':item['source_url'],'kind':'body_unit_ownership','source':len(units),'owned':len(owned)})
   for ordinal,node in enumerate(units):
    r=owned.get(ordinal);counts['body_units']+=1
    if r is None:continue
    expected=clean(text(node));got=clean(r['text'])
    if expected!=got:errors.append({'url':item['source_url'],'ordinal':ordinal,'kind':'inline_run_text','source':expected,'normalized':got})
    if node.tag==W+'tbl':
     expected_table=table(node);tables=r.get('tables',[]);counts['tables']+=1;counts['rows']+=len(expected_table['rows']);counts['cells']+=sum(map(len,expected_table['rows']))
     if len(tables)!=1 or expected_table!=tables[0]:errors.append({'url':item['source_url'],'ordinal':ordinal,'kind':'table_cells','source':expected_table,'normalized':tables})
   for kind,member in [('footnote','word/footnotes.xml'),('endnote','word/endnotes.xml')]:
    if member not in z.namelist():continue
    content=z.read(member);opened.append({'native_sha256':item['sha256'],'member':member,'sha256':sha(content)});note_rows={r['source_id']:r for r in rs if r['kind']==kind}
    for note in ET.fromstring(content):
     ident=note.get(W+'id');r=note_rows.get(ident)
     if r is None:
      if ident not in ('-1','0'):errors.append({'url':item['source_url'],'kind':'unowned_note','note_id':ident})
      continue
     counts['notes']+=1
     if clean(text(note))!=clean(r['text']):errors.append({'url':item['source_url'],'kind':'note_text','note_id':ident,'source':clean(text(note)),'normalized':r['text']})
  results.append({'url':item['source_url'],'native_sha256':item['sha256'],'source_units':len(units),'owned_records':len(rs)})
 report={'passed':not errors,'script_sha256':sha(Path(__file__).read_bytes()),'normalized_records_sha256':sha(records_raw),**counts,'documents':results,'members_opened':opened,'font_symbol_observations_including_repeated_table_checks':dict(collections.Counter(str(s) for s in symbols)),'source_symbol_semantics_qualified':not any(s['font'].lower().replace(' ','')!='couriernew' for s in symbols),'errors':errors,'image_or_ole_members_opened':0,'network_requests_sent':0,'scope':'Actual native OOXML run/table/span/merge/note conservation only; exact [SYMBOL hexadecimal] placeholders preserve unresolved private font codes, not qualified Unicode glyph meaning; no Word rendering, pixel/OLE member read, image fetch, extraction or OCR. Date/dependency/source-closing gaps remain independent.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],**counts,'errors':len(errors),'sample':errors[:2]}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
