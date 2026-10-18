"""Exact source-XML/context/PDF-ToUnicode recoveries. No global font substitution or image APIs."""
import argparse,collections,io,json,re,struct,sys,unicodedata
from pathlib import Path
from pypdf import PdfReader
from source_common import *
PAT=re.compile(r'\[SYMBOL ([0-9A-Fa-f]+)\]')
def fontinfo(font):
 if font is None:return {'base_font':None,'to_unicode_sha256':None,'explicit_unicode_values':[]}
 tu=font.get('/ToUnicode');data=tu.get_object().get_data() if tu else b'';values=[]
 for block in re.findall(br'beginbfchar(.*?)endbfchar',data,re.S):
  for _,dest in re.findall(br'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>',block):
   try:values.extend(ord(c) for c in bytes.fromhex(dest.decode()).decode('utf-16-be'))
   except (ValueError,UnicodeDecodeError):pass
 return {'base_font':str(font.get('/BaseFont')),'to_unicode_sha256':sha(data) if data else None,'explicit_unicode_values':sorted(set(values))}
def normalized_runs(runs):
 chars=[];origin=[]
 for ri,run in enumerate(runs):
  for ch in run['text']:
   if ch.isspace():
    if chars and chars[-1]!=' ':chars.append(' ');origin.append(ri)
   else:chars.append(ch);origin.append(ri)
 if chars and chars[-1]==' ':chars.pop();origin.pop()
 return ''.join(chars),origin

def run(pdf_source,pairs,html_records,out):
 src=Path(pdf_source).resolve();out=Path(out).resolve()
 if out.exists():raise ValueError('Fresh recovery report required')
 state=load(src/'checkpoint.json');proof=load(pairs);owner_bytes=Path(html_records).read_bytes();owners=[json.loads(line) for line in owner_bytes.splitlines()]
 if state['errors'] or not state.get('opening_closing_inventory_equal'):raise ValueError('Source PDF acquisition/closing unqualified')
 report=[];font_metadata={};rawart={a['document_id']:a for a in state['artifacts'] if a['role']=='native-symbol-pdf'}
 for doc,a in rawart.items():
  raw=(src/a['path']).read_bytes()
  if sha(raw)!=a['sha256']:raise ValueError('Corrupt source PDF')
  reader=PdfReader(io.BytesIO(raw),strict=True);pages=[];runs_by_page=[];current_section=None
  for pi,page in enumerate(reader.pages):
   runs=[]
   def visitor(text,cm,tm,font,size):runs.append({'text':text,**fontinfo(font)})
   plain=page.extract_text(visitor_text=visitor,extraction_mode='plain') or '';text,origin=normalized_runs(runs)
   markers=[]
   for match in re.finditer(r'(?:^|\n)\s*(\d{1,2}[A-Z]?\.\d+[A-Z]?\.\d+)\s+[A-Z]',plain):markers.append({'offset':len(clean(plain[:match.start(1)])),'number':match.group(1)})
   pages.append({'page':pi+1,'text':text,'origin':origin,'plain_and_visitor_text_equal':text==clean(plain),'initial_section':current_section,'section_markers':markers})
   if markers:current_section=markers[-1]['number'];runs_by_page.append(runs)
   fonts=page['/Resources'].get('/Font')
   if fonts:
    for name,obj in fonts.get_object().items():
     font=obj.get_object()
     if 'Symbol' not in str(font.get('/BaseFont')):continue
     meta=fontinfo(font);fid=meta['to_unicode_sha256']
     if fid in font_metadata:continue
     meta.update(source_pdf_sha256=a['sha256'],source_document_id=doc,embedded_font_programs=[],source_actualtext_markers=0)
     desc=font.get('/DescendantFonts');target=desc[0].get_object() if desc else font;fd=target.get('/FontDescriptor');fd=fd.get_object() if fd else {}
     for key in ['/FontFile','/FontFile2','/FontFile3']:
      if key not in fd:continue
      stream=fd[key];data=stream.get_data();tables=[];post_version=None;custom_names=[]
      if key=='/FontFile2' and len(data)>=12:
       count=struct.unpack('>H',data[4:6])[0]
       for ti in range(count):
        tag,_,off,length=struct.unpack('>4sIII',data[12+16*ti:28+16*ti]);tag=tag.decode('latin1');tables.append(tag)
        if tag=='post':
         post=data[off:off+length];post_version=post[:4].hex()
         if post_version=='00020000' and len(post)>=34:
          ng=struct.unpack('>H',post[32:34])[0];pos=34+2*ng
          while pos<len(post):n=post[pos];custom_names.append(post[pos+1:pos+1+n].decode('latin1'));pos+=n+1
      meta['embedded_font_programs'].append({'font_key':key,'sha256':sha(data),'bytes':len(data),'table_tags':tables,'post_table_version':post_version,'post_custom_glyph_names':custom_names,'pixel_operations':False})
     font_metadata[fid]=meta
   contents=page.get_contents();data=contents.get_data() if contents else b''
   for m in font_metadata.values():
    if m['source_document_id']==doc:m['source_actualtext_markers']+=len(re.findall(br'/ActualText\b',data))
  for row in proof['rows']:
   if row['source_document_id']!=doc:continue
   parts=PAT.split(row['word_literal']);recoveries=[];scoped=[r for r in owners if r['source_document_id']==doc and r['source_sha256']==row['html_source_sha256']]
   first=row['html_literal_pairs'][0]
   if 'html_block_index' in first:own=[r for r in scoped if first['html_block_index'] in r['block_indices']]
   else:
    table_index=first['pairs'][0]['table_index'];table_owners=[r for r in scoped for _ in r['tables']];own=[table_owners[table_index]] if table_index<len(table_owners) else []
   if len(own)!=1:raise ValueError('Source HTML owner missing/nonunique')
   owner=own[0]['number'] or None
   for si,code in enumerate(parts[1::2]):
    left=parts[2*si];right=parts[2*si+2];attempt=[]
    for window,right_window in [(80,80),(60,60),(40,40),(24,24),(80,12),(40,12),(24,12)]:
     l=clean(left[-window:]);r=clean(right[:right_window])
     if len(l)+len(r)<35:continue
     pattern=re.compile(re.escape(l)+r'\s*(.)\s*'+re.escape(r),re.S)
     candidates=[]
     for page,runs in zip(pages,runs_by_page):
      if not page['plain_and_visitor_text_equal']:continue
      for match in pattern.finditer(page['text']):
       pos=match.start(1);section=page['initial_section']
       for marker in page['section_markers']:
        if marker['offset']<=pos:section=marker['number']
       if owner and section!=owner:continue
       char=match.group(1);f=runs[page['origin'][pos]];semantic=bool(f['to_unicode_sha256'] and ord(char) in f['explicit_unicode_values'] and unicodedata.category(char) not in ['Co','Cc','Cs','Cn'])
       candidates.append({'page':page['page'],'pdf_character':char,'unicode':'U+'+format(ord(char),'04X'),'unicode_name':unicodedata.name(char,None),'context':match.group(0),'context_sha256':sha(match.group(0).encode()),'font':{k:v for k,v in f.items() if k!='text'},'qualified':semantic,'window':window,'right_window':right_window,'native_pdf_section':section,'source_html_owner_section':owner})
     if len(candidates)==1:attempt=candidates;break
    recovered={'symbol_ordinal':si,'original_word_code':code,'candidates':attempt,'qualified':len(attempt)==1 and attempt[0]['qualified']}
    recoveries.append(recovered)
   report.append({'record_id':row['record_id'],'source_document_id':doc,'source_native_sha256':row['native_source_sha256'],'source_html_sha256':row['html_source_sha256'],'source_xml_sha256':row['source_xml_sha256'],'source_html_owner_record_id':own[0]['record_id'],'source_html_owner_section':owner,'word_source_ordinal':row['word_source_ordinal'],'source_pdf_sha256':a['sha256'],'source_pdf_url':a['source_url'],'original_word_literal':row['word_literal'],'html_literal_pairs':row['pairs'],'symbol_recoveries':recoveries})
 result={'schema':'king-source-bound-symbol-recovery-1','complete':False,'scope':'Only exact original XML/unit/hash plus unique same-source-PDF context and explicit ToUnicode destination. No font-name-only inference, no PUA guessing, no image/render APIs.','records':report,'font_metadata':font_metadata,'source_pdf_checkpoint_sha256':sha((src/'checkpoint.json').read_bytes()),'pair_proof_sha256':sha(Path(pairs).read_bytes()),'html_owner_records_sha256':sha(owner_bytes),'qualified_symbols':sum(x['qualified'] for r in report for x in r['symbol_recoveries']),'unqualified_symbols':sum(not x['qualified'] for r in report for x in r['symbol_recoveries']),'images_extracted':False,'code_fingerprint':{n:sha((Path(__file__).parent/n).read_bytes()) for n in ['king_symbol_recovery_v2.py','source_common.py']}};save(out,result);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--pdf-source',required=True);p.add_argument('--pairs',required=True);p.add_argument('--html-records',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=run(a.pdf_source,a.pairs,a.html_records,a.out);print(json.dumps({k:v for k,v in r.items() if k not in ['records','font_metadata']},indent=2));sys.exit(2)
