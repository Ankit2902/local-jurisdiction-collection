"""Bounded new metadata image-policy probe; no body acquisition or image operations."""
import sys,pathlib,types,importlib,json,hashlib,socket,subprocess,base64
from unittest.mock import patch
from PIL import Image
P=pathlib.Path(__file__).resolve().parents[4];B=P/'outputs/collection-readiness-posta35cef8-2026-10-18/ecode';O=pathlib.Path(__file__).resolve().parent;pkg=types.ModuleType('_stat_peer');pkg.__path__=[str(B/'candidate-v2')];sys.modules[pkg.__name__]=pkg;calls=[]
def no(*a,**k):calls.append('forbidden');raise AssertionError('Image/network forbidden')
with patch.object(socket,'create_connection',no),patch.object(socket.socket,'connect',no),patch.object(subprocess,'Popen',no),patch.object(base64,'b64decode',no),patch.object(Image,'open',no):
 a=importlib.import_module('_stat_peer.adapters')
 fixture='<p><svg><text>DATA:IMAGE/PNG;base64,QUJD\nCONTINUATION_SENTINEL</text></svg>Alcoholic Beverage Control Law § <a class="statref" href="https://municipal.codes/NY/ABC/140">140</a></p>'
 links=a.link_refs(fixture,'https://ecode360.com/7680474','7680474');text=links[0]['source_statutory_evidence']['source_context_text'];normal=str(a.normalized_images(fixture))
 report={'candidate_adapter_sha256':hashlib.sha256((B/'candidate-v2/adapters.py').read_bytes()).hexdigest(),'new_source_context_metadata_retains_image_payload':('data:image/' in text.lower() and 'CONTINUATION_SENTINEL'in text),'normalized_body_omits_same_image_payload':('CONTINUATION_SENTINEL' not in normal and '[IMAGE]'in normal),'original_source_label_140_preserved':links[0]['label']=='140','forbidden_calls':calls,'fixture_sha256':hashlib.sha256(fixture.encode()).hexdigest(),'image_decode_network_operations':0,'scope':'One synthetic known-image SVG context beside typed statutory anchor; no actual Albany exposure inferred'}
 (O/'image-context-finding.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
