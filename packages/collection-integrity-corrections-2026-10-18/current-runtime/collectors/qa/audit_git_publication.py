"""Read-only archive/commit/normalized reconciliation, independent of adapters."""
import argparse,hashlib,json,collections
from pathlib import Path
from git_archive_binding import inspect_archive,root_tree,object_id

def sha(b):return hashlib.sha256(b).hexdigest()
def audit(run):
 cp=json.loads((run/'checkpoint.json').read_text());cfg=json.loads((run/'config.json').read_text());inv=json.loads((run/'inventory.json').read_text());errors=[];sources=[]
 def raw(ref):
  p=run/ref;b=p.read_bytes();r=json.loads(p.with_suffix('.receipt.json').read_text())
  if r.get('status')!=200 or r.get('sha256')!=sha(b) or r.get('raw_ref')!=ref:raise ValueError('Raw receipt binding failure '+ref)
  sources.append({'path':ref,'sha256':sha(b),'url':r['url']});return b,r
 identity=cp['identity'];commit_b,cr=raw(identity['commit_ref']);commit=json.loads(commit_b)
 expected_commit=identity['commit'];repo=identity['repository'];expected_tree=commit['commit']['tree']['sha']
 assert commit['sha']==expected_commit and commit['url']==f'https://api.github.com/repos/{repo}/commits/{expected_commit}'
 item=inv[0];assert len(inv)==1 and item['url']==identity['archive_url']==f'https://api.github.com/repos/{repo}/zipball/{expected_commit}'
 _,zr=raw(item['raw_ref']);assert zr['url']==item['url']
 result=inspect_archive(run/item['raw_ref']);members={m['path']:m for m in result['members']}
 if result['git_root_tree_sha1']!=expected_tree:errors.append('archive Git root differs from independently retained commit tree')
 coverage=json.loads((run/'coverage.json').read_text());records=[json.loads(s) for s in (run/'records.jsonl').read_text().splitlines() if s];recordmap={r['id']:r for r in records};disps=coverage['dispositions'];prefix=cfg['archive_prefix'].strip('/')
 canonical={m['path'] for m in result['members'] if m['relative_path'].startswith(prefix+'/') and m['relative_path'].endswith('/index.html')}
 if len(recordmap)!=len(records):errors.append('duplicate record IDs')
 if len({d['member'] for d in disps})!=len(disps) or {d['member'] for d in disps}!=canonical:errors.append('canonical archive/disposition set differs')
 for d in disps:
  if d.get('record_id') and d.get('member_sha256')!=members[d['member']]['sha256']:errors.append('disposition member hash '+d['id'])
  if d.get('record_id'):
   r=recordmap.get(d['record_id'])
   if not r or r['raw_ref']!=item['raw_ref']+'!'+d['member'] or r['raw_sha256']!=members[d['member']]['sha256']:errors.append('record raw binding '+d['id'])
 # Adversarial reconciliation against the actual full source inventory: a valid
 # rebuilt archive/rehashed receipt cannot restore the retained commit root.
 files=[(m['relative_path'],m['git_mode'],bytes.fromhex(m['git_blob_sha1'])) for m in result['members']]
 middle=sorted(canonical)[len(canonical)//2];chosen=members[middle];relative=chosen['relative_path']
 removed=root_tree([f for f in files if f[0]!=relative]);changed=root_tree([(p,mode,object_id('blob',b'changed legal body')) if p==relative else (p,mode,oid) for p,mode,oid in files])
 faults={'middle_canonical_member_removed':{'member':middle,'recomputed_git_root':removed,'rejected':removed!=expected_tree},'middle_canonical_member_changed_and_rehashed':{'member':middle,'recomputed_git_root':changed,'rejected':changed!=expected_tree}}
 if not all(v['rejected'] for v in faults.values()):errors.append('independent root accepted adverse inventory')
 return {'schema_version':1,'kind':'independent-commit-tree-and-publication-source-binding','script_sha256':sha(Path(__file__).read_bytes()),'helper_sha256':sha(Path(__file__).with_name('git_archive_binding.py').read_bytes()),'sources':sources,'commit':expected_commit,'expected_git_tree':expected_tree,'reconstructed_git_tree':result['git_root_tree_sha1'],'archive_files':result['file_count'],'archive_directories':result['directory_entries'],'zip_crc_all_members_valid':result['zip_crc_all_members_valid'],'canonical_source_pages':len(canonical),'normalized_records':len(records),'disposition_counts':dict(collections.Counter(d['disposition'] for d in disps)),'record_units':dict(collections.Counter(r['unit'] for r in records)),'records_sha256':sha((run/'records.jsonl').read_bytes()),'coverage_sha256':sha((run/'coverage.json').read_bytes()),'fault_checks':faults,'network_requests':0,'image_decoding_or_member_file_extraction':False,'legal_semantic_coverage_complete':coverage['legal_semantic_coverage_complete'],'passed':not errors,'errors':errors}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('run',type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
 if a.out.exists() or a.run.resolve() in a.out.resolve().parents:raise SystemExit('fresh report outside evidence required')
 report=audit(a.run);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 2)
