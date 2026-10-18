"""Guard faults on a temporary copy of actual retained IR; never source validation."""
import copy,hashlib,json,shutil,socket,sys,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent/'candidate'))
import package
from common import canonical,encoded,files,load,jsonl

def run(original):
    original=Path(original).resolve();before=files(original);results=[]
    with tempfile.TemporaryDirectory(prefix='actual-package-faults-') as tmp:
        base=Path(tmp);source=base/'input';shutil.copytree(original/'evidence/input',source)
        pp=base/'proof.json';fp=base/'family.json';proof0=load(original/'evidence/proofs/read-only-proof.json');family0=load(original/'evidence/proofs/family-verification.json')
        rp=source/'normalized/records.jsonl';ir0=rp.read_bytes();cp0=(source/'source/checkpoint.json').read_bytes();inv0=(source/'normalized/source-inventory.json').read_bytes()
        cases=[('image_input','<input type="image" src="opaque">'),('mime_less_image_object','<object data="https://example.invalid/diagram.png"></object>'),('image_link','<a href="https://example.invalid/diagram.svg">Diagram</a>'),('CSS_whitespace','<p style="background:url (opaque)">Caption</p>'),('image_preload','<link rel="preload" as="image" href="/opaque">'),('shortcut_icon','<link rel="shortcut icon" href="/opaque">'),('namespace_image','<svg:image href="/opaque"></svg:image>'),('recursive_source_descriptor',None)]
        for name,html in cases:
            rp.write_bytes(ir0);(source/'source/checkpoint.json').write_bytes(cp0);(source/'normalized/source-inventory.json').write_bytes(inv0);family=copy.deepcopy(family0)
            if html:
                rows=[json.loads(l) for l in ir0.decode().split('\n') if l];rows[1]['semantic_html']+=html;rp.write_bytes(jsonl(rows))
            else:
                cp=json.loads(cp0);cp['inventory'][0]['guard_fault']={'nested':{'uri':'DATA:IMAGE/svg+xml,<svg>FORBIDDEN_PAYLOAD</svg>'}};(source/'source/checkpoint.json').write_bytes(encoded(cp));(source/'normalized/source-inventory.json').write_bytes(encoded(cp['inventory']));family['formats']['html']['summary']['source_checkpoint_sha256']=package.file_hash(source/'source/checkpoint.json')
            proof=copy.deepcopy(proof0);proof['evidence_sha256_before']=proof['evidence_sha256_after']=files(source);pp.write_bytes(encoded(proof));fp.write_bytes(encoded(family));out=base/('out-'+name)
            old=socket.socket;socket.socket=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('Network forbidden'))
            try:
                try:package.run(source,pp,fp,out,'originals-flagstaff-html-v1')
                except ValueError as error:reason=str(error)
                else:raise AssertionError('Fault accepted: '+name)
            finally:socket.socket=old
            assert not out.exists();results.append({'fault':name,'refused':True,'error':reason,'export_created':False})
    assert files(original)==before
    return {'passed':True,'scope':'Deliberately rehashed temporary corruptions of actual retained Flagstaff IR/descriptors; forged fixture proof is not a source qualification','actual_records':2661,'checks':results,'original_package_unchanged':True,'network_requests':0,'image_decode_render_extraction_calls':0}
if __name__=='__main__':print(json.dumps(run(sys.argv[1]),indent=2))
