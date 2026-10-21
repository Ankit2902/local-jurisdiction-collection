"""Pure offline16-column corpus packaging; verified source IR remains immutable."""
from __future__ import annotations
import sys
from pathlib import Path as _Path
_root = _Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
from collectors.winboot import ensure_fcntl
ensure_fcntl()
sys.dont_write_bytecode=True
import argparse,csv,fcntl,io,json,tempfile
from pathlib import Path
from common import *
from readers import reader,READERS

HERE=Path(__file__).resolve().parent
MODULES=['common.py','readers.py','flagstaff.py','flagstaff_hierarchy.py','package.py','reader_utils.py','municode_html.py','encodeplus_html.py','readiness.py','ecode_html.py','american_legal_html.py','american_legal_attachment.py','municipal_codes_html.py']
IMAGE_SUFFIXES={'.png','.jpg','.jpeg','.gif','.webp','.svg','.bmp','.avif','.tif','.tiff','.ico'}
def code():return {n:sha((HERE/n).read_bytes()) for n in MODULES}
def validate_input(root,proof,family):
    root=Path(root).resolve()
    require(proof.get('evidence_read_only') is True and proof.get('publisher_requests')==0 and proof.get('source_changed_during_run') is False and proof.get('runtime_changed_during_run') is False,'Missing unchanged read-only verification binding')
    before=proof.get('evidence_sha256_before');after=proof.get('evidence_sha256_after')
    require(isinstance(before,dict) and before and before==after,'Verification evidence changed or unbound')
    require(proof.get('collector_sources_before')==proof.get('collector_sources_after') and proof.get('collector_sources_before'),'Verifier source changed/unbound')
    require(files(root)==before,'Input differs from hash-bound source verification proof')
    for n in before:
        require(Path(n).suffix.lower() not in IMAGE_SUFFIXES,'Separate image file cannot enter package')
    # The reader requires positive raw replay/route/chronology proof, even when
    # source gaps intentionally caused a nonzero publication-completeness exit.
    return root
def binding(root,proof_bytes,family_bytes,mode):
    proof=json.loads(proof_bytes);family=json.loads(family_bytes)
    root=validate_input(root,proof,family)
    b={'schema_version':1,'reader':mode,'input_files':proof['evidence_sha256_before'],'read_only_proof_sha256':sha(proof_bytes),'family_verification_sha256':sha(family_bytes),'packager_code':code(),'publication_id':proof['publication_id']}
    return b,proof,family,reader(mode)(root,proof,family)
def input_artifacts(root,b,proof_bytes,family_bytes):
    result={}
    for n in b['input_files']:result['evidence/input/'+n]=safe(root,n).read_bytes()
    result['evidence/proofs/read-only-proof.json']=proof_bytes
    result['evidence/proofs/family-verification.json']=family_bytes
    for n in MODULES:result['packager-source/'+n]=(HERE/n).read_bytes()
    return result
def exact_artifacts(b,generated):
    result={'evidence/input/'+n:h for n,h in b['input_files'].items()}
    result.update({'evidence/proofs/read-only-proof.json':b['read_only_proof_sha256'],'evidence/proofs/family-verification.json':b['family_verification_sha256']})
    result.update({'packager-source/'+n:h for n,h in b['packager_code'].items()})
    result.update({n:sha(data) for n,data in generated.items()});return result
def validate_state(state):
    require(set(state)=={'schema_version','binding','phase','artifacts'} and state['schema_version']==1 and state['phase'] in ['copying','complete'] and isinstance(state['artifacts'],dict),'Unknown/corrupt package checkpoint schema or phase')
def manifest(state,outputs,projection):
    report=json.loads(outputs['validation-report.json'])
    return {'schema_version':1,'packager_version':VERSION,'reader':state['binding']['reader'],'publication_id':projection.publication_id,'jurisdiction':projection.metadata['jurisdiction'],'status':report['status'],'complete':report['complete'],'serialization_complete':True,'selected_publication_ready':report['selected_publication_ready'],'source_config':projection.metadata['source_config'],'source_version':projection.metadata['source_version'],'acquisition_interval':projection.metadata['acquisition_interval'],'artifact_hashes':dict(state['artifacts'],**{'package-state.json':sha(encoded(state))}),'record_count':len(projection.rows),'inventory_counts':{'source_nodes':len(projection.nodes),'dispositions':len(projection.dispositions)},'retry_failure_counts':{'packaging_network_retries':0,'source_errors':len(projection.inherited_coverage.get('errors',[]))},'configuration_sha256':sha(canonical(projection.metadata['source_config'])),'source_coverage_path':'inherited-coverage.json','source_verification_path':'evidence/proofs/read-only-proof.json','family_verification_path':'evidence/proofs/family-verification.json','binding':state['binding'],'paths':'All generated artifact references are relative; absolute strings inside original immutable evidence are historical provenance only','scope':'One selected publication; no all-jurisdiction or native segmentation qualification added'}

class InterruptedPackage(Exception):pass
def run(root,proof_path,family_path,out,mode,resume=False,interrupt_after=None):
    root=Path(root).resolve();out=Path(out).resolve()
    require(not out.is_relative_to(root) and not root.is_relative_to(out),'Input/output trees must be disjoint')
    require(interrupt_after is None or interrupt_after>0,'Interrupt boundary must be positive')
    proof_path=Path(proof_path).resolve();proof_bytes=proof_path.read_bytes();proof_meta=json.loads(proof_bytes)
    # Only an explicit relative JSON report path in the actual proof supplies a
    # default. Historical absolute log locations are never followed implicitly.
    if family_path is None:
        name=proof_meta.get('family_verification_path');require(isinstance(name,str) and name,'Explicit --family-verification or proof-relative family_verification_path required')
        family_path=safe(proof_path.parent,name)
    family_bytes=Path(family_path).read_bytes();json.loads(family_bytes)
    expected=proof_meta.get('family_verification_sha256') or proof_meta.get('verification',{}).get('family_report_sha256')
    require(expected is None or expected==sha(family_bytes),'Family report differs from proof hash')
    b,proof,family,p=binding(root,proof_bytes,family_bytes,mode);generated=artifacts(p)
    # Serialize writers for one destination without adding verifier lockfiles.
    lockpath=Path(tempfile.gettempdir())/('corpus-package-'+sha(str(out).encode())+'.lock')
    with lockpath.open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if out.exists() and any(out.iterdir()):
            require(resume and (out/'package-state.json').is_file(),'Fresh unpopulated output required')
            state=load(out/'package-state.json');validate_state(state);require(state['binding']==b,'Resume input/reader/publication/source/code mismatch')
            if state['phase']=='complete' and (out/'run-manifest.json').exists():return verify(out)
            for n,h in state['artifacts'].items():require(file_hash(safe(out,n))==h,'Corrupt committed packaging artifact')
        else:
            require(not resume,'Resume requires owned checkpoint')
            out.mkdir(parents=True,exist_ok=True);state={'schema_version':1,'binding':b,'phase':'copying','artifacts':{}}
            state_write(out/'package-state.json',state)
        evidence=input_artifacts(root,b,proof_bytes,family_bytes);all_expected={**evidence,**generated}
        require(set(state['artifacts'])<=set(all_expected),'Foreign committed artifact in package checkpoint')
        allowed=set(all_expected)|{'package-state.json','run-manifest.json'}
        require(set(files(out))<=allowed,'Unrelated output file; no overwrite/adoption')
        count=0
        for n,data in all_expected.items():
            expected=sha(data)
            if n in state['artifacts']:require(state['artifacts'][n]==expected,'Changed pending packaging projection');continue
            checked_write(safe(out,n),data);state['artifacts'][n]=expected;state_write(out/'package-state.json',state);count+=1
            if interrupt_after is not None and count>=interrupt_after:raise InterruptedPackage('Injected stop after durable package artifact')
        require(files(root)==b['input_files'],'Source changed during packaging')
        state['phase']='complete';state_write(out/'package-state.json',state)
        checked_write(out/'run-manifest.json',encoded(manifest(state,generated,p)))
        return verify(out)

def verify(out):
    """Read-only, source-independent package reconstruction; no writes or imports."""
    out=Path(out).resolve();m=load(out/'run-manifest.json');state=load(out/'package-state.json');validate_state(state);b=state['binding']
    require(state['phase']=='complete' and m['binding']==b and b['packager_code']==code(),'Incomplete or wrong-version packager state')
    expected=dict(m['artifact_hashes']);expected['run-manifest.json']=file_hash(out/'run-manifest.json')
    require(files(out)==expected,'Package missing/extra/corrupt artifact')
    for n,h in b['packager_code'].items():require(file_hash(safe(out,'packager-source/'+n))==h,'Packager snapshot corrupt')
    pb=(out/'evidence/proofs/read-only-proof.json').read_bytes();fb=(out/'evidence/proofs/family-verification.json').read_bytes()
    require(sha(pb)==b['read_only_proof_sha256'] and sha(fb)==b['family_verification_sha256'],'Wrong proof binding')
    root=out/'evidence/input';bb,proof,family,p=binding(root,pb,fb,b['reader']);require(bb==b,'Portable input binding differs')
    generated=artifacts(p)
    require(state['artifacts']==exact_artifacts(b,generated),'Package artifact inventory differs from exact source projection')
    for name,data in generated.items():require(safe(out,name).read_bytes()==data,'Corpus projection differs: '+name)
    require(m==manifest(state,generated,p),'Run manifest claim differs from source-bound projection')
    # Independent CSV parser checks every field, quoting, row order and TOC values.
    for folder,stem in [('', 'aggregate-fulltext'),('', 'aggregate-toc'),('publications/'+p.publication_id+'/', 'fulltext'),('publications/'+p.publication_id+'/', 'toc')]:
        raw=safe(out,folder+stem+'.csv').read_bytes();require(raw.startswith(b'\xef\xbb\xbf'),'Missing UTF8 BOM')
        csv.field_size_limit(64*1024*1024);r=csv.DictReader(io.StringIO(raw.decode('utf-8-sig'),newline=''))
        require(r.fieldnames==FIELDS,'CSV16-field order differs');rows=list(r);obj=load(safe(out,folder+stem+'.json'))
        require(list(obj)==['metadata','provisions'] and rows==obj['provisions'],'CSV/JSON row equality failed')
    result=json.loads(generated['validation-report.json']);return dict(result,package_verified=True,read_only=True,network_requests=0,source_reparsed=False)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    r=sub.add_parser('package');r.add_argument('--input',required=True);r.add_argument('--proof',required=True);r.add_argument('--family-verification');r.add_argument('--reader',choices=list(READERS),required=True);r.add_argument('--out',required=True);r.add_argument('--resume',action='store_true');r.add_argument('--interrupt-after',type=int)
    v=sub.add_parser('verify');v.add_argument('--out',required=True)
    a=parser.parse_args(argv)
    try:
        result=verify(a.out) if a.action=='verify' else run(a.input,a.proof,a.family_verification,a.out,a.reader,a.resume,a.interrupt_after)
        print(json.dumps(result,indent=2));return 0 if result['complete'] else 2
    except InterruptedPackage as e:print(json.dumps({'interrupted':True,'error':str(e)}));return 75
    except Exception as e:print(json.dumps({'package_verified':False,'complete':False,'error':type(e).__name__+': '+str(e)}));return 1
if __name__=='__main__':sys.exit(main())
