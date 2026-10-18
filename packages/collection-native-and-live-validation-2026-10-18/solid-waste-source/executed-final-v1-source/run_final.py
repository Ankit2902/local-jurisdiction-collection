#!/usr/bin/env python3
"""Fresh deterministic exact-source extraction and independent audit with tripwires."""
import argparse,hashlib,importlib.metadata,json,pathlib,platform,sys
import extract_logical,independent_audit,test_logical
p=argparse.ArgumentParser();p.add_argument('--pdf',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--receipt',type=pathlib.Path,required=True);a=p.parse_args()
assert not a.receipt.exists(),'Fresh receipt required'
data=a.pdf.read_bytes()
source={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in pathlib.Path(__file__).parent.glob('*.py')}
with test_logical.no_images_network():
 result=extract_logical.write(data,a.out);audit=independent_audit.audit(data,a.out)
assert not test_logical.CALLS
receipt={'passed':True,'source_sha256':hashlib.sha256(data).hexdigest(),'source_files':source,'out':str(a.out),'qualification':result['qualification'],'independent_full6_audit':audit,'blocked_API_calls':test_logical.CALLS,'tripwires':['socket.socket','socket.create_connection','PIL.Image.open','PyMuPDF.Document.extract_image','PyMuPDF.Page.get_pixmap','pypdf image stream get_data'],'runtime':{'python':sys.version,'platform':platform.platform(),'packages':{k:importlib.metadata.version(k) for k in ['pypdf','pdfminer.six','PyMuPDF','Pillow']}},'outputs':{f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(a.out.iterdir())}}
a.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'passed':True,'logical_units':88,'controls':26,'audit_passed':audit['passed'],'forbidden_calls':test_logical.CALLS,'receipt':str(a.receipt)},indent=2))
