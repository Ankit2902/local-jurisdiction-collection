"""Deterministic documentary source bundle; no native PDFs/pixels or network."""
from pathlib import Path
import hashlib,json,zipfile
P=Path(__file__).resolve().parent;R=Path(json.loads((P/'source-binding.json').read_text())['repository']);F=R/'packages/collection-source-recovery-2026-10-18/clark/full30';Q=R/'packages/collection-source-recovery-2026-10-18/clark/peer';dest=P/'candidate/collectors/registry'
def read(p):return json.loads(p.read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
cp=read(F/'run/checkpoint.json');names=['config.json','run/config.json','source-inventory.json','run/checkpoint.json','run/coverage.json','verify.stdout','status.json','source-binding.json','verification-source-binding.json','verify_guarded.py','run.py','run/'+cp['identity']['source_ref'],'run/'+cp['consistency']['raw_ref']]
names += ['run/executed/'+n for n in cp['scripts']]
names += [str(p.relative_to(F))for p in(F/'run/raw').glob('*.receipt.json')]
contents={'full30/'+n:(F/n).read_bytes()for n in sorted(set(names))};contents['full30/MANIFEST.json']=(F/'MANIFEST.json').read_bytes();contents['peer/review.json']=(Q/'review.json').read_bytes()
z=dest/'clark-title30-source-evidence.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=9)as archive:
 for n,b in sorted(contents.items()):
  info=zipfile.ZipInfo(n,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,b)
m={'schema_version':1,'archive_sha256':sha(z.read_bytes()),'source_full_manifest_sha256':sha((F/'MANIFEST.json').read_bytes()),'source_peer_review_sha256':sha((Q/'review.json').read_bytes()),'scope':'Documentary selector/identity/initial-closing receipts and original verified file-page qualification only; no nativePDFbinaries copied, no new common/native verification.','files':[{'member':n,'bytes':len(b),'sha256':sha(b)}for n,b in sorted(contents.items())]}
(dest/'clark-title30-source-evidence-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
q=dest/'followup-qualified-configs.json';v=read(q);entry=v['publications']['96-7e8795b1baee'];entry.pop('validation_level',None);e=entry['qualification_evidence'];e.update(bundle='clark-title30-source-evidence.zip',source_manifest='clark-title30-source-evidence-manifest.json',source_archive_sha256=m['archive_sha256']);q.write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps({'archive_sha256':m['archive_sha256'],'members':len(contents),'bytes':z.stat().st_size},indent=2))
