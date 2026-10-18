"""Actual _record no-image metadata/caption controls, statutory AND ordinary anchors."""
import base64,hashlib,importlib,json,pathlib,socket,subprocess,sys,types
from unittest.mock import patch
from PIL import Image
P=pathlib.Path(__file__).resolve().parents[4];B=P/'outputs/collection-readiness-posta35cef8-2026-10-18/ecode';O=pathlib.Path(__file__).resolve().parent;pkg=types.ModuleType('_stat_v5_peer');pkg.__path__=[str(B/'candidate-v5')];sys.modules[pkg.__name__]=pkg;calls=[]
def no(*a,**k):calls.append('forbidden');raise AssertionError('No network/decoder')
with patch.object(socket,'create_connection',no),patch.object(socket.socket,'connect',no),patch.object(subprocess,'Popen',no),patch.object(base64,'b64decode',no),patch.object(Image,'open',no):
 a=importlib.import_module('_stat_v5_peer.adapters');e=importlib.import_module('_stat_v5_peer.engine')
 raw='<div id="1_content" class="section_content content"><p>Alcoholic Beverage Control Law § <a class="statref" href="https://municipal.codes/NY/ABC/140">140<svg><text>DATA:IMAGE/PNG;base64,QUJD\nCONTINUATION_SENTINEL</text></svg></a> and <a href="https://example.invalid/legal">Ordinary caption<svg><text>DATA:IMAGE/PNG;base64,QUJD\nCONTINUATION_SENTINEL</text></svg></a>.</p></div>'
 r=a._record('1','Section 1','section',a.BeautifulSoup(raw,'html.parser').div,'https://ecode360.com/1',None,{'1'});serialized=json.dumps(r);assert 'data:image/' not in serialized.lower() and 'CONTINUATION_SENTINEL' not in serialized
 assert r['image_placeholder_count']==2 and r['content_html'].count('[IMAGE]')==2
 assert len(r['links'])==2 and r['links'][0]['label']=='140 [IMAGE]' and r['links'][1]['label']=='Ordinary caption [IMAGE]'
 ev=r['links'][0]['source_statutory_evidence'];assert ev['source_label']=='140 [IMAGE]' and 'Alcoholic Beverage Control Law' in ev['source_context_text']
 assert not e.statutory_reference(r['links'][0]['url'],'https://ecode360.com/AL0934','ecode360',r['links'][0])
 control='<div id="1_content" class="section_content content"><p>Alcoholic Beverage Control Law § <a class="statref" href="https://municipal.codes/NY/ABC/140">140</a>.</p></div>'
 clean=a._record('1','Section 1','section',a.BeautifulSoup(control,'html.parser').div,'https://ecode360.com/1',None,{'1'});assert clean['links'][0]['label']=='140' and e.statutory_reference(clean['links'][0]['url'],'https://ecode360.com/AL0934','ecode360',clean['links'][0])
 polluted='<div id="1_content" class="section_content content"><p>Alcoholic Beverage Control Law § <a class="statref DATA:IMAGE/PNG;base64,QUJD\nCONTINUATION_SENTINEL" href="https://municipal.codes/NY/ABC/140">140</a>.</p></div>'
 redacted=a._record('1','Section 1','section',a.BeautifulSoup(polluted,'html.parser').div,'https://ecode360.com/1',None,{'1'});safe=json.dumps(redacted);assert 'data:image/' not in safe.lower() and 'CONTINUATION_SENTINEL' not in safe and not redacted['links'][0].get('source_statutory_evidence')
 assert not e.statutory_reference(redacted['links'][0]['url'],'https://ecode360.com/AL0934','ecode360',redacted['links'][0])
 report={'passed':True,'source_classes_payload_absent_all_record_fields_and_redacted_statref_refused':True,'actual_record_graphic_anchor_payload_absent_in_all_fields':True,'statutory_and_ordinary_available_labels_and_IMAGE_preserved':True,'source_label_safe':True,'graphic_label_not_falsely_qualified_as_numeric_statutory_reference':True,'ordinary_legal_reference_control_qualifies':True,'forbidden_calls':calls,'adapter_sha256':hashlib.sha256((B/'candidate-v5/adapters.py').read_bytes()).hexdigest(),'engine_sha256':hashlib.sha256((B/'candidate-v5/engine.py').read_bytes()).hexdigest(),'executed_source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'publisher_native_image_decode_operations':0}
 (O/'record-label-review-v5.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
