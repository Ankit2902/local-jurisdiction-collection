"""Independent bounded heading offset/image controls against frozen reader; no source replay."""
import base64,hashlib,importlib,json,pathlib,socket,subprocess,sys
from unittest.mock import patch
from PIL import Image
P=pathlib.Path(__file__).resolve().parents[5];O=pathlib.Path(__file__).resolve().parent;B=P/'outputs/collection-readiness-post9ef7220-2026-10-17/municipal-corpus-reader-v1';sys.path.insert(0,str(B/'source'));calls=[];cases=[]
def no(*a,**k):calls.append('forbidden');raise AssertionError('No network/decoder/process')
with patch.object(socket,'create_connection',no),patch.object(socket.socket,'connect',no),patch.object(subprocess,'Popen',no),patch.object(base64,'b64decode',no),patch.object(Image,'open',no):
 mc=importlib.import_module('municipal_codes_html');base='https://example.municipal.codes/Code';ident=base+'/A'
 def get(header,prefix=''):
  raw=(prefix+'<article id="A" class="type-Section" data-history="/Code/A/history">'+header+'<p>Law.</p></article>').encode();return mc.own_heading(raw,ident,base,ident,{ident:{}})
 for control in ['\u2028','\u0085','\x1e','\r']:
  expected='<header>Before'+control+'After</header>';r=get(expected,'outside'+control+'prefix\n');assert r['source_heading_html']==expected;assert r['source_heading_raw_html_sha256']==hashlib.sha256(expected.encode()).hexdigest();cases.append('exact LF-only slicing with '+repr(control))
 r=get('<header>Before<img src="data:application/octet-stream;base64,NEVER_DECODE">After</header>');assert r['source_heading_html']=='<header>Before[IMAGE]After</header>' and 'NEVER_DECODE' not in str(r);cases.append('opaque image src replaced without payload/decoder')
 r=get('<header><a type=" IMAGE/PNG " href="data:application/octet-stream;base64,NEVER_DECODE">Map caption</a> After</header>');assert 'Map caption[IMAGE] After' in r['source_heading_html'] and 'NEVER_DECODE' not in str(r) and r['source_heading_links'][0]['source_href']=='[IMAGE]';cases.append('typed opaque image anchor caption and marker, redacted link provenance')
 r=get('<header>Caption<picture><source srcset="x.png 1x,y.png 2x"><img src="/z.png"></picture><table><tr><td background="/map.png">Cell caption</td></tr></table></header>');assert r['source_heading_image_placeholders']==2 and '[IMAGE]Cell caption' in r['source_heading_html'] and '<table>' in r['source_heading_html'];cases.append('picture + table image slots preserve captions/table structure')
assert not calls
report={'passed':True,'cases':cases,'test_count':len(cases),'reader_sha256':hashlib.sha256((B/'source/municipal_codes_html.py').read_bytes()).hexdigest(),'forbidden_calls':calls,'actual_source_normalization_native_parse_calls':0,'image_decoding_rendering_extraction_OCR_calls':0,'executed_source_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()}
(O/'heading-guard-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
