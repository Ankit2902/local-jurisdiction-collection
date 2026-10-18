"""Local-only independent fresh-runtime receipt/profile validation."""
import hashlib,importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
repo=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection')
runtime=root/'runtime-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((runtime/'runtime.json').read_text());doctor=json.loads((root/'doctor-browser.stdout').read_text());commands=json.loads((root/'commands.json').read_text())
assert all(command['exit']==0 for command in commands)
assert receipt['setup_complete'] and receipt['browser']['passed'] and receipt['browser']['headed']
assert doctor['ready'] and doctor['runtime_ready'] and doctor['browser']['passed'] and doctor['browser']['headed']
assert doctor['publisher_requests']==receipt['publisher_requests']==0
pinned={line.split('==')[0].lower().replace('_','-'):line.split('==')[1] for line in (repo/'collectors/ops/requirements.txt').read_text().splitlines() if line and not line.startswith('#')}
code='import importlib.metadata,json,sys;print(json.dumps({"python":sys.version,"packages":{d.metadata["Name"].lower().replace("_","-"):d.version for d in importlib.metadata.distributions()}}))'
actual=json.loads(subprocess.check_output([str(runtime/'venv/bin/python'),'-B','-c',code],text=True))
assert all(actual['packages'].get(name)==version for name,version in pinned.items())
assert actual['packages']=={p['name'].lower().replace('_','-'):p['version'] for p in receipt['packages']}
node=Path(receipt['node']);core=node.parent/'package'
env=dict(os.environ,NODE_PATH=str(runtime/'node_modules'),COLLECTION_PLAYWRIGHT_CORE=str(core))
js='const a=require("playwright"),b=require(process.env.COLLECTION_PLAYWRIGHT_CORE);console.log(JSON.stringify({same_api:a===b,chromium_launch:typeof a.chromium.launch,core_version:require(process.env.COLLECTION_PLAYWRIGHT_CORE+"/package.json").version,node:process.version}))'
bridge=json.loads(subprocess.check_output([str(node),'-e',js],env=env,text=True));assert bridge['same_api'] and bridge['chromium_launch']=='function'
for src,dest in [(runtime/'runtime.json',root/'fresh-runtime-receipt.json'),(runtime/'install.log',root/'dependency-install.log'),(runtime/'node_modules/playwright/package.json',root/'bridge-package.json'),(runtime/'node_modules/playwright/index.cjs',root/'bridge-index.cjs'),(repo/'collectors/american-legal/requirements-lock.txt',root/'american-legal-standalone-lock.txt')]:shutil.copyfile(src,dest)
standalone={line.split('==')[0].lower().replace('_','-'):line.split('==')[1] for line in (root/'american-legal-standalone-lock.txt').read_text().splitlines() if line and not line.startswith('#')}
diffs={name:{'standalone_lock':ver,'fresh_shared':actual['packages'].get(name)} for name,ver in standalone.items() if actual['packages'].get(name)!=ver}
comparison={'american_legal_standalone_package_json_sha256':sha(repo/'collectors/american-legal/package.json'),'standalone_node_playwright_pin':json.loads((repo/'collectors/american-legal/package.json').read_text())['dependencies']['playwright'],'fresh_python_playwright_distribution':actual['packages']['playwright'],'fresh_official_bundled_api_core':bridge['core_version'],'fresh_node':bridge['node'],'python_lock_differences':diffs,'profiles_equivalent_claimed':False,'live_american_legal_transport_qualified':False}
report={'passed':True,'scope':'fresh_shared_macos_setup_and_local_headed_browser_only','publisher_requests':0,'image_fetch_decode_render_ocr':False,'direct_pins_matched':len(pinned),'installed_distribution_count':len(actual['packages']),'local_alias_check':bridge,'runtime_browser':receipt['browser'],'doctor_browser':doctor['browser'],'standalone_profile_comparison':comparison,'runbook_observations':[{'kind':'host_prerequisite','detail':'python3.12 is not on this host PATH. Used documented absolute path to installed Python3.12.14; Chrome installed. Not a setup implementation failure.'},{'kind':'dependency_scope','detail':'Shared requirements pin exact direct dependencies; transitive versions are resolved by pip and captured in runtime receipt/freeze. They are not claimed identical to standalone family locks.'}],'setup_or_doctor_defects_observed':[],'source_integrity':json.loads((root/'source-integrity.json').read_text())}
(root/'independent-runtime-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
