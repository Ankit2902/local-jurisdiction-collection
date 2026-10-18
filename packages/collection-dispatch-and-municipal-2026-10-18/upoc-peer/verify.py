"""Portable, stdlib-only peer verification. No native PDF or image imports."""
import argparse, hashlib, json, pathlib, sys
sys.dont_write_bytecode=True
from audit_artifacts import audit
def verify(packet):
    here=pathlib.Path(__file__).resolve().parent
    manifest=json.loads((here/'MANIFEST.json').read_text())
    files={r['path']:r for r in manifest['files']}
    actual={p.relative_to(here).as_posix():p for p in here.rglob('*') if p.is_file()and p.name!='MANIFEST.json'}
    assert set(actual)==set(files),'Peer packet inventory changed'
    for name,p in actual.items():
        assert p.stat().st_size==files[name]['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==files[name]['sha256'],'Peer bytes changed '+name
    report=json.loads((here/'review.json').read_text())
    result=audit(packet)
    assert result['manifest_sha256']==report['selected_source_packet']['manifest_sha256'],'Wrong source packet/revision'
    assert report['status']=='PASS' and result['passed']
    return {'verified':True,'peer_status':'PASS','peer_files':len(files),'selected_source_manifest':result['manifest_sha256'],'all172_source_and_cached_records_verified':True,'native_parser_or_image_operations':0}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-packet',required=True,type=pathlib.Path)
    print(json.dumps(verify(p.parse_args().source_packet),indent=2))
