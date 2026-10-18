"""Actual retained excluded-node negative, rehashed adversarial input not a new family proof."""
import copy,json,pathlib,shutil,sys,tempfile
P=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(P/'candidate'));import common,municode_html
source=P/'packages/henderson/evidence/input';proof=common.load(P/'henderson-proof/read-only-proof.json');family=common.load(P/'henderson-proof/family-verification.json');report=[]
with tempfile.TemporaryDirectory()as d:
 root=pathlib.Path(d)/'input';shutil.copytree(source,root);cp=common.load(root/'checkpoint.json');pid=next(iter(cp['publications']));coverage=common.load(root/'publications'/pid/'coverage.json');ex=coverage['justified_exclusions'][0];u=cp['units'][ex['evidence_unit']];rp=root/u['receipt'];receipt=common.load(rp);body=root/receipt['body_file'];original=body.read_bytes()
 for field in ['Notes','Footnotes']:
  raw=json.loads(original);ds=raw if isinstance(raw,list)else raw['Docs'];target=next(x for x in ds if str(x['Id'])==str(ex['id']));target[field]='MANDATORY EXCLUDED LEGAL NOTE';body.write_bytes(common.encoded(raw));sha=common.file_hash(body);u['sha256']=receipt['sha256']=sha;rp.write_bytes(common.encoded(receipt));(root/'checkpoint.json').write_bytes(common.encoded(cp));attacked=copy.deepcopy(proof);attacked['evidence_sha256_before']=common.files(root);attacked['evidence_sha256_after']=copy.deepcopy(attacked['evidence_sha256_before'])
  try:
   p=municode_html.read_projection(root,attacked,family);report.append({'field':field,'refused':False,'rows':len(p.rows),'excluded_id':ex['id'],'note_present_in_output':any('MANDATORY EXCLUDED LEGAL NOTE'in str(row)for row in p.rows)})
  except ValueError as e:report.append({'field':field,'refused':True,'error':str(e)})
print(json.dumps({'scope':'Adversarial actual-source branch fault only; recomputed hashes are not successful family verification credit','results':report},indent=2))
raise SystemExit(0 if all(x['refused']for x in report)else 2)
