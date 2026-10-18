"""Source-bound common preflight + compact existing standard AL verification."""
import sys
sys.dont_write_bytecode=True
import ast,hashlib,importlib.util,json,shutil,socket,tempfile
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
ROOT=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 bound=[ROOT/'collectors/registry/catalog.py',ROOT/'collectors/ops/launcher.py']+list((ROOT/'collectors/american-legal').glob('*.py'))+list((ROOT/'collectors/american-legal').glob('*.cjs'))
 before={str(p):sha(p) for p in bound}
 spec=importlib.util.spec_from_file_location('selected_catalog',ROOT/'collectors/registry/catalog.py');cat=importlib.util.module_from_spec(spec);spec.loader.exec_module(cat)
 actual=cat.load_catalog();selected=[p for p in actual['publications'] if p['publisher']=='american-legal'];assert len(selected)==23
 with tempfile.TemporaryDirectory() as td:
  td=Path(td);registry=td/'registry';registry.mkdir()
  for p in (ROOT/'collectors/registry').glob('*.json'):shutil.copy2(p,registry/p.name)
  shutil.copy2(HERE/'candidate/collectors/registry/access-advisories.json',registry/'access-advisories.json')
  candidate=cat.load_catalog(here=registry);pubs=[p for p in candidate['publications'] if p['publisher']=='american-legal'];assert len(pubs)==23
  for pub in pubs:
   records=[a for a in pub['observed_access_advisories'] if a['family']=='american-legal'];assert len(records)==1 and records[0]['source_sha256']=='cc41433c18b63efb119a07e3e1ce27c8309921471f2e2d0b4f8cc564adbcb66d'
  launcher=ROOT/'collectors/ops/launcher.py';tree=ast.parse(launcher.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='access_state')
  ns={'Path':Path,'ROOT':ROOT,'referenced_hosts':lambda pub,out:[],'retained_stops':lambda pub,out,stops:stops,'read':load}
  exec(compile(ast.Module(body=[fn],type_ignores=[]),str(launcher),'exec'),ns)
  gate=td/'absentgate';stops=ns['access_state'](pubs[0],{'AMLEGAL_GATE_DIR':str(gate)})
  assert len(stops)==1 and stops[0]['checkpoint_access_advisory'] is True and not gate.exists()
  assert stops[0]['state']['observed_stop']==load(HERE/'evidence/browser-stop.json')
  unchanged_non_al=[]
  old={p['id']:p for p in actual['publications']}
  for p in candidate['publications']:
   if p['publisher']!='american-legal':assert p==old[p['id']];unchanged_non_al.append(p['id'])
 # Execute only compact preexisting HTML fixture standard verifier. No acquisition.
 sys.path.insert(0,str(ROOT/'collectors/american-legal'))
 from verify import verify
 from PIL import Image
 fixture=ROOT/'collectors/american-legal/fixtures/nested-synthetic.zip';fixture_sha=sha(fixture)
 forbidden=[]
 def block(*a,**k):forbidden.append('forbidden');raise AssertionError('network/image operation forbidden')
 with patch.object(socket.socket,'connect',block),patch.object(socket,'create_connection',block),patch.object(Image,'open',block):
  report=verify(fixture)
 assert not forbidden and sha(fixture)==fixture_sha
 assert before=={str(p):sha(p) for p in bound}
 result={'passed':True,'common_catalog_actual_AL_publications':len(pubs),'all_receive_exact_new_stop':True,'unchanged_other_publications':len(unchanged_non_al),'actual_common_access_state_ast_fresh_absent_gate_refused':True,'physical_gate_created':False,'standard_readonly_fixture_verification':{'fixture_sha256':fixture_sha,'inventory_count':report['inventory_count'],'publication_complete':report['publication_complete'],'image_binary_download_count':report['image_binary_download_count'],'image_reference_placeholder_count':report['image_reference_placeholder_count'],'no_requests_or_image_open':not forbidden,'fixture_unchanged':True},'production_sources_unchanged':True,'source_sha256':before,'publisher_requests':0,'limits':['Common integration tests actual source catalog/preflight functions with isolated registry JSON overlay; no full common acquisition or runtime doctor invoked.','Read-only verifier uses the existing compact synthetic HTML fixture, not a new full actual publication replay.']}
 (HERE/'common-and-offline.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'AL_publications':len(pubs),'fixture_nodes':report['inventory_count']}))
if __name__=='__main__':main()
