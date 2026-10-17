"""Independent raw-native list/class/embedded-CSS inventory; zero transport."""
import json,hashlib,socket
from pathlib import Path
from collections import Counter
from bs4 import BeautifulSoup
base=Path(__file__).resolve().parent;project=base.parents[3]
def deny(*a,**k):raise AssertionError('No network')
socket.socket.connect=deny;socket.create_connection=deny
reports=[]
for relative in ['outputs/collection-readiness-next-2026-10-17/gridics/miami-client-qualified-v1','outputs/collection-readiness-2026-10-17/gridics/cupertino-portable-v4-replay']:
 path=project/relative;cp=json.loads((path/'start-checkpoint.json').read_text());classes=Counter();declared=Counter();tags=Counter();seen=set();bodies=0;lists=0;style_definitions=[];sources={}
 def walk(n):
  global bodies,lists
  assert n['id'] not in seen;seen.add(n['id'])
  if n.get('li_attr',{}).get('dataTag')=='BodyM':
   bodies+=1;markup=n.get('text') or '';soup=BeautifulSoup(markup,'html.parser')
   for node in soup.find_all(['ol','ul']):
    lists+=1;tags[node.name]+=1;classes.update(node.get('class',[]))
    if node.has_attr('style'):declared[node['style']]+=1
   for style in soup.find_all('style'):
    style_definitions.append({'owner_body_id':n['id'],'source_style_sha256':hashlib.sha256(str(style).encode()).hexdigest(),'custom_class_literals':[c for c in ['paren-value-paren','value-paren','style-square'] if c in style.get_text()]})
  for child in n.get('children',[]):walk(child)
 for row in cp['roots']:
  receipt=row['tree_response'];raw=(path/receipt['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==receipt['sha256'];sources[receipt['path']]=receipt['sha256']
  for n in json.loads(raw):walk(n)
 reports.append({'source':relative,'phase':'start','source_tree_sha256':sources,'nodes':len(seen),'BodyM_blocks':bodies,'lists':lists,'list_tags':dict(tags),'list_classes':dict(classes),'list_style_attributes':dict(declared),'embedded_style_elements':style_definitions})
(base/'raw-source-list-inventory.json').write_text(json.dumps({'network_requests':0,'scope':'Independent raw native BodyM inventory, no marker punctuation inferred','reports':reports},indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k not in ['source_tree_sha256','list_style_attributes']} for r in reports],indent=2))
