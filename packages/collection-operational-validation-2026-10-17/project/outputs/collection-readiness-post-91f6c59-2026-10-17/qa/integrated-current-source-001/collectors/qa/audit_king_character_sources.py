"""Independent finite King County Word/HTML glyph evidence against original PDF fonts."""
import argparse,collections,hashlib,io,json,re,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
from pypdf import PdfReader
from pypdf.generic import EncodedStreamObject
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def sha(b):return hashlib.sha256(b).hexdigest()
def compact(t):return ''.join(t.split())
def clean(t):return ' '.join(t.split())
def literal(n):
 tag=n.tag.removeprefix(W)
 if tag in ['drawing','pict','object']:return '[IMAGE]'
 if tag in ['t','delText']:return n.text or ''
 if tag in ['tab','br','cr']:return ' '
 if tag=='noBreakHyphen':return '\u2011'
 if tag=='softHyphen':return '\u00ad'
 if tag=='sym':
  code=n.get(W+'char','');font=n.get(W+'font','').lower()
  return chr(int(code,16)) if font in ['courier new','arial','times new roman','calibri','cambria'] and 32<=int(code,16)<=126 else '[SYMBOL '+code+']'
 return ''.join(literal(c) for c in n)+(' ' if tag in ['p','tc','tr'] else '')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh output required')
 base=a.package;profile_raw=(base/'source_character_dispositions.json').read_bytes();profiles=json.loads(profile_raw);word_source=base/'evidence/king-county-native-word-v2';pdf_source=base/'evidence/king-symbol-source-pdfs';wc=json.loads((word_source/'checkpoint.json').read_text());pc=json.loads((pdf_source/'checkpoint.json').read_text());word={x['sha256']:x for x in wc['artifacts'] if x['role']=='native-word'};pdf={x['sha256']:x for x in pc['artifacts'] if x['role']=='native-symbol-pdf'};results=[];errors=[];font_checks=[];native_members=[];readers={};image_reads=0
 original=EncodedStreamObject.get_data
 def guarded(stream,*args,**kwargs):
  nonlocal image_reads
  if stream.get('/Subtype')=='/Image':image_reads+=1;raise AssertionError('Image stream decode forbidden')
  return original(stream,*args,**kwargs)
 with patch.object(EncodedStreamObject,'get_data',guarded):
  for entry in profiles['word']:
   wi=word[entry['source_native_sha256']];wr=(word_source/wi['path']).read_bytes();assert sha(wr)==entry['source_native_sha256']
   with zipfile.ZipFile(io.BytesIO(wr)) as z:
    xml=z.read('word/document.xml');native_members.append({'source_native_sha256':sha(wr),'member':'word/document.xml','sha256':sha(xml)});body=ET.fromstring(xml).find(W+'body');unit=list(body)[entry['word_source_ordinal']]
    assert sha(ET.tostring(unit))==entry['source_xml_sha256'];assert clean(literal(unit))==entry['original_word_literal']
   pi=pdf[entry['source_pdf_sha256']];pr=(pdf_source/pi['path']).read_bytes();assert sha(pr)==entry['source_pdf_sha256'];assert pi['source_url']==entry['source_pdf_url'] and pi['status']==200
   reader=readers.setdefault(entry['source_pdf_sha256'],PdfReader(io.BytesIO(pr)))
   for event in entry['recoveries']:
    cand=event['candidates'][0];page=reader.pages[cand['page']-1];source_text=page.extract_text();matches=[]
    for ref in page['/Resources']['/Font'].values():
     font=ref.get_object()
     if str(font.get('/BaseFont'))!=cand['font']['base_font'] or '/ToUnicode' not in font:continue
     cmap=font['/ToUnicode'].get_object().get_data()
     if sha(cmap)!=cand['font']['to_unicode_sha256']:continue
     destinations=[]
     for block in re.findall(rb'beginbfchar(.*?)endbfchar',cmap,re.S):
      for code,value in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>',block):
       decoded=bytes.fromhex(value.decode()).decode('utf-16-be');destinations.append(decoded)
     matches.append({'font':str(font['/BaseFont']),'to_unicode_sha256':sha(cmap),'explicit_bfchar_destinations':destinations})
    context=compact(cand['context']);qualified=len(matches)==1 and cand['pdf_character'] in matches[0]['explicit_bfchar_destinations'] and compact(source_text).count(context)==1 and cand['pdf_character'] in cand['context']
    if not qualified:errors.append({'document':entry['source_document_id'],'ordinal':entry['word_source_ordinal'],'symbol':event['original_word_code'],'page':cand['page'],'font_matches':matches,'context_occurrences':compact(source_text).count(context)})
    results.append({'document':entry['source_document_id'],'word_source_ordinal':entry['word_source_ordinal'],'word_source_xml_sha256':entry['source_xml_sha256'],'original_word_code':event['original_word_code'],'source_pdf_sha256':entry['source_pdf_sha256'],'source_pdf_url':entry['source_pdf_url'],'source_page':cand['page'],'recovered_character':cand['pdf_character'],'context_sha256':sha(cand['context'].encode()),'context_occurrences':compact(source_text).count(context),'font_evidence':matches,'passed':qualified})
 report={'passed':not errors,'script_sha256':sha(Path(__file__).read_bytes()),'profiles_sha256':sha(profile_raw),'word_profile_units':len(profiles['word']),'qualified_events':sum(x['passed'] for x in results),'events':results,'errors':errors,'native_structural_members_read':native_members,'pdf_image_stream_decodes':image_reads,'image_or_ole_word_members_read':0,'network_requests_sent':0,'scope':'Each finite Word original XML unit/literal and native file are rehashed, each independently retained same-document PDF page has unique exact context and explicit hashed font ToUnicode bfchar mapping. This qualifies only17 specific percent/degree/double-prime recoveries, not unresolved private symbols or wholepublication dates/dependencies.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'qualified_events':report['qualified_events'],'errors':errors}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
