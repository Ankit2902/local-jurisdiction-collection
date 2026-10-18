import datetime,hashlib,json,os,platform,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection')
BASE=Path('/Users/oliverflint/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
RUNTIME=ROOT/'runtime-v1'
assert not RUNTIME.exists(),'Fresh setup runtime already exists; do not silently reuse'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=['collect.py','collectors/ops/launcher.py','collectors/ops/browser_check.cjs','collectors/ops/requirements.txt','collectors/ops/README.md','collectors/american-legal/requirements.txt','collectors/american-legal/package.json']
before={name:sha(REPO/name) for name in files}
for name in files:
 dest=ROOT/'executed-source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(REPO/name,dest)
commands=[]
def run(label,args,env=None):
 started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (ROOT/(label+'.stdout')).open('w') as out,(ROOT/(label+'.stderr')).open('w') as err:
  proc=subprocess.run([str(a) for a in args],cwd=REPO,stdout=out,stderr=err,env=env)
 record={'label':label,'argv':[str(a) for a in args],'cwd':str(REPO),'exit':proc.returncode,'started_at':started,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stdout':label+'.stdout','stderr':label+'.stderr'};commands.append(record);(ROOT/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');return proc.returncode
# Preserve actual host discovery, not an invented Python-on-PATH assumption.
(ROOT/'host.json').write_text(json.dumps({'platform':platform.platform(),'python3.12_on_path':shutil.which('python3.12'),'selected_base_python':str(BASE),'chrome_installed':Path('/Applications/Google Chrome.app').is_dir(),'source_before':before},indent=2)+'\n')
code=run('setup',[BASE,'-B',REPO/'collect.py','--runtime',RUNTIME,'setup','--python',BASE])
if code==0:
 run('doctor-browser',[BASE,'-B',REPO/'collect.py','--runtime',RUNTIME,'doctor','--browser'])
 run('installed-pip-check',[RUNTIME/'venv/bin/python','-B','-m','pip','check'])
 run('installed-pip-freeze',[RUNTIME/'venv/bin/python','-B','-m','pip','freeze','--all'])
after={name:sha(REPO/name) for name in files}
(ROOT/'source-integrity.json').write_text(json.dumps({'before':before,'after':after,'unchanged':before==after},indent=2)+'\n')
assert before==after,'Source changed during setup'
print(json.dumps({'setup_exit':code,'commands':commands,'source_unchanged':before==after},indent=2))
