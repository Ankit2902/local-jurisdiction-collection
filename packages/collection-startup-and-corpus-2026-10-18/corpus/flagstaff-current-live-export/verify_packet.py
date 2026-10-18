"""Read-only selected-packet and current corpus audit; no outside origin reads."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,socket
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    root=Path(__file__).resolve().parent;m=json.loads((root/'PACKET-MANIFEST.json').read_text());ready=json.loads((root/'PACKET-READY.json').read_text());assert sha(root/'PACKET-MANIFEST.json')==ready['manifest_sha256']
    observed=set()
    for p in root.rglob('*'):
        assert not p.is_symlink(),'Symlinks forbidden'
        if p.is_file():observed.add(p.relative_to(root).as_posix())
    assert observed==set(m['files'])|{'PACKET-MANIFEST.json','PACKET-READY.json'}
    for name,expected in m['files'].items():p=root/name;assert p.stat().st_size==expected['bytes'] and sha(p)==expected['sha256'],name
    calls=[]
    def forbidden(*a,**kw):calls.append('socket');raise AssertionError('Network forbidden')
    socket.socket=forbidden
    package_root=root/'package';sys.path.insert(0,str(package_root/'packager-source'))
    import package
    assert Path(package.__file__).resolve()==(package_root/'packager-source/package.py').resolve()
    result=package.verify(package_root);assert result['package_verified'] and result['complete'] is False
    cov=json.loads((package_root/'inherited-coverage.json').read_text());proof=json.loads((package_root/'evidence/proofs/read-only-proof.json').read_text());origin=json.loads((root/'ORIGIN-BINDINGS.json').read_text());terminal=json.loads((root/'TERMINAL-BINDINGS.json').read_text())
    assert sha(package_root/'evidence/proofs/read-only-proof.json')==origin['proof_sha256']=='4f0146a2e52ff4953fdf6e2be1333fe7a3c375538a5b10c7db512f58b0156a85'
    assert sha(package_root/'evidence/proofs/family-verification.json')==origin['family_report_sha256']=='53818c2ea07a257cba24b8c86f0cc12b31b4d4af367aba488c9f2696c1faed74'
    assert sha(package_root/'inherited-coverage.json')==origin['coverage_sha256']=='f07572dbd7052805215aeac74962fda18e67a79e067094df73b7e873fd5573d9'
    assert proof['status']=='verified_publication' and proof['verification_exit']==0 and proof['acceptance']['acceptance_gaps']==[]
    assert cov['publication_accepted'] is True and cov['complete'] is True and cov['source_consistency_complete'] is True and cov['whole_jurisdiction_complete'] is False
    assert terminal['writer_modules_after']==origin['writer_modules_before']==package.code()
    rows=json.loads((package_root/'aggregate-fulltext.json').read_text())['provisions'];assert len(rows)==2661 and sum(r['full_text'].count('[IMAGE]') for r in rows)==882
    assert len(proof['evidence_sha256_before'])==558 and not calls
    print(json.dumps({'passed':True,'selected_files':len(m['files']),'source_input_files':558,'records':2661,'image_markers':882,'actual_current_common_status':'verified_publication','actual_current_common_exit':0,'inherited_primary_publication_accepted':True,'inherited_primary_complete':True,'strict_jurisdiction_complete':False,'corpus_package_verified':True,'corpus_strict_complete':False,'current8writer_bound':True,'source_normalizer_calls':0,'publisher_requests':0,'native_or_image_operations':0,'read_only':True},indent=2))
if __name__=='__main__':main()
