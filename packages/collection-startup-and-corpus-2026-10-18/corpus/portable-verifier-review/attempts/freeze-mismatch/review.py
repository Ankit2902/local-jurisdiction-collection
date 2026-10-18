"""Scoped orchestration/path/provenance review; no source normalizer rerun."""
import sys
sys.dont_write_bytecode=True
import hashlib,importlib,json,os,pathlib,shutil,socket,subprocess,tempfile,time,unittest
from unittest.mock import patch
ROOT=pathlib.Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00')
BASE=ROOT/'outputs/collection-readiness-post1997ee1-2026-10-17/qa/corpus-readers-municode-encodeplus-v1'
CAND=BASE/'candidate'
HERE=pathlib.Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
def tree(root):
    result={}
    for p in sorted(root.rglob('*')):
        assert not p.is_symlink()
        if p.is_file():result[p.relative_to(root).as_posix()]=sha(p)
    return result
freeze=load(BASE/'SOURCE-FREEZE.json')
freeze_sha=sha(BASE/'SOURCE-FREEZE.json')
def check_source():
    assert sha(BASE/'SOURCE-FREEZE.json')==freeze_sha
    for name,h in freeze['files'].items():assert sha(CAND/name)==h,name
check_source()
sys.path.insert(0,str(CAND))
vi=importlib.import_module('verify_input')
interfaces=importlib.import_module('test_verify_input_interface')
readers=importlib.import_module('test_html_readers')
from PIL import Image
calls=[]
def no(*args,**kwargs):calls.append('forbidden operation');raise AssertionError(calls[-1])
start=time.monotonic()
actual=[]
with patch.object(socket,'create_connection',side_effect=no),patch.object(socket.socket,'connect',side_effect=no),patch.object(Image,'open',side_effect=no):
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(interfaces.Interface),readers.Readers('test_raw_separate_notes_present_but_old_ir_empty_refused')])
    with (HERE/'tests.log').open('w') as out:result=unittest.TextTestRunner(stream=out,verbosity=2).run(suite)
    assert result.wasSuccessful() and result.testsRun==7
    # Recompute every input and collector file hash, not only maps' equality.
    for name in ['henderson','charter']:
        directory=BASE/'portable-verification'/name
        proof=load(directory/'read-only-proof.json')
        family=load(directory/'family-verification.json')
        verify=proof['verification']
        input_root=BASE/'packages'/name/'evidence/input'
        source_root=pathlib.Path(verify['captured_runtime_root'])
        assert proof['evidence_read_only'] is True and proof['publisher_requests']==0
        assert proof['source_changed_during_run'] is proof['runtime_changed_during_run'] is False
        assert tree(input_root)==proof['evidence_sha256_before']==proof['evidence_sha256_after']
        prefix='collectors/encodeplus/' if name=='charter' else ''
        assert {prefix+k:v for k,v in tree(source_root).items()}==proof['collector_sources_before']==proof['collector_sources_after']
        assert vi.runtime()==verify['runtime_before']==verify['runtime_after']
        assert verify['adapter_source_sha256']==sha(CAND/'verify_input.py')
        assert verify['module_sha256']==sha(source_root/'verify.py')
        assert pathlib.Path(verify['module_file']).resolve()==source_root/'verify.py'
        assert verify['family_report_sha256']==sha(directory/'family-verification.json')
        assert verify['forbidden_calls']==[]
        assert proof['family_verification_path']=='family-verification.json'
        assert proof['selected_config']==load(input_root/'checkpoint.json')['config' if name=='charter' else 'binding']
        actual.append({'name':name,'input_files':len(proof['evidence_sha256_before']),'collector_files':len(proof['collector_sources_before']),
                       'proof_sha256':sha(directory/'read-only-proof.json'),'family_report_sha256':sha(directory/'family-verification.json'),
                       'module_sha256':verify['module_sha256'],'runtime_python_sha256':verify['runtime_before']['python_executable_sha256'],
                       'runtime_packages':verify['runtime_before']['packages'],
                       'family_status':family.get('status',family.get('passed')),
                       'explicit_historical_source_no_current_equivalence':verify['source_revision_selection'],
                       'complete_before_after_maps_recomputed':True})
assert not calls

# Fresh controlled verifier sources exercise the ordinary direct CLI in isolated
# relocated trees. They are orchestration controls, never source replay claims.
env=dict(os.environ)
for name in ['PYTHONDONTWRITEBYTECODE','PYTHONPYCACHEPREFIX','PYTHONPATH']:env.pop(name,None)
controls=[]
specimens={
    'ordinary_success':"def verify(root):\n return {'status':'synthetic only, not raw-replay proof','publication_complete':False}\n",
    'input_mutation':"def verify(root):\n (root/'new-file.txt').write_text('mutation')\n return {'status':'synthetic'}\n",
    'source_mutation':"from pathlib import Path\ndef verify(root):\n Path(__file__).with_name('new-source.txt').write_text('mutation')\n return {'status':'synthetic'}\n",
    'runtime_identity_mutation':"def verify(root):\n import importlib.metadata\n importlib.metadata.distributions=lambda: []\n return {'status':'synthetic'}\n",
    'network_tripwire':"def verify(root):\n import socket\n socket.create_connection(('example.invalid',443))\n return {'status':'synthetic'}\n",
    'image_decoder_tripwire':"def verify(root):\n from PIL import Image\n Image.open('must-not-be-opened')\n return {'status':'synthetic'}\n",
}
for name,source in specimens.items():
    with tempfile.TemporaryDirectory() as temp:
        td=pathlib.Path(temp)
        shipped=td/'shipped';shipped.mkdir()
        shutil.copy2(CAND/'verify_input.py',shipped/'verify_input.py')
        collector=td/'explicit-source';collector.mkdir()
        (collector/'verify.py').write_text(source)
        # Complete maps must retain bytecode-named files, not silently filter them.
        (collector/'retained.pyc').write_bytes(b'Synthetic retained source artifact, not executed')
        inp=td/'input';inp.mkdir()
        (inp/'checkpoint.json').write_text(json.dumps({'phase':'finished','config':{'base':'https://source.invalid/regs/control/'}}))
        (inp/'retained.pyc').write_bytes(b'Synthetic retained input artifact, not executed')
        output=td/'proof'
        before=tree(inp);sources_before=tree(collector)
        command=[sys.executable,str(shipped/'verify_input.py'),'--reader','encodeplus-html-publication-v1','--input',str(inp),'--collector-root',str(collector),'--publication-id','synthetic-control','--out',str(output)]
        cp=subprocess.run(command,cwd=td,env=env,text=True,capture_output=True)
        (HERE/(name+'.stdout')).write_text(cp.stdout)
        (HERE/(name+'.stderr')).write_text(cp.stderr)
        observed=json.loads(cp.stdout)
        if name=='ordinary_success':
            assert cp.returncode==0 and observed['verification_adapter_complete'] is True
            proof=load(output/'read-only-proof.json')
            assert proof['evidence_sha256_before']==proof['evidence_sha256_after']==before
            assert proof['collector_sources_before']==proof['collector_sources_after']=={'collectors/encodeplus/'+k:v for k,v in sources_before.items()}
            assert proof['verification']['runtime_before']==proof['verification']['runtime_after']
            assert proof['publication_id']=='synthetic-control' and proof['verification']['forbidden_calls']==[]
            assert observed['publication_acceptance_added'] is False
            assert load(output/'family-verification.json')['publication_complete'] is False
            assert tree(inp)==before and tree(collector)==sources_before
        else:
            assert cp.returncode==1 and observed['verified'] is False
            assert not (output/'read-only-proof.json').exists()
            if name=='input_mutation':assert observed['evidence_unchanged'] is False
            elif name=='source_mutation':assert observed['collector_sources_unchanged'] is False
            elif name=='runtime_identity_mutation':assert observed['runtime_unchanged'] is False
            else:
                assert observed['forbidden_calls']==['forbidden_network_or_image']
                assert tree(inp)==before and tree(collector)==sources_before
        assert not list(collector.rglob('__pycache__')) and not list(shipped.rglob('__pycache__'))
        controls.append({'case':name,'returncode':cp.returncode,'result':observed})
check_source()
report={'passed':True,'scope':'Portable verification orchestration, report-path CLI and raw Notes fail-closed control; source-reader semantic review remains separate',
        'source_freeze_sha256':freeze_sha,'candidate_source_sha256':freeze['files'],'selected_interface_and_raw_note_tests':7,
        'actual_historical_proofs':actual,'all_actual_before_after_input_source_runtime_maps_equal_recomputed':True,
        'all_recorded_python_and_dependency_identities_equal_current_review_runtime':True,
        'direct_ordinary_relocated_controls':controls,'historical_absolute_log_not_implicitly_followed':True,
        'safe_relative_report_and_explicit_report_controls_passed':True,
        'raw_Notes_and_Footnotes_present_with_old_empty_IR_refused':True,
        'no_repeated_actual_source_normalization_or_native_parse':True,'candidate_sources_unchanged':True,
        'forbidden_calls_during_actual_map_and_interface_review':calls,'seconds':time.monotonic()-start,
        'limitations':['Actual family raw replay execution was performed by owner; this review independently recomputed its complete byte maps and source/runtime identities without executing it again.',
                       'Six controlled verifier sources are orchestration fault probes, not acquisition or semantic qualification.',
                       'Adapter success means a report was generated under recorded explicit code; family/source/publication acceptance must still be checked by the selected reader.',
                       'Historical explicitly chosen collector code is not relabelled as current production.']}
(HERE/'review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':True,'tests':7,'controlled_cases':len(controls),'actual_proof_maps':[(x['name'],x['input_files'],x['collector_files']) for x in actual],'seconds':report['seconds']},indent=2))
