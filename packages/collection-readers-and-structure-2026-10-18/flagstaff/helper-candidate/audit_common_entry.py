"""Source-only current common verify path/binding review; no family replay/import."""
import sys
sys.dont_write_bytecode=True
import argparse,ast,hashlib,importlib.util,json
from pathlib import Path

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--collector-root',type=Path,required=True);p.add_argument('--helper',type=Path,required=True);p.add_argument('--existing-receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 root=a.collector_root.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 sp=importlib.util.spec_from_file_location('reviewed_helper',a.helper);h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)
 before=h.collector_files(root)
 path=root/'collectors/ops/launcher.py';tree=ast.parse(path.read_text());binding=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='code_binding')
 ns={'ROOT':root,'HERE':path.parent,'FAMILIES':(),'sha':digest}
 exec(compile(ast.Module(body=[binding],type_ignores=[]),str(path),'exec'),ns)
 assert before==ns['code_binding']('originals')
 names=['collect.py','collectors/ops/launcher.py','collectors/registry/collect.py','collectors/registry/dispatch.py','collectors/originals/cli.py','collectors/originals/verify.py','collectors/originals/flagstaff_html_normalize.py','collectors/originals/model.py','collectors/originals/publication_source_verify.py']
 excerpts={};scopes=[]
 for name in names:
  source=(root/name).read_text();t=ast.parse(source)
  wanted={'collectors/ops/launcher.py':['execute_job','runtime_env','doctor','code_binding'], 'collectors/registry/collect.py':['main'], 'collectors/registry/dispatch.py':['command'], 'collectors/originals/cli.py':['verify'], 'collectors/originals/verify.py':['verify']}.get(name)
  if wanted:
   funcs=[n for n in t.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in wanted]
   snippet='\n\n'.join(ast.get_source_segment(source,n) for n in funcs)
   scopes.extend({'path':name,'function':n.name,'first_line':n.lineno,'last_line':n.end_lineno,'sha256':digest(root/name)} for n in funcs)
  else:snippet=source
  safe=name.replace('/','__')+'.txt';(out/safe).write_text(snippet)
  excerpts[name]={'path':safe,'source_sha256':digest(root/name),'review_excerpt_sha256':digest(out/safe)}
 launcher=(root/'collectors/ops/launcher.py').read_text();start=launcher.index('    if verify_only:',launcher.index('def execute_job'))
 end=launcher.index('\n    if out == ROOT',start);branch=launcher[start:end]
 assert 'health = doctor(runtime)' in branch and 'browser=True' not in branch
 assert "'verify', '--target'" in branch and 'runtime_env' not in branch
 assert 'sources_before = code_binding' in branch and 'evidence_before = evidence_hashes' in branch
 assert "coverage(cfg.binding(),root,html,word,write=False)" in (root/'collectors/originals/cli.py').read_text()
 assert "with tempfile.TemporaryDirectory" in (root/'collectors/originals/verify.py').read_text()
 receipt=json.loads(a.existing_receipt.read_text());same=receipt['collector_sources_before']==receipt['collector_sources_after']==before
 assert receipt['evidence_read_only'] is True and receipt['publisher_requests']==0
 assert before==h.collector_files(root)
 report={'source_review_complete':True,'actual_family_or_common_verifier_executed':False,'current_originals_common_binding_parity':True,'bound_files':len(before),'source_sha256_before':before,'source_sha256_after':h.collector_files(root),'helper_sha256':digest(a.helper),'existing_receipt':{'path':str(a.existing_receipt.resolve()),'sha256':digest(a.existing_receipt),'source_binding_matches_current':same,'status':receipt['status'],'family_verifier_passed':receipt['family_verifier_passed'],'acceptance_preserved_for_context_only':receipt['acceptance']},'entry_path_scopes':scopes,'excerpts':excerpts,'review_findings':['Root collect.py disables bytecode before importing ops launcher.','Common verify uses default browser=False runtime doctor; its registry command is explicitly verify. Its logs are written under owned runtime/verifications, not evidence.','Originals cli.verify validates exact executed config/revision/acquisition mode and recomputes coverage(write=False).','Originals verify regenerates normalized text/HTML in a temporary directory and compares exact canonical artifacts; it does not invoke acquisition, transport, browser, image extraction/render/OCR.','The helper copies exact actual common JSON and exact JSON family log without replacing acceptance fields or relabelling source acquisition.','Runtime installation integrity is checked by actual common doctor; the helper independently checks runtime.json stability and complete collector/config maps.'],'limits':['This is source-path/binding inspection plus prior actual receipt context, not a new full common or family verification.','Controlled CLI tests prove orchestration/refusals only. No current real Flagstaff helper run has yet occurred.','No claim of all transitively imported code security against a hostile collector-root or runtime; these are explicitly chosen trusted implementations.'],'publisher_requests':0,'separate_image_downloads':0,'image_decode_render_extract_ocr_operations':0}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'passed':True,'bound_files':len(before),'old_receipt_current_binding':same,'report_sha256':digest(out/'report.json')}))
if __name__=='__main__':main()
