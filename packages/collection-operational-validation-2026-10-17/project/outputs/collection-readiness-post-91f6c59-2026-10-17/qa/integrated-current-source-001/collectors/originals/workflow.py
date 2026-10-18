"""Operational collection-root reconciliation and explicit, network-free retained-source replay."""
import json,shutil
from pathlib import Path
from source_common import load,save,sha,stamp
ROOT=Path(__file__).resolve().parent

def runtime_binding():
 return {p.name:sha(p.read_bytes()) for p in ROOT.iterdir() if p.is_file() and (p.suffix=='.py' or p.name in ['configs.json','source_dispositions.json','source_character_dispositions.json','requirements.txt'])}

def checkpoint(cfg,out,mode,origin=None):
 data={'schema':'originals-collection-checkpoint-1','publisher':'official','adapter_family':'originals','target_id':cfg['target_id'],'config':cfg,'source_identity':{k:cfg[k] for k in ['target_id','jurisdiction','state','source_url','profile','publication','required_formats']},'acquisition_mode':mode,'started_at':stamp(),'stage':'started','complete':False,'code_fingerprint':runtime_binding(),'origin':origin,'errors':[]}
 save(Path(out)/'checkpoint.json',data);return data

def coverage(cfg,out,html=None,word=None,write=True):
 out=Path(out);flag=cfg['profile']=='flagstaff_html';html=html if html is not None else load(out/'normalized/summary.json');word=None if flag else word if word is not None else load(out/'native-normalized/summary.json')
 formats={'html':{'normalized':'normalized','summary':html}}
 if word:formats['word']={'normalized':'native-normalized','summary':word}
 body_html=bool(html.get('publication_body_complete')) if not flag else bool(html.get('source_documents')==html.get('acquired_parsed_documents') and html.get('source_blocks')==html.get('owned_blocks') and html.get('source_tables')==html.get('owned_tables') and html.get('source_graph_edges')==html.get('matched_toc_edges') and html.get('missing_toc_edges')==0 and html.get('extra_body_headings')==0 and html.get('heading_only_unresolved')==0)
 bodies=body_html and (not word or word.get('publication_body_complete') is True)
 text=bool(bodies and html.get('character_semantics_complete',True) and (not word or word.get('character_semantics_complete')))
 attachments=html.get('attachments_complete',html.get('unresolved_nonimage_dependencies')==0) and (not word or word.get('attachments_complete') is True)
 consistency=bool(html.get('opening_closing_inventory_equal') and (html.get('opening_closing_roots_equal') and html.get('opening_currency') and html.get('opening_currency')==html.get('closing_currency') if flag else html.get('publication_update_labels_consistent') and html.get('source_navigation_complete')) and (not word or word.get('edition_complete') is True))
 structure=bool(bodies and html.get('source_tables')==html.get('owned_tables'))
 accepted=bool(text and attachments and consistency and structure and html.get('complete') and (not word or word.get('complete')))
 result={'schema':'originals-coverage-1','publisher':'official','adapter_family':'originals','target_id':cfg['target_id'],'config':cfg,'required_formats':cfg['required_formats'],'publication_text_complete':text,'publication_bodies_acquired_and_owned':bool(bodies),'attachments_complete':bool(attachments),'legal_structure_qualified':structure,'legal_structure_qualification_scope':'Profiled source ownership, heading/navigation and table conservation gates; independent final source-DOM/Word audits are tracked separately and not inferred from this field','source_consistency_complete':consistency,'publication_accepted':accepted,'complete':accepted,'whole_jurisdiction_complete':False,'external_adopted_legal_dependency_closure_complete':False,'independent_final_review_complete':False,'independent_review_note':'Prior exact source-DOM/XML conservation reports retained; final Flagstaff and latest King deltas need their own independent promotion record','image_policy':'No separate image body/member acquisition; exact[IMAGE] in source order; native original document may intrinsically contain images','formats':formats,'errors':html.get('errors',[])+(word.get('errors',[]) if word else [])}
 if write:
  save(out/'coverage.json',result);state=load(out/'checkpoint.json');state.update(stage='normalized',complete=accepted,finished_at=stamp(),errors=result['errors']);save(out/'checkpoint.json',state)
 return result

def _normalize_stage(cfg,format,source,out):
 from cli import normalize
 from verify import verify
 dest=out/('normalized' if format=='html' else 'native-normalized')
 if dest.exists():return verify(cfg.family(format),source,dest)
 attempts=sorted(out.glob('.normalization-attempt-'+format+'-*'));attempt=out/('.normalization-attempt-'+format+'-'+str(len(attempts)+1).zfill(4))
 # Interrupted attempts remain immutable. A new temporary generation is published only on terminal parse.
 result=normalize(cfg,format,source,attempt);attempt.rename(dest);return result

def replay(cfg,source,out,native_source=None,resume=False):
 from publication_source_verify import validate
 source=Path(source).resolve();out=Path(out).resolve();flag=cfg.profile.value=='flagstaff_html'
 if flag and native_source:raise ValueError('Flagstaff has no qualified Word source format')
 if not flag and not native_source:raise ValueError('King replay requires --native-source for all required source formats')
 native_source=Path(native_source).resolve() if native_source else None
 validate(cfg.family('html'),source)
 if native_source:validate(cfg.family('word'),native_source)
 origin={'html_checkpoint_sha256':sha((source/'checkpoint.json').read_bytes()),'word_checkpoint_sha256':sha((native_source/'checkpoint.json').read_bytes()) if native_source else None}
 if resume:
  state=load(out/'checkpoint.json');marker=load(out/'collection-start.json')
  if state.get('acquisition_mode')!='retained_source_replay' or state.get('config')!=cfg.binding() or state.get('origin')!=origin or state.get('code_fingerprint')!=runtime_binding() or marker.get('publication_config')!=cfg.binding():raise ValueError('Replay source/configuration/revision drift; use an explicit new output')
 else:
  if out.exists() and any(out.iterdir()):raise ValueError('Replay requires a fresh empty output unless explicit --resume')
  out.mkdir(parents=True,exist_ok=True);checkpoint(cfg.binding(),out,'retained_source_replay',origin);save(out/'collection-start.json',{'target':cfg.id,'publication_config':cfg.binding(),'code_fingerprint':runtime_binding(),'started_at':stamp(),'acquisition_mode':'retained_source_replay'})
  from source_common import source_snapshot
  source_snapshot(out,list(runtime_binding()))
 for format,original,subdir in [('html',source,'source' if flag else 'html-source')]+([] if flag else [('word',native_source,'native-source')]):
  dest=out/subdir
  if not dest.exists():
   attempt=out/('.source-copy-'+format)
   if attempt.exists():raise ValueError('Interrupted source-copy staging requires operator review; original retained source has not been changed')
   shutil.copytree(original,attempt);validate(cfg.family(format),attempt);attempt.rename(dest)
  validate(cfg.family(format),dest)
  if sha((dest/'checkpoint.json').read_bytes())!=origin[format+'_checkpoint_sha256']:raise ValueError('Retained source checkpoint drift during replay')
  _normalize_stage(cfg,format,dest,out)
 result=coverage(cfg.binding(),out)
 result.update(acquisition_mode='retained_source_replay',fresh_acquisition=False,publisher_requests=0)
 save(out/'collection-result.json',result)
 # Same operational verifier used by common verify, not a separate success path.
 from cli import verify
 proof=verify(cfg,out=out);save(out/'replay-verification.json',proof)
 return dict(result,full_raw_replay_equal=proof.get('full_raw_replay_equal'),input_files_modified=False)

def incomplete_coverage(cfg,out,errors):
 """A terminal acquisition failure cannot inherit any normalized coverage success."""
 root=Path(out);result={'schema':'originals-coverage-1','publisher':'official','adapter_family':'originals','target_id':cfg['target_id'],'config':cfg,'required_formats':cfg['required_formats'],'publication_text_complete':False,'publication_bodies_acquired_and_owned':False,'attachments_complete':False,'legal_structure_qualified':False,'source_consistency_complete':False,'publication_accepted':False,'complete':False,'whole_jurisdiction_complete':False,'external_adopted_legal_dependency_closure_complete':False,'independent_final_review_complete':False,'formats':{},'errors':errors}
 save(root/'coverage.json',result);state=load(root/'checkpoint.json');state.update(stage='acquisition_incomplete',complete=False,errors=errors);save(root/'checkpoint.json',state);return result
