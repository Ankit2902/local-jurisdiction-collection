"""Offline identify substantive table-bearing candidates from retained publisher TOCs."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def candidates():
 result=[]
 for a in json.loads((ROOT/'assignment.json').read_text()):
  name=a['jurisdiction'].lower().replace(' ','-');ds=[ROOT/'http'/name,ROOT/'recovery'/name,ROOT/'browser'/name];d=next((d for d in ds if (d/'toc-full.json').exists()),None)
  if not d:continue
  nodes=[]
  def walk(n,parents=[]):
   nodes.append({**n,'path':parents+[n.get('Heading','')]})
   for c in n.get('Children',[]):walk(c,parents+[n.get('Heading','')])
  walk(json.loads((d/'toc-full.json').read_text()))
  matches=[{'id':n['Id'],'heading':n.get('Heading'),'path':n['path']} for n in nodes if not n.get('HasChildren') and re.search(r'permitted uses|uses permitted|use regulations|use regulation chart|use table|allowed uses|land use regulations|permitted and conditional uses',n.get('Heading',''),re.I)]
  result.append({'jurisdiction':a['jurisdiction'],'folder':str(d.relative_to(ROOT)),'candidates':matches[:6]})
 (ROOT/'quality-candidates.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':candidates()
