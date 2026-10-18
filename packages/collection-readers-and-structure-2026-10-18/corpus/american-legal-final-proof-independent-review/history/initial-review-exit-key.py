"""Independent actual proof byte/hash/guard inspection; no verifier/native parse."""
import sys
sys.dont_write_bytecode=True
import ast,hashlib,importlib.metadata,json,platform,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
ACTUAL=HERE.parent/'cleveland-final-common-proof-v1'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(p.read_text())
def snapshot(root):
 result={}
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink()
  if p.is_file():result[p.relative_to(root).as_posix()]=sha(p)
 return result
def main():
 before=snapshot(ACTUAL);command=load(ACTUAL/'command.json');stdout=load(ACTUAL/'cli.stdout');exit=load(ACTUAL/'exit.json');p=load(ACTUAL/'proof/read-only-proof.json');f=load(ACTUAL/'proof/family-verification.json')
 assert exit.get('returncode',exit.get('exit'))==0,exit
 assert stdout['verification_adapter_complete'] is True and stdout['publication_acceptance_added'] is False and stdout['forbidden_calls']==[]
 assert p['schema']=='offline-family-readonly-proof-1' and p['family']=='american-legal' and p['reader']=='american-legal-native-html-publication-v1'
 assert p['publication_id']=='59-primary' and p['registry_mapping_verified'] is False
 assert p['publication_id_origin'].startswith('Caller-assigned')
 assert p['family_verification_path']=='family-verification.json'
 v=p['verification'];assert v['family_report_sha256']==sha(ACTUAL/'proof/family-verification.json')
 assert v['forbidden_calls']==[] and v['runtime_before']==v['runtime_after']
 inp=Path(command[command.index('--input')+1]);collector=Path(command[command.index('--collector-root')+1]);family=collector/'collectors/american-legal';helper=Path(command[2])
 assert command==[str(collector/'.collection-runtime/venv/bin/python'),'-B',str(helper),'--reader',p['reader'],'--input',str(inp),'--collector-root',str(collector),'--publication-id',p['publication_id'],'--out',str(ACTUAL/'proof')]
 assert sha(helper)==v['adapter_source_sha256'] and str(family)==v['captured_runtime_root']
 assert v['module_file']==str(family/'verify.py') and sha(family/'verify.py')==v['module_sha256']
 assert len(p['evidence_sha256_before'])==988 and p['evidence_sha256_before']==p['evidence_sha256_after']==snapshot(inp)
 assert len(p['collector_sources_before'])==66 and p['collector_sources_before']==p['collector_sources_after']==snapshot(family)
 assert p['evidence_read_only'] is True and p['publisher_requests']==0 and p['source_changed_during_run'] is False and p['runtime_changed_during_run'] is False
 rt=v['runtime_before'];assert sha(Path(rt['python_executable']))==rt['python_executable_sha256']
 current={'python_executable':str(Path(sys.executable).resolve()),'python_executable_sha256':sha(Path(sys.executable).resolve()),'python_version':sys.version,'implementation':platform.python_implementation(),'packages':dict(sorted((d.metadata['Name'],d.version) for d in importlib.metadata.distributions() if d.metadata.get('Name')))}
 assert current==rt
 run=load(inp/'run.json');assert p['selected_config']=={'source_url':run['source_url'],'publication_selector':run['publication_selector']}
 assert run['status']=='acquired' and run['strategy']=='native' and run['max_items'] is None and run['identity']['is_pdf'] is False
 assert f['publication_identity']==run['identity'] and f==load(inp/'coverage.json')
 assert f['inventory_count']==f['acquired_count']==f['unique_id_count']==6140
 assert f['owned_source_block_count']==43676 and f['independently_recomputed_branch_count']==459
 assert f['table_count']==322 and f['table_cell_count']==7738
 assert f['publication_complete'] is True and f['jurisdiction_complete'] is False
 assert f['native_publication_files_complete'] is False and f['pdf_legal_provision_segmentation_qualified'] is False
 assert f['required_asset_count']==f['retained_asset_count']==5 and f['attachment_complete'] is True
 assert f['pdf_normalized_distinct_document_count']==f['pdf_text_layer_pages_parsed']==5
 assert f['pdf_semantic_text_completeness_qualified'] is True and f['pdf_table_completeness_qualified'] is True
 assert f['image_binary_download_count']==0 and f['image_policy']=='literal-[IMAGE]-no-image-fetch-v1'
 assert f['image_reference_placeholder_count']==15 and f['image_marker_count']==33
 text=helper.read_text();tree=ast.parse(text);mainfn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 assert text.index('with contextlib.ExitStack() as guard:')<text.index("module=importlib.import_module('verify')")<text.index('result=module.verify(root)')
 markers=["(socket,['create_connection'])","(socket.socket,['connect'])","(Image,['open'])","(pypdfium2.PdfPage,['render','get_objects'])","(pypdfium2.PdfImage,['extract','get_bitmap','get_data'])","(pdfplumber.page.Page,['to_image'])","patch.object(PageObject,'images'","patch.object(PDFStream,'get_data',guarded_stream)","(fitz.Document,['extract_image'])","(fitz.Page,['get_pixmap','get_svg_image'])"]
 assert all(x in text for x in markers)
 assert "if str(resolve1(stream.attrs.get('Subtype'))) in [\"/'Image'\",'Image','/Image']:return no()" in text
 assert 'calls.append' in text and 'or calls:raise ValueError' in text
 assert snapshot(ACTUAL)==before and snapshot(inp)==p['evidence_sha256_before'] and snapshot(family)==p['collector_sources_before']
 for name in ['command.json','exit.json','cli.stdout','cli.stderr','proof/family-verification.json']:
  dest=HERE/'captured'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ACTUAL/name,dest)
 # Keep the full proof map once as exact bytes, not duplicated before/after trees.
 shutil.copy2(ACTUAL/'proof/read-only-proof.json',HERE/'captured/proof/read-only-proof.json')
 report={'schema':'independent-current-cleveland-offline-proof-review-1','passed':True,'actual_verifier_rerun':False,'production_or_actual_proof_modified':False,'proof_kind':'Actual standard AL family verify() through portable verify_input; not a collect.py common-launcher acceptance receipt','exit':0,'helper_sha256':sha(helper),'standard_family_verifier_sha256':sha(family/'verify.py'),'family_report_sha256':sha(ACTUAL/'proof/family-verification.json'),'exact_coverage_bytes_hash':sha(inp/'coverage.json'),'report_equals_stored_coverage':True,'input_files':988,'current_family_files':66,'independent_rehash_before_after_equal':True,'python_binary_packages_unchanged_and_current':True,'python_packages':len(rt['packages']),'publication_namespace':'caller-assigned59-primary; registry mapping explicitly unverified','guard_evidence':{'zero_forbidden_calls_reported':True,'current_helper_guard_source_bound':True,'source_hash':sha(helper),'guard_api_markers':markers,'guard_installed_before_selected_collector_import':True,'no_separate_guard_loaded_event_log_in_this_adapter':'In-process guarded standard family invocation, not the Flagstaff subprocess sitecustomize protocol.'},'family_dimensions':{k:f[k] for k in ['inventory_count','owned_source_block_count','independently_recomputed_branch_count','table_count','table_cell_count','required_asset_count','retained_asset_count','pdf_text_layer_pages_parsed','publication_complete','jurisdiction_complete','native_publication_files_complete','pdf_legal_provision_segmentation_qualified','pdf_semantic_text_completeness_qualified','pdf_table_completeness_qualified','image_binary_download_count','image_marker_count','limitations']},'actual_files_sha256':before,'scope_limits':['Existing native HTML source and five one-page attachments reverified by the actual helper; this peer rechecks proof/maps only, no parser/native rerun.','publication_complete is this selected AL family result, not new common registry acceptance, whole-jurisdiction coverage or PDF legal-provision segmentation.','No source acquisition or scope upgrade; exact original limitations remain.'],'peer_publisher_requests':0,'peer_image_download_decode_render_extract_ocr_operations':0}
 (HERE/'review.json').write_text(json.dumps(report,indent=2)+'\n')
 m={p.relative_to(HERE).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='MANIFEST.json'}
 (HERE/'MANIFEST.json').write_text(json.dumps({'files':m},indent=2)+'\n');print(json.dumps({'passed':True,'review_sha256':sha(HERE/'review.json'),'manifest_sha256':sha(HERE/'MANIFEST.json'),'files':len(m)}))
if __name__=='__main__':main()
