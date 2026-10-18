"""Narrow exact-source reference and wrapped-image candidate review, no network."""
import argparse,copy,hashlib,importlib,json,socket,sys,types
from pathlib import Path
from unittest.mock import patch

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('candidate',type=Path);ap.add_argument('--native',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh output required')
 folder=a.candidate/'collectors/encodeplus';before={p.name:sha(p) for p in folder.glob('*.py')};pkg=types.ModuleType('qa_ep_reference_candidate');pkg.__path__=[str(folder)];sys.modules[pkg.__name__]=pkg;refs=importlib.import_module(pkg.__name__+'.publication_references');model=importlib.import_module(pkg.__name__+'.model');fixture=json.loads((folder/'fixtures/overland-reference-records.json').read_text());checks=[]
 def check(name,value):checks.append({'name':name,'passed':bool(value)});assert value,name
 def projection(rows):return {key:{k:v for k,v in r.items() if k not in ['assets','qualified_reference_dispositions']} for key,r in rows.items()}
 def deny(*args,**kwargs):raise AssertionError('CANDIDATE_NETWORK_FORBIDDEN')
 with patch.object(socket.socket,'connect',deny),patch.object(socket,'create_connection',deny):
  original=fixture['records'];cfg=fixture['config'];rows=refs.reconcile(copy.deepcopy(original),cfg);check('reference_reconciliation_keeps_all_body_table_link_fields',projection(rows)==projection(original))
  for url,q in refs.INTERNAL.items():
   check('exact_malformed_reference_resolved_with_retained_target',not any(x['url']==url for x in rows[q['owner_id']]['assets']))
   for mutation in ['owner','target','witness','missing']:
    changed=copy.deepcopy(original)
    if mutation=='missing':changed.pop(q['substantive_target_witness']['id'])
    else:
     ident={'owner':q['owner_id'],'target':q['target']['id'],'witness':q['substantive_target_witness']['id']}[mutation];changed[ident]['body_sha256']='wrong'
    result=refs.reconcile(changed,cfg);check('changed_'+mutation+'_leaves_original_required_reference',any(x['url']==url for x in result[q['owner_id']]['assets']))
  wrong=copy.deepcopy(cfg);wrong['scope']='changed-publication';changed=copy.deepcopy(original);check('wrong_config_never_applies_source_exemptions',refs.reconcile(changed,wrong)==original)
  native=a.native.read_bytes();check('actual_native_alternative_identity_hash_pages_cover',refs.qualify_bound_document(rows,refs.ALTERNATIVE['url'],native)==refs.ALTERNATIVE)
  try:refs.qualify_bound_document(rows,refs.ALTERNATIVE['url'],native+b'changed');accepted=True
  except ValueError:accepted=False
  check('changed_native_bytes_rejected',not accepted)
  tail='UElYRUxTX0NPTlRJTlVBVElPTl9NVVNUX05PVF9TVVJWSVZF';uri='DATA:IMAGE/PNG;base64,QUJD\n'+tail;imagecfg={'base':'https://example.invalid/book/','identity':'Fixture','jurisdiction':'Fixture NV','scope':'candidate image text'}
  def parse(body):return model.parse_document('<div id="thePage" secid="1"><section data-secid="1"><h2>§ 1</h2>'+body+'</section></div>','1',imagecfg,{'1':{'heading':'§ 1','has_children':False}})[0]
  r=parse('<p>Before legal text "'+uri+'" after legal text</p>');check('quoted_wrapped_text_preserves_prose_without_pixels',tail not in json.dumps(r) and all(t in r['text'] for t in ['Before legal text','after legal text','[IMAGE]']))
  for space in ['\n','\t',' ']:
   try:parse('<p>Before legal text DATA:IMAGE/PNG;base64,QUJD'+space+tail+' after legal text</p>');accepted=True
   except ValueError:accepted=False
   check('ambiguous_bare_whitespace_fails_closed',not accepted)
 check('candidate_sources_unchanged',before=={p.name:sha(p) for p in folder.glob('*.py')})
 report={'passed':True,'candidate_sources':before,'fixture_sha256':sha(folder/'fixtures/overland-reference-records.json'),'native_sha256':sha(a.native),'checks':checks,'network_requests_sent':0,'scope':'Exact source-bound internal refs and source-observed same-city/same-edition original only; no broad publication waiver or native semantic promotion. Image policy checked through real parser.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'checks':len(checks)}))
if __name__=='__main__':main()
