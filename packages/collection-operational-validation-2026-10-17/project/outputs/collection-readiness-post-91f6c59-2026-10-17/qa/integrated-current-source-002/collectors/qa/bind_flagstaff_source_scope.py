"""Bind finite independent Flagstaff source dimensions to actual common verify.

Only proves the tested dimensions. It cannot manufacture workflow, resume,
legal-structure, edition or jurisdiction acceptance from an audit summary.
"""
import argparse,hashlib,json
from pathlib import Path
from readiness_binding import canonical,current_components,selected_configuration,gate_qa_sources
ROOT=Path(__file__).resolve().parents[2];PROJECT=ROOT.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(proof_path,audits,out):
 if out.exists():raise ValueError('Fresh report required')
 proof=json.loads(proof_path.read_text());assert proof['publication_id']=='original-flagstaff-az-primary' and proof['source_url']=='https://www.codepublishing.com/AZ/Flagstaff/'
 def file(path,digest):
  p=(PROJECT/path).resolve()
  if not p.is_relative_to(PROJECT.resolve()) or not p.is_file() or sha(p)!=digest:raise ValueError('Missing/changed bound file '+path)
  return p
 manifest=json.loads(file(proof['artifact_manifest'],proof['artifact_manifest_sha256']).read_text());receipt=json.loads(file(proof['verification_receipt'],proof['verification_receipt_sha256']).read_text());file(proof['runtime_receipt'],proof['runtime_receipt_sha256'])
 assert receipt['publication_accepted'] is True and receipt['read_only'] is True
 for key in ('publication_id','source_url','config_sha256','component_sources','artifact_manifest_sha256','runtime_receipt_sha256'):
  assert receipt[key]==proof[key], 'Actual verification receipt/tuple mismatch: '+key
 import sys
 sys.path.insert(0,str(ROOT/'collectors/registry'));from catalog import load_catalog
 from dispatch import command
 catalog=load_catalog();pub=next(p for p in catalog['publications'] if p['id']==proof['publication_id']);target=next(t for t in catalog['targets'] if t['id']==pub['target_id']);sources=current_components(ROOT,pub)
 assert sources==proof['component_sources']==receipt['source_before']==receipt['source_after']
 assert proof['config_sha256']==selected_configuration(ROOT,pub,target,command(pub,target,'{OUT}'))['sha256']==receipt['config_sha256']
 scope={k:proof[k] for k in ('publication_id','source_url','config_sha256','component_sources','artifact_manifest_sha256','verification_receipt_sha256','runtime_receipt_sha256')};assert canonical(scope)==proof['scope_id']
 available=set()
 for item in manifest['files']:file(item['path'],item['sha256']);available.add(item['sha256'])
 names=['flagstaff-full-source-qualified-v3.json','flagstaff-independent-inventory-v3.json'];evidence=[];reports=[]
 for name in names:
  p=audits/name;r=json.loads(p.read_text());assert r['passed'];reports.append(r);evidence.append({'path':str(p.relative_to(PROJECT)),'sha256':sha(p)})
 body,inventory=reports;assert body['records_sha256']==inventory['records_sha256'];assert body['source_checkpoint_sha256']==inventory['source_checkpoint_sha256'];assert body['source_documents']==inventory['source_documents']==361 and body['records']==inventory['normalized_records']==2661
 assert body['tables']==377 and body['cells']==27167 and inventory['source_edges_per_phase']==2658 and inventory['mapped_edges']==2658
 assert body['records_sha256'] in available and body['source_checkpoint_sha256'] in available
 assert all(r['sha256'] in available for r in inventory['source_raw_receipts'])
 assert len(body['exact_heading_image_dispositions'])==14 and not body['errors'] and not inventory['errors']
 reasons={'identity':'Exact current common config/government/state/publication binding plus source-root/label/currency witnesses, all bound to current artifact manifest.','full_inventory':'Independent retained native18root/2658edge reconstruction;361source documents,2661records, every source edge exactlyone output owner.','owned_text':'Independent all361source documents/24237atomic blocks/2661records agree with original body text, source heading labels and14exact ordered image-heading dispositions.','table_fidelity':'Independent inert original DOM377tables/7558rows/27167cells text/tag/rowspan/colspan agreement.','closing_consistency':'Exact retained opening/closing root/readers/currency and acquisition chronology. This is not fresh reacquisition of every body.'}
 image_evidence=[]
 for key in ('normalized_image_audit','acquired_bytes_image_audit','image_transport_regression'):
  item=proof.get(key)
  if not item:break
  path=file(item['path'],item['sha256']);r=json.loads(path.read_text());assert r['passed'] and r['proof_scope_id']==proof['scope_id'] and r['component_sources']==sources and r['executed_qa_sources']==gate_qa_sources(ROOT,pub,key)
  assert r['artifact_manifest_sha256']==proof['artifact_manifest_sha256'];image_evidence.append(item)
 if len(image_evidence)==3:
  reasons['image_policy']='Actual current479file source/run normalized-stream and binary/MIME audits pass, current originals no-image transport/Word-media/HTML-cell tests pass under network tripwire; exact current source tuple and artifact manifest unchanged. Exact IMAGE omissions are intentional policy.'
 requirements={k:{'status':'pass','proof_scope_id':proof['scope_id'],'reason':v,'evidence':image_evidence if k=='image_policy' else evidence} for k,v in reasons.items()}
 report={'passed':True,'publication_id':proof['publication_id'],'scope_id':proof['scope_id'],'active_proof_path':str(proof_path.relative_to(PROJECT)),'active_proof_sha256':sha(proof_path),'requirements':requirements,'records_sha256':body['records_sha256'],'source_checkpoint_sha256':body['source_checkpoint_sha256'],'component_sources':sources,'script_sha256':sha(Path(__file__)),'network_requests_sent':0,'source_acquisition_mode':'retained_source_replay','requirements_not_granted':[k for k in ['required_nonimage_documents','image_policy','resume_integrity','fresh_setup_cli','legal_structure'] if k not in reasons],'jurisdiction_complete':False,'limits':'Only exact tested source dimensions receive current tuple binding. Remaining independent dimensions and complete-readiness acceptance are not inferred. Separate Employee Handbook scope remains unresolved.'};out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--proof',type=Path,required=True);p.add_argument('--audits',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=bind(a.proof,a.audits,a.out);print(json.dumps({'passed':r['passed'],'scope_id':r['scope_id'],'requirements':list(r['requirements'])}))
