"""Read-only normalized stream and standalone dependency audit; no browser/network/images."""
import ast,csv,json,re
from pathlib import Path
from bs4 import BeautifulSoup
from source_common import sha,save,stamp
ROOT=Path(__file__).resolve().parent
SELECTED=['flagstaff-html-normalized-qualified-v3','king-county-normalized-final-v6','king-county-word-normalized-final-v8']
def run():
 rows=[]
 for name in SELECTED:
  path=ROOT/'evidence'/name;bad=[];records=0;markers=0;images=0
  for i,line in enumerate((path/'records.jsonl').open(),1):
   records+=1;item=json.loads(line);markers+=line.count('[IMAGE]')
   def check(v,trail):
    if isinstance(v,dict):
     for k,x in v.items():check(x,trail+'.'+k)
    elif isinstance(v,list):
     for n,x in enumerate(v):check(x,trail+f'[{n}]')
    elif isinstance(v,str):
     if re.search(r'data\s*:\s*image\s*/',v,re.I):bad.append([i,trail,'image-data-uri'])
     if trail.endswith(('.semantic_html','.content_html')):
      s=BeautifulSoup(v,'html.parser')
      for tag in s.find_all(True):
       if tag.name in ['img','picture','svg','image','source','object','embed','iframe','script']:bad.append([i,trail,'active-image-or-embedded-tag:'+tag.name])
       for attr,value in tag.attrs.items():
        if attr.lower() in ['background','srcset'] or attr.lower().startswith('on') or (attr.lower()=='style' and re.search(r'url\s*\(',str(value),re.I)):bad.append([i,trail,'active-attribute:'+attr])
   check(item,'record')
  csvpath=path/'records.csv';csvrows=None
  if csvpath.exists():
   with csvpath.open(newline='') as f:csvrows=sum(1 for _ in csv.DictReader(f))
   if csvrows!=records:bad.append(['csv','count','CSV/JSONL mismatch'])
  rows.append({'normalized':str(path.relative_to(ROOT)),'legal_streams':['records.jsonl']+(['records.csv'] if csvpath.exists() else []),'jsonl_records':records,'csv_records':csvrows,'literal_placeholder_occurrences_in_all_json_fields':markers,'failures':bad,'passed':not bad,'records_sha256':sha((path/'records.jsonl').read_bytes())})
 files={p.stem:p for p in ROOT.glob('*.py')};modules=[];unresolved=set();third=set()
 for name,p in sorted(files.items()):
  imports=[]
  for node in ast.walk(ast.parse(p.read_text())):
   if isinstance(node,ast.Import):imports.extend(x.name.split('.')[0] for x in node.names)
   elif isinstance(node,ast.ImportFrom) and node.module:imports.append(node.module.split('.')[0])
  local=sorted(set(x for x in imports if x in files));third.update(x for x in imports if x not in files)
  modules.append({'path':p.name,'sha256':sha(p.read_bytes()),'local_dependencies':[x+'.py' for x in local]})
 config_names=['configs.json','integration.json','source_dispositions.json','source_character_dispositions.json','requirements.txt']
 save(ROOT/'module-manifest.json',{'schema':'original-adapter-module-closure-1','generated_at':stamp(),'standalone':True,'modules':modules,'configuration':[{'path':n,'sha256':sha((ROOT/n).read_bytes())} for n in config_names],'imports_not_local':sorted(third),'installed_requirements':'requirements.txt','external_project_imports':False,'normalized_streams':'records.jsonl; HTML also records.csv; Word notes/ancillary are same stream'})
 result={'schema':'original-final-normalized-image-audit-1','generated_at':stamp(),'scope':'Read all selected normalized JSONL recursive fields and CSV counts; no native image members or browser/network accessed. Source-acquisition no-image enforcement is separately tested; this is delivered-normalization audit.','passed':all(x['passed'] for x in rows),'outputs':rows};save(ROOT/'evidence/final-normalized-image-audit.json',result);return result
if __name__=='__main__':print(json.dumps(run(),indent=2))
