#!/usr/bin/env python3
"""Read-only selected-run audit for separately retained image bytes, including opaque .bin."""
import argparse,hashlib,json,re,sys
sys.dont_write_bytecode=True
from pathlib import Path
def signature(data):
 if data.startswith(b'\x89PNG\r\n\x1a\n'):return 'png'
 if data.startswith(b'\xff\xd8\xff'):return 'jpeg'
 if data[:6] in [b'GIF87a',b'GIF89a']:return 'gif'
 if data.startswith((b'II*\x00',b'MM\x00*')):return 'tiff'
 if data.startswith(b'RIFF') and data[8:12]==b'WEBP':return 'webp'
 if data.startswith(b'BM'):return 'bmp'
 if data.startswith(b'\x00\x00\x01\x00'):return 'ico'
 if data[4:8]==b'ftyp' and data[8:12] in [b'avif',b'avis',b'heic',b'heix',b'hevc',b'hevx',b'mif1',b'msf1']:return 'avif_or_heif'
 if re.match(br'\s*(?:<\?xml[^>]+>\s*)?<svg\b',data,re.I):return 'svg'
 return None
def audit(root):
 root=Path(root).resolve();hits=[];inspected=0;receipt_images=[]
 for p in sorted(root.rglob('*')):
  if not p.is_file() or '.venv' in p.parts or '__pycache__' in p.parts:continue
  inspected+=1
  with p.open('rb') as f:head=f.read(2048)
  kind=signature(head)
  if kind:hits.append({'path':str(p.relative_to(root)),'signature':kind,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  # Acquisition receipts may be UUID.json, not named *receipt*. Inspect every
  # retained JSON document before deciding whether it is response metadata.
  if p.suffix!='.json':continue
  try:r=json.loads(p.read_text())
  except (ValueError,UnicodeError):continue
  def walk(value,locator=''):
   if isinstance(value,list):
    for n,x in enumerate(value):walk(x,locator+'/'+str(n))
   if not isinstance(value,dict):return
   h=value.get('headers') or value.get('response',{}).get('headers') or {};mime=next((str(v) for k,v in h.items() if k.lower()=='content-type'),'')
   if mime.lower().startswith('image/'):
    refs=[value.get(k) for k in ['body_file','raw_ref','file','path'] if isinstance(value.get(k),str)];actual=[]
    for ref in refs:
     candidate=(root/ref).resolve()
     if candidate.is_relative_to(root) and candidate.is_file():actual.append({'path':str(candidate.relative_to(root)),'bytes':candidate.stat().st_size})
    if 'receipt' in p.name:
     for candidate in [p.with_name(p.name.replace('.receipt.json','.bin')),p.with_name(p.name.removesuffix('.receipt.json'))]:
      if candidate.is_file() and candidate!=p and all(x['path']!=str(candidate.relative_to(root)) for x in actual):actual.append({'path':str(candidate.relative_to(root)),'bytes':candidate.stat().st_size})
    receipt_images.append({'receipt':str(p.relative_to(root))+locator,'content_type':mime,'request_method':value.get('request',{}).get('method',value.get('method')),'body_artifacts':actual})
   for k,v in value.items():
    if k not in ['headers','response']:walk(v,locator+'/'+str(k))
  walk(r)
 nonempty=[r for r in receipt_images if any(x['bytes']>0 for x in r['body_artifacts'])]
 return {'run_name':root.name,'inspected_files':inspected,'separate_image_binary_count':len(hits),'image_mime_receipts':receipt_images,'nonempty_image_mime_receipts':nonempty,'image_binaries':hits,'passed':not hits and not nonempty,'scope_note':'Selected current-policy run only. Binary signatures and image MIME receipts checked, including opaque files. Embedded graphics in native PDF/HTML/archives are original source bytes and are not separately extracted.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('runs',type=Path,nargs='+');a=p.parse_args();results=[audit(r) for r in a.runs];report={'schema_version':1,'read_only':True,'network_requests_sent':0,'passed':all(r['passed'] for r in results),'results':results};print(json.dumps(report,indent=2));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
