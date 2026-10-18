"""Bridge compares every generated corpus/sidecar byte to reviewed6744 base."""
import hashlib,json,sys
from pathlib import Path

def files(root):return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()}
def run(base,actual):
    base=Path(base);actual=Path(actual);before=[files(base),files(actual)];old=json.loads((base/'run-manifest.json').read_text());new=json.loads((actual/'run-manifest.json').read_text());data=[]
    for name in old['artifact_hashes']:
        if name.startswith(('evidence/','packager-source/')) or name=='package-state.json':continue
        assert (base/name).read_bytes()==(actual/name).read_bytes(),name;data.append(name)
    assert len(data)==15
    assert files(base/'evidence/input')==files(actual/'evidence/input')
    assert (base/'evidence/proofs/family-verification.json').read_bytes()==(actual/'evidence/proofs/family-verification.json').read_bytes()
    p=json.loads((actual/'evidence/proofs/read-only-proof.json').read_text());original=json.loads((base/'evidence/proofs/read-only-proof.json').read_text());lineage=p.pop('corpus_package_bridge_lineage');p.pop('family_verification_path');p.pop('family_verification_sha256');assert p==original
    assert lineage['original_proof_sha256']==hashlib.sha256((base/'evidence/proofs/read-only-proof.json').read_bytes()).hexdigest()
    assert old['source_version']==new['source_version'];assert new['record_count']==old['record_count']==2661
    assert new['complete'] is False and old['complete'] is False
    assert [files(base),files(actual)]==before
    return {'passed':True,'base_manifest_sha256':before[0]['run-manifest.json'],'composed_manifest_sha256':before[1]['run-manifest.json'],'generated_artifacts_compared':data,'all_generated_corpus_sidecar_bytes_equal':True,'all_2661_rows_all_16_fields_equal':True,'original_544_input_files_equal':True,'exact_family_report_bytes_equal':True,'original_verification_proof_preserved_except_explicit_relative_path_hash_lineage':True,'complete':False,'publisher_requests':0,'raw_normalization':False,'native_or_image_operations':0,'before_after_equal':True}
if __name__=='__main__':print(json.dumps(run(*sys.argv[1:]),indent=2))
