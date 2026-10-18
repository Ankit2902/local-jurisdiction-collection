"""Independent final composed Flagstaff bridge; exact prior source proof retained."""
import sys
sys.dont_write_bytecode=True
import ast,hashlib,importlib,json,os,pathlib,shutil,socket,subprocess,tempfile,time
from unittest.mock import patch
ROOT=pathlib.Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00')
PARENT=ROOT/'outputs/collection-readiness-next-2026-10-17/encodeplus/post-91f6c59'
BASE=PARENT/'corpus-package-fidelity-candidate-v1/actual/flagstaff-package-v2'
BRIDGE=PARENT/'corpus-package-composed-flagstaff-bridge-v3'
PACK=BRIDGE/'actual/flagstaff-composed-package-v3'
COMPOSITION=ROOT/'outputs/collection-readiness-post1997ee1-2026-10-17/qa/corpus-readers-municode-encodeplus-v1'
HERE=pathlib.Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
start=time.monotonic()
ready=load(BRIDGE/'BRIDGE-READY.json')
assert sha(BRIDGE/'BRIDGE-MANIFEST.json')==ready['manifest_sha256']=='ef1cd9b11e7c2eff4c974e1eef97d748017b1f2294a1dc0b6e8202e15f982749'
selected=load(BRIDGE/'BRIDGE-MANIFEST.json')['files']
def check_freeze():
    for name,e in selected.items():
        p=BRIDGE/name
        assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],name
check_freeze()
old=load(BASE/'run-manifest.json');new=load(PACK/'run-manifest.json')
assert sha(BASE/'run-manifest.json')=='2d344503a188d131cd9bcc69742f13ba1eb6b0a2e7bd71fa29f6b73c6b4ba6c5'
assert sha(PACK/'run-manifest.json')==ready['actual_manifest_sha256']=='acca7c382bd20afa33081f9fa84c7e21dbef9d648fd514bfa881a7a268e243dc'
data_names=[n for n in old['artifact_hashes'] if not n.startswith(('evidence/','packager-source/')) and n!='package-state.json']
assert len(data_names)==15
for name in data_names:
    assert (BASE/name).read_bytes()==(PACK/name).read_bytes()
    assert sha(PACK/name)==old['artifact_hashes'][name]==new['artifact_hashes'][name]
assert old['binding']['input_files']==new['binding']['input_files']
assert len(new['binding']['input_files'])==544
for name,h in new['binding']['input_files'].items():
    assert (BASE/'evidence/input'/name).read_bytes()==(PACK/'evidence/input'/name).read_bytes()
    assert sha(PACK/'evidence/input'/name)==h
for key in ['source_version','source_config','acquisition_interval','record_count','complete']:
    assert old[key]==new[key]
assert new['record_count']==2661 and new['complete'] is False

frozen=load(COMPOSITION/'SOURCE-FREEZE.json');frozen_sha=sha(COMPOSITION/'SOURCE-FREEZE.json')
modules=ready['writer_module_hashes']
assert len(modules)==8 and modules==new['binding']['packager_code']
for name,h in modules.items():
    assert frozen['files'][name]==h==sha(COMPOSITION/'candidate'/name)==sha(PACK/'packager-source'/name)==sha(BRIDGE/'writer-tests'/name)
    # The shipped writer/reader path does not import network/native/image APIs.
    tree=ast.parse((PACK/'packager-source'/name).read_text());imports=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):imports.extend(a.name for a in node.names)
        elif isinstance(node,ast.ImportFrom):imports.append(node.module or '')
    assert not any(x in {'requests','http','urllib.request','subprocess','PIL','pypdf','pdfplumber','pypdfium2','fitz','playwright'} for x in imports)

# The only source-proof augmentation is explicitly relative report selection and
# lineage. Original common receipt/report bytes remain unchanged.
original_proof=BRIDGE/'bridge-input-proofs/original-read-only-proof.json'
assert original_proof.read_bytes()==(BASE/'evidence/proofs/read-only-proof.json').read_bytes()
proof=load(PACK/'evidence/proofs/read-only-proof.json')
lineage=proof.pop('corpus_package_bridge_lineage')
relative=proof.pop('family_verification_path')
report_sha=proof.pop('family_verification_sha256')
assert proof==load(original_proof)
assert lineage['original_proof_sha256']==sha(original_proof)
assert report_sha==sha(BRIDGE/'bridge-input-proofs'/relative)==sha(PACK/'evidence/proofs/family-verification.json')
assert (PACK/'evidence/proofs/family-verification.json').read_bytes()==(BASE/'evidence/proofs/family-verification.json').read_bytes()
assert not pathlib.PurePosixPath(relative).is_absolute() and '..' not in pathlib.PurePosixPath(relative).parts

sys.path.insert(0,str(PACK/'packager-source'));package=importlib.import_module('package');common=importlib.import_module('common')
from PIL import Image
calls=[]
def no(*a,**k):calls.append('forbidden image/network operation');raise AssertionError(calls[-1])
before=common.files(PACK)
with patch.object(socket,'socket',side_effect=no),patch.object(socket,'create_connection',side_effect=no),patch.object(Image,'open',side_effect=no):
    verified=package.verify(PACK)
assert verified['package_verified'] and verified['serialization_complete'] and not verified['complete']
assert common.files(PACK)==before and not calls

env=dict(os.environ)
for name in ['PYTHONDONTWRITEBYTECODE','PYTHONPYCACHEPREFIX','PYTHONPATH']:env.pop(name,None)
with tempfile.TemporaryDirectory() as temp:
    td=pathlib.Path(temp);moved=td/'relocated';shutil.copytree(PACK,moved);copied_before=common.files(moved)
    command=[sys.executable,str(moved/'packager-source/package.py'),'verify','--out',str(moved)]
    result=subprocess.run(command,cwd=td,env=env,text=True,capture_output=True)
    (HERE/'direct-ordinary-relocated.stdout').write_text(result.stdout);(HERE/'direct-ordinary-relocated.stderr').write_text(result.stderr)
    assert result.returncode==2 and json.loads(result.stdout)==verified
    assert common.files(moved)==copied_before and not list(moved.rglob('__pycache__'))
    negative_out=td/'must-not-exist'
    negative=subprocess.run([sys.executable,str(moved/'packager-source/package.py'),'package','--reader','originals-flagstaff-html-v1','--input',str(moved/'evidence/input'),'--proof',str(original_proof),'--out',str(negative_out)],cwd=td,env=env,text=True,capture_output=True)
    (HERE/'historical-absolute-default-refusal.stdout').write_text(negative.stdout)
    assert negative.returncode==1 and not negative_out.exists() and 'family_verification_path required' in negative.stdout
    assert common.files(moved)==copied_before
check_freeze()
assert sha(COMPOSITION/'SOURCE-FREEZE.json')==frozen_sha
for name,h in modules.items():assert sha(COMPOSITION/'candidate'/name)==h
coverage=load(PACK/'inherited-coverage.json')
assert coverage==load(BASE/'inherited-coverage.json') and not coverage['source_consistency_complete'] and not coverage['publication_accepted'] and not coverage['whole_jurisdiction_complete']
report={'passed':True,'scope':'Exact final eight-module composition with retained Flagstaff data; no source normalization or acquisition',
        'bridge_manifest_sha256':ready['manifest_sha256'],'selected_files_checked':len(selected),
        'actual_package_manifest_sha256':sha(PACK/'run-manifest.json'),'composition_source_freeze_sha256':frozen_sha,
        'writer_modules_sha256':modules,'reviewed_base_package_manifest_sha256':sha(BASE/'run-manifest.json'),
        'all_15_generated_artifacts_byte_identical':data_names,'all_2661_rows_16_fields_source_parents_dispositions_unchanged':True,
        'all_544_original_input_files_exact':True,'canonical_HTML_tables_lists_notes_882_IMAGE_positions_unchanged':True,
        'source_identity_version_date_citation_and_false_gates_unchanged':True,
        'proof_augmentation_only_relative_report_hash_and_explicit_lineage':True,'original_common_receipt_and_report_exact_bytes_retained':True,
        'inprocess_shipped_package_verify_passed_under_socket_Image_open_tripwires':True,
        'ordinary_direct_relocated_shipped_CLI_exit':result.returncode,'bytecode_or_package_mutation':False,
        'untouched_historical_absolute_log_default_refused_before_output':True,'forbidden_calls':calls,
        'serialization_complete':True,'source_consistency_complete':False,'publication_accepted':False,'whole_publication_complete':False,
        'candidate_source_original_and_bridge_unchanged':True,'seconds':time.monotonic()-start,
        'limitations':['Final composition executes the Flagstaff reader only; MC/EP semantic/native review remains separate.',
                       'Prior exact base all-field/source-parent and27 MIME tests were not needlessly repeated; equality preserves those actual Flagstaff data assertions.',
                       'Owner executed the fresh default-relative-report packaging build; this review independently checks its exact bytes/lineage and current verification, plus the absolute-default refusal.',
                       'No new current legal edition, dependency closure, jurisdiction completeness or live acquisition claim.']}
(HERE/'review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':True,'data_artifacts':15,'input_files':544,'records':2661,'source_freeze':frozen_sha,'seconds':report['seconds']},indent=2))
