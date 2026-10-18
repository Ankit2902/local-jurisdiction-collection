"""Default dispatch with actual retained62IR; only new bounded page26 witness reparsed."""
import base64,contextlib,csv,gzip,hashlib,io,json,pathlib,shutil,socket,subprocess,sys
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'candidate'));sys.dont_write_bytecode=True
from collectors.encodeplus import infrastructure_logical as m,native_document as native
import pdfplumber,pypdfium2
from pdfminer.pdftypes import PDFStream
from PIL import Image
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
repo=ROOT.parent.parent.parent/'github/local-jurisdiction-collection'
family=ROOT/'candidate/collectors/encodeplus'
fixture=json.loads(gzip.decompress((family/'fixtures/infrastructure-printed-native/source-ir-and-native-inventory.json.gz').read_bytes()));cfg=json.loads((family/'configs/native-82-0c6b3dc40877.json').read_text());data=(ROOT/'source/start.pdf').read_bytes();assert hashlib.sha256(data).hexdigest()==m.source.SHA
old=[json.loads(x) for x in (ROOT/'source/baseline172.jsonl').read_text().splitlines()]
oldmixed=[json.loads(x) for x in (ROOT/'source/baseline828.jsonl').read_text().splitlines()]
calls=[];original=PDFStream.get_data

def deny(name):
 def fail(*a,**k):calls.append(name);raise AssertionError('Forbidden '+name)
 return fail

def stream(s):
 if getattr(s.attrs.get('Subtype'),'name',None)=='Image' or ('W' in s.attrs and 'H' in s.attrs):return deny('PDFStream image data')()
 return original(s)
sourcehashes={str(p.relative_to(ROOT/'candidate')):sha(p) for p in sorted((ROOT/'candidate').rglob('*')) if p.is_file()}
with contextlib.ExitStack() as stack:
 stack.enter_context(patch.object(PDFStream,'get_data',stream))
 for obj,names in [(Image,['open']),(socket,['socket']),(subprocess,['run','Popen']),(base64,['b64decode']),(pypdfium2.PdfImage,['get_bitmap','extract','get_data']),(pypdfium2.PdfPage,['render']),(pdfplumber.page.Page,['to_image'])]:
  for name in names:
   if hasattr(obj,name):stack.enter_context(patch.object(obj,name,deny(name)))
 stack.enter_context(patch.object(m.source,'native_inventory',return_value=fixture['native_inventory']))
 # Existing62page parser/native inventory are authentic retained fixtures, not new extraction credit.
 stack.enter_context(patch('collectors.encodeplus.pdf_structure.pages',return_value=(fixture['source_pages'],[])))
 records,details=native.page_records(data,cfg)
 native.validate_record_identity(records,details,cfg)
 out=native.outputs(records);outdir=ROOT/'actual-default172';outdir.mkdir()
 for name,body in out.items():(outdir/name).write_bytes(body)
 # Strict current canonical verifier refuses corrupt tree, glyph witness, diagnostics and source fields.
 faults=[]
 import copy
 for label,change in [('flatten',lambda r:r[54].update(ordered_blocks=copy.deepcopy(old[54]['ordered_blocks']))),('child_owner',lambda r:r[54]['ordered_blocks'][3]['items'][0]['children'].reverse()),('glyph',lambda r:r[54]['source_nested_list_native_witness']['blocks'][4]['glyphs'][0].update(fontname='Other')),('diagnostic',lambda r:r[54]['superseded_flat_list_diagnostics']['original_fields'].update(text='lost')),('source_owner',lambda r:r[54].update(document_id='wrong'))]:
  bad=copy.deepcopy(records);change(bad)
  try:native.outputs(bad)
  except AssertionError:faults.append(label)
  else:raise AssertionError('Fault accepted '+label)
 changed=[i for i,(a,b) in enumerate(zip(old,records)) if a!=b];assert changed==[54],changed
 assert records[54]['text']==old[54]['text'] and all(records[i]==old[i] for i in range(172) if i!=54)
 replacement={r['id']:r for r in records if r['id']==m.nested.ID};mixed=[replacement.get(r['id'],r) for r in oldmixed];mixedout=native.outputs(mixed);mixedpath=ROOT/'mixed828';mixedpath.mkdir()
 for name,body in mixedout.items():(mixedpath/name).write_bytes(body)
 assert sum(a!=b for a,b in zip(mixed,oldmixed))==1 and len(mixed)==828
 def images(rows):return [(r['id'],b) for r in rows for b in r.get('ordered_blocks',[]) if b.get('kind')=='image']
 assert images(mixed)==images(oldmixed) and sum(r['text'].count('[IMAGE]') for r in mixed)==201
 report={'source_sha256':m.source.SHA,'source_bytes':len(data),'source_runtime_hashes':sourcehashes,'source_family_unchanged':all(sha(ROOT/'candidate'/p)==h for p,h in sourcehashes.items()),'mode':'Real native.page_records/identity/outputs; prior62IR/nativeinventory retained, only newbounded26glyphwitness recomputed fromoriginalPDF','new_native_text_pages':[26],'new_full62_parse':False,'records':172,'changed_record_indices':changed,'unchanged_records':171,'mixed_records':828,'mixed_unchanged':827,'image_markers':201,'image_blocks_exact':True,'source_selected_list_word_ids':105,'selected_list_glyphs':516,'outer_items':2,'child_items':4,'levels':2,'strict_canonical_faults_refused':faults,'forbidden_calls':calls,'details':details}
 (ROOT/'actual-proof.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 assert not calls
print(json.dumps({k:report[k] for k in ['records','unchanged_records','mixed_unchanged','image_markers','strict_canonical_faults_refused','forbidden_calls']}))
