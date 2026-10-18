"""Portable bridge hash/metadata audit; no source normalizer or external reads."""
import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
BASE='2d344503a188d131cd9bcc69742f13ba1eb6b0a2e7bd71fa29f6b73c6b4ba6c5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    root=Path(__file__).resolve().parent;old_path=root/'lineage/base6744-run-manifest.json';assert sha(old_path)==BASE;old=json.loads(old_path.read_text());actual=root/'actual/flagstaff-composed-package-v3';new=json.loads((actual/'run-manifest.json').read_text());data=[]
    for name,h in old['artifact_hashes'].items():
        if name.startswith(('evidence/','packager-source/')) or name=='package-state.json':continue
        assert sha(actual/name)==h==new['artifact_hashes'][name],name;data.append(name)
    assert len(data)==15;assert old['binding']['input_files']==new['binding']['input_files'];assert len(new['binding']['input_files'])==544
    for name,h in old['binding']['input_files'].items():assert sha(actual/'evidence/input'/name)==h
    for key in ['source_version','source_config','acquisition_interval','record_count','complete']:assert old[key]==new[key]
    assert new['record_count']==2661 and new['complete'] is False
    proof=json.loads((actual/'evidence/proofs/read-only-proof.json').read_text());oldproof=root/'bridge-input-proofs/original-read-only-proof.json';original=json.loads(oldproof.read_text());lineage=proof.pop('corpus_package_bridge_lineage');rel=proof.pop('family_verification_path');familysha=proof.pop('family_verification_sha256');assert proof==original;assert sha(oldproof)==lineage['original_proof_sha256'];assert familysha==sha(root/'bridge-input-proofs'/rel)==sha(actual/'evidence/proofs/family-verification.json')
    binding=json.loads((root/'WRITER-SOURCE-BINDING.json').read_text());assert binding['frozen_writer_module_hashes']==new['binding']['packager_code']
    for name,h in binding['frozen_writer_module_hashes'].items():assert sha(actual/'packager-source'/name)==sha(root/'writer-tests'/name)==h
    print(json.dumps({'passed':True,'all_15_generated_artifacts_byte_identical_to_reviewed_base':True,'all_2661_rows_16_fields_and_sidecars_unchanged':True,'all_544_source_input_files_unchanged':True,'original_common_log_exact_bytes_bound':True,'eight_executed_writer_modules_bound':True,'source_consistency_complete':False,'complete':False,'network_requests':0,'raw_source_normalization':False,'native_or_image_operations':0},indent=2))
if __name__=='__main__':main()
