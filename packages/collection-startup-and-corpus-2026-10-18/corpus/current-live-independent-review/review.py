"""Current live-source package consumer and shipped relocation; no source reparse."""
import sys
sys.dont_write_bytecode=True
import argparse,csv,hashlib,importlib,io,json,os,pathlib,shutil,socket,subprocess,tempfile,time
from unittest.mock import patch
from urllib.parse import urldefrag
ROOT=pathlib.Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00')
HERE=pathlib.Path(__file__).resolve().parent
LIVE=ROOT/'outputs/collection-readiness-postf561-2026-10-17/originals-live-early-inventory'
SOURCE=LIVE/'flagstaff-common-early-inventory-live-v1'
REPO=ROOT/'github/local-jurisdiction-collection'
BASE=ROOT/'outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59/corpus-package-fidelity-candidate-v1/actual/flagstaff-package-v2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
lines=lambda p:[json.loads(s) for s in p.read_text(encoding='utf-8').split('\n') if s]
def tree(root):
    result={}
    for p in sorted(root.rglob('*')):
        assert not p.is_symlink()
        if p.is_file():result[p.relative_to(root).as_posix()]=sha(p)
    return result
ap=argparse.ArgumentParser();ap.add_argument('--packet',type=pathlib.Path,required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--expected-manifest',required=True);ap.add_argument('--package',required=True);a=ap.parse_args()
PACKET=a.packet.resolve();PACK=PACKET/a.package;MAN=PACKET/a.manifest
assert sha(MAN)==a.expected_manifest
selected=load(MAN)['files']
def frozen():
    assert sha(MAN)==a.expected_manifest
    for name,e in selected.items():assert (PACKET/name).stat().st_size==e['bytes'] and sha(PACKET/name)==e['sha256'],name
frozen();start=time.monotonic()
readonly=LIVE/'current-common-readonly.json';assert sha(readonly)=='4f0146a2e52ff4953fdf6e2be1333fe7a3c375538a5b10c7db512f58b0156a85'
proof=load(readonly);family=pathlib.Path(proof['log']);assert sha(family)=='53818c2ea07a257cba24b8c86f0cc12b31b4d4af367aba488c9f2696c1faed74'
assert proof['status']=='verified_publication' and proof['verification_exit']==0 and proof['family_verifier_passed'] is True
assert proof['evidence_read_only'] is True and proof['publisher_requests']==0 and proof['runtime_changed_during_run'] is proof['source_changed_during_run'] is False
assert tree(SOURCE)==proof['evidence_sha256_before']==proof['evidence_sha256_after']
assert len(proof['evidence_sha256_before'])==558
assert proof['collector_sources_before']==proof['collector_sources_after']
for name,h in proof['collector_sources_before'].items():assert sha(REPO/name)==h,name
assert sha(pathlib.Path(proof['runtime_receipt_path']))==proof['runtime_receipt_sha256']=='2d1f08b78d8a4e3479d6ed4e8799e7afb890ee6612929bea731efa7f0af87f1e'
family_report=load(family)
for flag in ['full_raw_replay_equal','source_route_ledger_verified','opening_body_closing_chronology_verified','source_consistency_complete','publication_accepted','complete']:assert family_report[flag] is True
assert family_report['input_files_modified'] is False and family_report['whole_jurisdiction_complete'] is False
raw=PACK/'evidence/input';assert tree(raw)==proof['evidence_sha256_before']
stored_proof=load(PACK/'evidence/proofs/read-only-proof.json')
assert all(stored_proof[k]==v for k,v in proof.items())
assert (PACK/'evidence/proofs/family-verification.json').read_bytes()==family.read_bytes()
coverage=load(raw/'coverage.json');assert sha(raw/'coverage.json')=='f07572dbd7052805215aeac74962fda18e67a79e067094df73b7e873fd5573d9'
assert (PACK/'inherited-coverage.json').read_bytes()==(raw/'coverage.json').read_bytes()
for flag in ['publication_text_complete','attachments_complete','legal_structure_qualified','source_consistency_complete','publication_accepted','complete']:assert coverage[flag] is True
for flag in ['whole_jurisdiction_complete','external_adopted_legal_dependency_closure_complete','independent_final_review_complete']:assert coverage[flag] is False
summary=coverage['formats']['html']['summary'];assert summary['source_navigation_complete'] is False and summary['source_target_coverage_complete'] is True
source=load(raw/'source/checkpoint.json');assert source['inventory']==load(BASE/'evidence/input/source/checkpoint.json')['inventory']
ir=lines(raw/'normalized/records.jsonl');assert sha(raw/'normalized/records.jsonl')==sha(BASE/'evidence/input/normalized/records.jsonl')=='1344484a99e9dce522f72d2254b713e9b725d552bb28d174c3fb66884a7fae5b'
rows=load(PACK/'aggregate-fulltext.json')['provisions'];base_rows=load(BASE/'aggregate-fulltext.json')['provisions']
nodes=lines(PACK/'source-nodes.jsonl');base_nodes=lines(BASE/'source-nodes.jsonl')
disp=lines(PACK/'node-dispositions.jsonl');prov=lines(PACK/'record-provenance.jsonl')
assert len(rows)==len(ir)==len(nodes)==len(disp)==len(prov)==2661
assert disp==lines(BASE/'node-dispositions.jsonl')
assert len(source['inventory'])==2658 and len({n['node_id'] for n in nodes})==2661
for current,old in zip(nodes,base_nodes):
    for key in ['node_id','parent_node_id','source_order','node_kind','display_heading','source_url']:assert current[key]==old[key]
    assert current['source_version']=='sha256:'+sha(raw/'source/checkpoint.json')
    assert sha(PACK/current['raw_artifact_path'])==current['raw_sha256']
cfg=load(raw/'checkpoint.json')['config'];receipts={x['source_url']:x for x in source['artifacts'] if x['role']=='content'}
FIELDS='jurisdiction code_name division title subtitle chapter subchapter article part subpart section_number section_name citation full_text source_url scrape_date'.split()
for i,(record,row,old,q) in enumerate(zip(ir,rows,base_rows,prov)):
    receipt=receipts[urldefrag(record['source_url'])[0]];expected=dict(old,code_name=cfg['publication'],scrape_date=receipt['started_at'])
    assert list(row)==FIELDS and all(isinstance(v,str) for v in row.values()) and row==expected,(i,record['heading'])
    assert row['full_text']==record['semantic_html'] and row['full_text'].count('[IMAGE]')==record['image_placeholder_count']
    assert q['record_id']==record['record_id'] and q['row_ordinal']==i and q['rich_ir']['line_ordinal']==i
    assert q['source_version']['snapshot_id']=='sha256:'+sha(raw/'source/checkpoint.json')
    assert q['locator']['block_indices']==record['block_indices']
    assert q['raw_sha256']==sha(PACK/q['raw_artifact_path'])==record['source_sha256']==receipt['sha256']
assert sum(x['full_text'].count('[IMAGE]') for x in rows)==882
assert summary['source_tables']==summary['owned_tables']==377 and summary['source_blocks']==summary['owned_blocks']==24237
manifest=load(PACK/'run-manifest.json');pid=manifest['publication_id'];assert pid==proof['publication_id']=='original-flagstaff-az-primary'
for stem in ['aggregate-fulltext','aggregate-toc','publications/'+pid+'/fulltext','publications/'+pid+'/toc']:
    expected=[dict(r,full_text='') for r in rows] if stem.endswith('toc') else rows
    assert load(PACK/(stem+'.json'))['provisions']==expected
    data=(PACK/(stem+'.csv')).read_bytes();assert data[:3]==b'\xef\xbb\xbf';csv.field_size_limit(64*1024*1024)
    reader=csv.DictReader(io.StringIO(data.decode('utf-8-sig'),newline=''));assert reader.fieldnames==FIELDS and list(reader)==expected
modules=manifest['binding']['packager_code'];assert len(modules)==8
for name,h in modules.items():assert sha(PACK/'packager-source'/name)==sha(REPO/'collectors/corpus_package'/name)==h
sys.path.insert(0,str(PACK/'packager-source'));package=importlib.import_module('package');common=importlib.import_module('common')
from PIL import Image
calls=[]
def no(*a,**k):calls.append('forbidden network/image operation');raise AssertionError(calls[-1])
before=common.files(PACK)
with patch.object(socket,'socket',side_effect=no),patch.object(socket,'create_connection',side_effect=no),patch.object(Image,'open',side_effect=no):verified=package.verify(PACK)
assert verified['package_verified'] and verified['serialization_complete'] and verified['complete'] is False
assert verified['inherited_gate_values']['publication_accepted'] is True and verified['inherited_gate_values']['complete'] is True
assert verified['inherited_gate_values']['whole_jurisdiction_complete'] is False
assert before==common.files(PACK) and not calls
with tempfile.TemporaryDirectory() as temp:
    td=pathlib.Path(temp);moved=td/'relocated';shutil.copytree(PACK,moved);before_move=common.files(moved)
    env=dict(os.environ)
    for name in ['PYTHONDONTWRITEBYTECODE','PYTHONPYCACHEPREFIX','PYTHONPATH']:env.pop(name,None)
    result=subprocess.run([sys.executable,str(moved/'packager-source/package.py'),'verify','--out',str(moved)],cwd=td,env=env,text=True,capture_output=True)
    (HERE/'direct-ordinary-relocated.stdout').write_text(result.stdout);(HERE/'direct-ordinary-relocated.stderr').write_text(result.stderr)
    assert result.returncode==2 and json.loads(result.stdout)==verified
    assert before_move==common.files(moved) and not list(moved.rglob('__pycache__'))
assert tree(SOURCE)==proof['evidence_sha256_before'];frozen()
report={'passed':True,'scope':'Current live-source Flagstaff full corpus export and current promoted writer verification; no raw source normalization or publisher work',
        'packet':str(PACKET.relative_to(ROOT)),'packet_manifest_sha256':a.expected_manifest,'selected_packet_files_checked':len(selected),
        'package_manifest_sha256':sha(PACK/'run-manifest.json'),'current_common_readonly_sha256':sha(readonly),'family_report_sha256':sha(family),
        'source_input_files':558,'collector_source_files_rehashed':len(proof['collector_sources_before']),'runtime_receipt_sha256':proof['runtime_receipt_sha256'],
        'current_promoted_writer_modules_sha256':modules,'records':2661,'source_TOC_nodes':2658,'body_only_nodes':3,
        'all_16_fields_JSON_CSV_BOM_TOC_current_dates_source_version_and_raw_provenance_verified':True,
        'current_IR_and_source_ancestry_equal_prior_independently_reviewed_source':True,'all_source_nodes_parents_and_dispositions_unchanged':True,
        'tables':377,'owned_source_blocks':24237,'exact_IMAGE_positions':882,
        'current_collection_and_common_readonly_exit':0,'primary_publication_accepted':True,'publication_text_complete':True,
        'required_nonimage_documents_complete':True,'legal_structure_qualified':True,'source_consistency_complete':True,
        'literal_source_navigation_complete':False,'source_target_coverage_complete':True,
        'native_capture_verified':False,'edition_complete':None,'whole_jurisdiction_complete':False,
        'external_adopted_legal_dependency_closure_complete':False,'independent_final_review_complete':False,
        'package_verified':True,'serialization_complete':True,'strict_downstream_package_complete':False,'relocated_shipped_ordinary_CLI_exit':result.returncode,
        'strict_exit_explanation':'Exit2 preserves the unproved jurisdiction/adopted-layer/final-review gates; it does not negate current accepted primary-publication collection and read-only verification exit0.',
        'forbidden_calls':calls,'original_and_package_unchanged':True,'seconds':time.monotonic()-start,
        'limits':['No repeated27unit tests, raw source normalizer, native parser, publisher calls or image operations.',
                  'Literal source navigation false is retained separately from true source-target coverage, not silently repaired.',
                  'Primary operational acceptance does not establish current legal edition, native capture, adopted-layer closure or whole jurisdiction completeness.']}
(HERE/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'records':2661,'input_files':558,'primary_accepted':True,'strict_package_complete':False,'seconds':report['seconds']},indent=2))
