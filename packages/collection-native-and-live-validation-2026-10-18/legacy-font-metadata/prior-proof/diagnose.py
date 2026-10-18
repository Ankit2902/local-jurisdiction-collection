"""Original-file-only finite font diagnostics; no normalization or source mutation."""
import collections,copy,hashlib,json,socket,sys,datetime
from pathlib import Path
from unittest.mock import patch,PropertyMock
import pypdfium2 as pdfium
from pypdf import PdfReader
from pypdf._page import PageObject
from font_proof import derive,validate,decoder_from_original,SOURCE_SHA256
source=Path(sys.argv[1]);out=Path(sys.argv[2]);data=source.read_bytes();before=hashlib.sha256(data).hexdigest();calls=[]
def forbidden(*a,**k):calls.append('forbidden image/network API');raise AssertionError(calls[-1])
def original_bytes(value):
 if isinstance(value,bytes):return bytes(value)
 if isinstance(value,str):return value.original_bytes
 return None
with patch('socket.socket',side_effect=forbidden),patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=forbidden),patch.object(pdfium.PdfPage,'render',side_effect=forbidden),patch.object(pdfium.PdfPage,'get_objects',side_effect=forbidden),patch.object(pdfium.PdfImage,'get_bitmap',side_effect=forbidden),patch.object(pdfium.PdfImage,'extract',side_effect=forbidden):
 proof=derive(data);decoder=decoder_from_original(data,proof);reader=PdfReader(source,strict=True);usage={p['target_font_object']:{'pages':set(),'cids':collections.Counter(),'qualified_occurrences':0,'unqualified_occurrences':0,'source_text_runs':0} for p in proof['pairs']};page_reports=[];actual_text=[];form_invocations=[]
 for number,page in enumerate(reader.pages,1):
  resources=page.get('/Resources',{});font_refs=resources.get('/Font',{});current=None;stack=[];examples=[]
  for operands,op in page.get_contents().operations:
   if op==b'q':stack.append(current)
   elif op==b'Q':current=stack.pop() if stack else None
   elif op==b'Tf':current=font_refs.get(str(operands[0])).idnum
   elif op==b'BDC':
    for operand in operands:
     if isinstance(operand,dict) and '/ActualText' in operand:actual_text.append({'page':number,'sha256':hashlib.sha256(str(operand['/ActualText']).encode()).hexdigest()})
   elif op==b'Do':
    reference=resources.get('/XObject',{}).get(operands[0]);obj=reference.get_object() if reference else {}
    if obj.get('/Subtype')=='/Form':form_invocations.append({'page':number,'resource':str(operands[0]),'object':reference.idnum})
    # Never access image stream data. Forms are flagged, not silently traversed.
   elif op in [b'Tj',b'TJ',b"'",b'"'] and current in usage:
    strings=operands[0] if op==b'TJ' else [operands[-1]]
    for string in strings:
     raw=original_bytes(string)
     if raw is None:continue
     units=decoder(raw,current);u=usage[current];u['pages'].add(number);u['source_text_runs']+=1
     for unit in units:u['cids'][unit['cid']]+=1;u['qualified_occurrences']+=unit['qualified'];u['unqualified_occurrences']+=not unit['qualified']
     if len(examples)<2:examples.append({'font_object':current,'raw_text_operand_sha256':hashlib.sha256(raw).hexdigest(),'source_cids':[x['cid'] for x in units],'diagnostic_units':units,'diagnostic_only_not_operative_text':True})
  if examples:page_reports.append({'physical_page':number,'source_font_examples':examples})
 tests=[]
 def refused(name,fn):
  try:fn()
  except (ValueError,AssertionError):tests.append({'name':name,'passed':True});return
  tests.append({'name':name,'passed':False})
 validate(data,proof);tests.append({'name':'actual original proof fully regenerates','passed':True})
 cloned=copy.deepcopy(proof);cloned['pairs'][0]['accepted'][0]['unicode']='X';refused('decoder factory rejects mutated proof',lambda:decoder_from_original(data,cloned))
 cloned=copy.deepcopy(proof);safe_decoder=decoder_from_original(data,cloned);cloned['pairs'][0]['accepted'][0]['unicode']='X';tests.append({'name':'postvalidation caller proof mutation cannot affect decoder','passed':safe_decoder(bytes.fromhex('0003'),620)[0]['unicode']==' '})
 refused('source edition/bytes change refused',lambda:validate(data+b'\n',proof))
 altered=copy.deepcopy(proof);altered['pairs'][0]['accepted'][0]['unicode']='X';refused('tampered Unicode mapping refused',lambda:validate(data,altered))
 altered=copy.deepcopy(proof);altered['pairs'][0]['target_font_object']=623;refused('different font object refused',lambda:validate(data,altered))
 altered=copy.deepcopy(proof);altered['pairs'][0]['accepted'][0]['target_glyf_sha256']='0'*64;refused('unmatched source glyph proof refused',lambda:validate(data,altered))
 refused('odd Identity-H byte sequence refused',lambda:decoder(b'\x00',620))
 unresolved=decoder(bytes.fromhex('00381087'),620);tests.append({'name':'known U recovers; unproven ff ligature stays unresolved','passed':unresolved[0]['unicode']=='U' and not unresolved[1]['qualified'] and unresolved[1]['unicode'] is None})
 refused('unprofiled font refused',lambda:decoder(bytes.fromhex('0038'),906))
for pair in proof['pairs']:
 u=usage[pair['target_font_object']];mapping={x['cid']:x['unicode'] for x in pair['accepted']};u['pages']=sorted(u['pages']);u['cids']={str(cid):{'occurrences':count,'qualified':cid in mapping,'unicode':mapping.get(cid)} for cid,count in sorted(u['cids'].items())};u['unresolved_distinct_used_CIDs']=sum(not x['qualified'] for x in u['cids'].values());u['fully_recoverable_from_finite_witness']=not u['unqualified_occurrences']
after=hashlib.sha256(source.read_bytes()).hexdigest();assert before==after==SOURCE_SHA256;assert not calls
(out/'font-proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');(out/'diagnostic-examples.json').write_text(json.dumps(page_reports,ensure_ascii=False,indent=2)+'\n')
report={'schema_version':1,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(source),'source_sha256':before,'source_pages':len(reader.pages),'scope':'Exact legacy40thEdition2024 original PDF only. Current42nd source, installed fonts and lexical/alphabet-shift inference never used.','font_pairs':[{k:p[k] for k in ['target_font_object','witness_font_object','font_face','source_font_program_sha256','witness_font_program_sha256']}|{'finite_qualified_CIDs':len(p['accepted']),'rejected_cmap_witnesses':p['rejected']} for p in proof['pairs']],'finite_mapping_total':sum(len(p['accepted']) for p in proof['pairs']),'usage':usage,'actual_text_witnesses':actual_text,'untraversed_Form_invocations':form_invocations,'tests':tests,'passed_within_finite_diagnostic_scope':all(t['passed'] for t in tests),'source_unchanged':before==after,'forbidden_API_calls':calls,'network_requests':0,'no_image_pixel_render_decode_extract_OCR':True,'full102page_Unicode_recovery':False,'publication_complete':False,'candidate_promoted':False,'limits':['TargetCIDfonts lackToUnicode/cmap/post. Only finite exactsamefontbinaryglyph witnesses from separate embedded originalPDF instances are mapped.','UnprovenCIDpositions remain explicit unresolved units; no string is promoted as operative legal text.','Exact raw glyf-byte equality is binary font-table identity, not glyph image interpretation or OCR.','Diagnostic usage traverses page text operators only; any Form invocations are reported explicitly.','All795table geometry/cell disagreements and40th-vs42ndsource conflict remain open.']}
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'finite_mapping_total':report['finite_mapping_total'],'usage':usage,'tests':tests,'Form_invocations':len(form_invocations)},ensure_ascii=False))
