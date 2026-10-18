"""Real root CLI planning/refusals, subprocess source imports guarded; no acquisition."""
import pathlib,json,subprocess,sys,os,hashlib,importlib.util
P=pathlib.Path(__file__).resolve().parent;C=P/'candidate';R=pathlib.Path(json.loads((P/'source-binding.json').read_text())['repository'])
D=P/'cli-evidence';D.mkdir(exist_ok=True)
env={**os.environ,'PYTHONPATH':str(P/'tripwire'),'PYTHONDONTWRITEBYTECODE':'1'}
commands=[]
def cli(name,args,expected=0):
 r=subprocess.run([sys.executable,'-B',str(C/'collect.py'),*args],cwd=C,env=env,text=True,capture_output=True)
 (D/(name+'.stdout')).write_text(r.stdout);(D/(name+'.stderr')).write_text(r.stderr)
 commands.append({'name':name,'argv':[sys.executable,'-B','collect.py',*args],'exit':r.returncode,'expected_exit':expected,'source_import_guard':'tripwire/sitecustomize.py','scope':'Actual rootCLI/registry planning or refusal only; no collector subprocess executed.'})
 assert r.returncode==expected,(name,r.returncode,r.stderr)
 return json.loads(r.stdout)if expected==0 else None
allplan=cli('all225',['plan','--all-publications']);historical=next(x for x in allplan['plans']if x['publication_id']=='82-8fbdce15716d')['runnable'];expected=196+int(historical);assert(allplan['publication_count'],allplan['runnable_config_count'])==(225,expected)
assert sum(not x['runnable']for x in allplan['plans'])==225-expected
assert sum(bool(x['observed_access_advisories'])for x in allplan['plans'])==154
chosen=next(x for x in allplan['plans']if x['publication_id']=='96-7e8795b1baee');assert chosen['qualified_config_path']=='collectors/official/configs/clark-title30-current-associated-documents.json'
primary=cli('primary130',['plan','--all']);assert primary['targets']==130
selected=cli('clark-selected',['plan','--target','96','--publication','96-7e8795b1baee']);assert selected['runnable_config_count']==1 and selected['plans'][0]['argv'][1]=='collectors/official/collect.py'
owned=cli('clark-target',['plan','--all-publications','--target','96']);assert any(x['publication_id']=='96-7e8795b1baee'and x['runnable']for x in owned['plans'])
for name,args in [('wrong-owner',['plan','--target','95','--publication','96-7e8795b1baee']),('all-run',['run','--target','96','--all-publications','--out',str(P/'SHOULD-NOT-EXIST')]),('unknown-publication',['plan','--publication','96-unknown']),('wrong-cohort',['plan','--cohort','original','--target','96','--publication','96-7e8795b1baee'])]:cli(name,args,2)
refusal=cli('correct-run-global-runtime-refusal',['--runtime',str(P/'NO-RUNTIME'),'run','--target','96','--publication','96-7e8795b1baee','--out',str(P/'SHOULD-NOT-EXIST')],3)
assert 'invalid choice' not in (D/'correct-run-global-runtime-refusal.stderr').read_text()
assert not(P/'SHOULD-NOT-EXIST').exists()and not(P/'NO-RUNTIME').exists()
sys.path.insert(0,str(C/'collectors/registry'));from catalog import load_catalog
old=load_catalog(here=R/'collectors/registry');new=load_catalog(here=C/'collectors/registry');a={x['id']:x for x in old['publications']};b={x['id']:x for x in new['publications']};changes=[i for i in a if a[i]!=b[i]];assert '96-7e8795b1baee'in changes and set(changes)<=({'96-7e8795b1baee','82-8fbdce15716d'}if historical else {'96-7e8795b1baee'});assert old['targets']==new['targets']
report={'passed':True,'actual_root_cli_cases':len(commands),'commands':commands,'all_publications':225,'runnable_configs':expected,'unqualified':225-expected,'advisory_entries':154,'primary_count':130,'changed_catalog_publications':changes,'other_publications_unchanged':225-len(changes),'government_primary_rows_unchanged':130,'publisher_requests_native_image_calls':0,'common_verify_executed':False,'qualification':'Liveproof remains sealed familyverification with exact16source+config bridge; currentCLI planning/refusal/dispatch only.'}
(P/'cli-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
