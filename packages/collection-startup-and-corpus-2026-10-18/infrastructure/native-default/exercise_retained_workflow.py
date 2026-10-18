import contextlib,copy,gzip,hashlib,json,pathlib,shutil,socket,subprocess,sys,tempfile,base64
from unittest.mock import patch
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P/'candidate'));sys.dont_write_bytecode=True
from collectors.encodeplus import native_document as native,pdf_structure,infrastructure_printed_projection as projection
import pypdfium2,pdfplumber
from pdfminer.pdftypes import PDFStream
from PIL import Image
S=P.parent/'official/infrastructure-full62-operational-proof-v1';source=S/'run';cfg=json.loads((P/'candidate/collectors/encodeplus/configs/native-82-0c6b3dc40877.json').read_text());fixture=json.loads(gzip.decompress((P/'candidate/collectors/encodeplus/fixtures/infrastructure-printed-native/source-ir-and-native-inventory.json.gz').read_bytes()))
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(p):return {str(f.relative_to(p)):h(f) for f in sorted(p.rglob('*')) if f.is_file()}
before=inventory(P/'candidate');native.runtime_info();calls=[];transfers=[];base=PDFStream.get_data

def forbid(*a,**kw):calls.append('forbidden');raise AssertionError('No native parse/network/image/pixel/decoder call')
def stream(s):
 if getattr(s.attrs.get('Subtype'),'name',None)=='Image' or ('W'in s.attrs and 'H'in s.attrs):return forbid()
 return base(s)
def transport(out,url,rel,timeout=120):
 assert url==cfg['url'] and rel in ['raw/start.pdf','raw/end.pdf'];raw=source/rel;meta=raw.with_name(raw.name+'.receipt.json');target=pathlib.Path(out)/rel;target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():assert target.read_bytes()==raw.read_bytes() and target.with_name(target.name+'.receipt.json').read_bytes()==meta.read_bytes()
 else:shutil.copyfile(raw,target);shutil.copyfile(meta,target.with_name(target.name+'.receipt.json'))
 transfers.append({'relative_path':rel,'source_sha256':h(raw),'original_receipt_sha256':h(meta),'current_request':False})
 return target.read_bytes(),dict(json.loads(meta.read_text()),_retained_path=rel)
O=P/'retained-default-workflow';O.mkdir();results={}
with contextlib.ExitStack() as es:
 es.enter_context(patch.object(socket,'socket',forbid));es.enter_context(patch.object(PDFStream,'get_data',stream))
 for obj,names in [(pypdfium2.PdfPage,['render']),(pypdfium2.PdfImage,['get_bitmap','extract','get_data']),(pdfplumber.page.Page,['to_image']),(Image,['open']),(subprocess,['run','Popen']),(base64,['b64decode'])]:
  for n in names:es.enter_context(patch.object(obj,n,forbid))
 es.enter_context(patch.object(pdf_structure,'pages',side_effect=lambda *a,**k:(copy.deepcopy(fixture['source_pages']),[])))
 es.enter_context(patch.object(projection,'native_inventory',side_effect=lambda *a,**k:copy.deepcopy(fixture['native_inventory'])))
 es.enter_context(patch.object(native,'cached',transport))
 fresh=O/'fresh';results['fresh']=native.collect(cfg,fresh);assert results['fresh']['native_document_complete']
 for k in ['publication_text_complete','source_logical_structure_qualified','attachments_complete','edition_complete','jurisdiction_complete']:assert results['fresh'][k] is False
 assert results['fresh']['normalized_record_count']==172 and results['fresh']['physical_pages']==62
 snap=inventory(fresh);results['verify']=native.verify(fresh);assert results['verify']['native_document_complete'] and inventory(fresh)==snap
 results['finished_resume']=native.collect(cfg,fresh,resume=True);assert results['finished_resume']['native_document_complete'] and inventory(fresh)==snap
 interrupted=O/'interrupted';results['interrupted']=native.collect(cfg,interrupted,interrupt_after_start=True);assert not results['interrupted']['native_document_complete']
 results['resumed']=native.collect(cfg,interrupted,resume=True);assert results['resumed']['native_document_complete']
 for name in native.outputs([json.loads(x) for x in (fresh/'records.jsonl').read_text().splitlines()]):assert (fresh/name).read_bytes()==(interrupted/name).read_bytes()
 badcsv=O/'fault-csv';shutil.copytree(fresh,badcsv);(badcsv/'records.csv').write_text('corrupt CSV');results['fault_csv']=native.verify(badcsv);assert not results['fault_csv']['native_document_complete']
 baddiag=O/'fault-diagnostics';shutil.copytree(fresh,baddiag);(baddiag/'infrastructure-source-page-diagnostics.jsonl').write_text('missing diagnostics');results['fault_diagnostics']=native.verify(baddiag);assert not results['fault_diagnostics']['native_document_complete']
 badraw=O/'fault-native';shutil.copytree(fresh,badraw);r=badraw/'raw/start.pdf';r.write_bytes(b'%PDF-truncated');s=json.loads((badraw/'checkpoint.json').read_text());s['start']['sha256']=h(r);m=json.loads(r.with_name(r.name+'.receipt.json').read_text());m['sha256']=h(r);r.with_name(r.name+'.receipt.json').write_text(json.dumps(m));(badraw/'checkpoint.json').write_text(json.dumps(s));results['fault_native']=native.verify(badraw);assert not results['fault_native']['native_document_complete']
assert inventory(P/'candidate')==before and calls==[]
report={'passed':True,'mode':'Standard native collect/resume/verify and source-specific dispatch with actual native bytes/authentic retained transport and captured source pages/native inventory; no generic/font/vector reparse','substituted_only':['native.cached (retained real bytes/receipt copy)','pdf_structure.pages (actual62 source IR fixture)','infrastructure_printed_projection.native_inventory (actual pinned171-font/vector inventory fixture)'],'source_sha256':cfg['expected_sha256'],'forbidden_calls':calls,'current_network_requests':0,'candidate_sources_before_after_unchanged':True,'runtime_source_hashes':before,'transfers':transfers,'results':results}
(P/'retained-default-workflow.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'fresh_resume_verify':True,'faults':3,'records':172,'physical_pages':62,'calls':calls}))
