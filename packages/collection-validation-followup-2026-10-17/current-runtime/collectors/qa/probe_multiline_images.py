"""Bounded synthetic multiline data-URI leakage probe through six real parsers."""
import argparse,hashlib,json,socket,sys
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sources():
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for family in ['american-legal','ecode','encodeplus','official','municode','gridics'] for p in sorted((ROOT/'collectors'/family).glob('*')) if p.suffix in ('.py','.cjs')}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh probe output required')
 before=sources();sys.path.insert(0,str(HERE));import test_all_family_image_metadata as parsers
 tail='UElYRUxTX0NPTlRJTlVBVElPTl9NVVNUX05PVF9TVVJWSVZF';uri='DATA:IMAGE/PNG;base64,QUJD\n'+tail;body='<p data-image-metadata="'+uri+'">Rule applies.</p><img src="'+uri+'"><object type="IMAGE/PNG" data="'+uri+'"></object>'
 def forbidden(*args,**kwargs):raise AssertionError('MULTILINE_PROBE_NETWORK_FORBIDDEN')
 results=[]
 with patch.object(socket.socket,'connect',forbidden),patch.object(socket,'create_connection',forbidden):
  for family,(r,key) in parsers.AllFamilyImageMetadata().rows(body).items():
   leaking=[]
   def walk(value,path=''):
    if isinstance(value,dict):
     for k,v in value.items():walk(v,path+'/'+k)
    elif isinstance(value,list):
     for i,v in enumerate(value):walk(v,path+'/'+str(i))
    elif isinstance(value,str) and any(t in value for t in [tail,'QUJD']):leaking.append(path)
   walk(r);results.append({'family':family,'passed':not leaking and 'data:image/' not in r[key].lower(),'leaking_fields':leaking,'markers':r['text'].count('[IMAGE]')})
 after=sources();report={'passed':all(r['passed'] for r in results) and before==after,'results':results,'source_before':before,'source_after':after,'source_unchanged':before==after,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'fixture_sha256':hashlib.sha256(body.encode()).hexdigest(),'network_requests_sent':0,'scope':'Synthetic actual HTML parser outputs only. No publisher, image body acquisition, rendering, OCR, or decoding; PDF/notes paths require separate probes.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'source_unchanged':before==after,'results':results}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
