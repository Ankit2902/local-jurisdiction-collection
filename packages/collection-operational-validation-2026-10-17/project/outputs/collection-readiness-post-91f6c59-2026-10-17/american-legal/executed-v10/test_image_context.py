"""Declared image anchor context; real html_record, no network/image decoding."""
import json,socket
from unittest.mock import patch
from model import html_record

def record(html):
 return html_record({'doc_id':'A','id':1,'html':'<h2 id="rid-A">Section A</h2><p>Operative source rule.</p>'+html},{'document_id':'A','internal_id':1,'heading':'Section A','path':['Section A'],'parent_id':None,'has_children':False},{},'https://example.invalid/book','fixture')

def tests():
 results=[]
 with patch.object(socket.socket,'connect',side_effect=AssertionError('No network')),patch('PIL.Image.open',side_effect=AssertionError('No image decoder')):
  value='data:application/octet-stream;base64,QUJD\nUEFZTE9BRF9NVVNUX05PVF9TVVJWSVZF'
  r=record('<a id="source-image" type="IMAGE/PNG" href="'+value+'">Available <b id="caption-label">caption</b>.</a>');serial=json.dumps(r)
  assert 'UEFZTE9BRF9NVVNUX05PVF9TVVJWSVZF' not in serial and 'data:application/octet-stream' not in serial.lower()
  assert '[IMAGE]' in r['text'] and 'Available caption.' in r['text'] and 'source-image' in r['html'] and 'caption-label' in r['html']
  assert all(a['disposition']=='image-placeholder' and a['raw']=='[IMAGE]' and a['source_attribute']=='[IMAGE]' for a in r['assets']);assert not r['links']
  results.append({'name':'declared_image_anchor_opaque_multiline_URI_payload_absent_label_ID_retained_no_transport_decode','passed':True})
  r=record('<a id="ordinary" type="application/pdf" href="https://example.invalid/standard.pdf">Available standard.</a>');assert '[IMAGE]' not in r['text'] and 'Available standard.' in r['text'] and 'https://example.invalid/standard.pdf' in r['html'];assert r['assets'][0]['disposition']=='required-asset'
  results.append({'name':'ordinary_nonimage_document_anchor_unchanged_and_required','passed':True})
 return {'passed':True,'count':len(results),'tests':results,'network_requests':0,'image_decode_calls':0}

if __name__=='__main__':print(json.dumps(tests(),indent=2))
