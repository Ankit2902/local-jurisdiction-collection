"""Offline normalize bounded Municode CodesContent samples; Python3 stdlib only.
Preserves HTML, source identifiers, lists in HTML, tables/cell span attributes, links and footnotes.
No claim that the selected leaf sample or TOC is a complete legal corpus.
"""
import argparse,csv,hashlib,json,re
from pathlib import Path
from html.parser import HTMLParser
from html import unescape
class LegalHTML(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.text=[];self.tables=[];self.links=[];self.table=None;self.row=None;self.cell=None;self.link=None;self.lists=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag in ('p','div','br','li','tr','h1','h2','h3','h4','h5','h6','table'):self.text.append('\n')
  if tag in ('br','p','div','li') and self.cell is not None:self.cell['text']+='\n'
  if tag in ('ol','ul'):self.lists+=1
  if tag=='table':self.table=[];self.tables.append(self.table)
  if tag=='tr' and self.table is not None:self.row=[];self.table.append(self.row)
  if tag in ('td','th') and self.row is not None:self.cell={'text':'','tag':tag,'rowspan':a.get('rowspan','1'),'colspan':a.get('colspan','1')};self.row.append(self.cell)
  if tag=='a':self.link={'href':a.get('href',''),'attributes':a,'target_node_id':a.get('data-nodeid') or a.get('data-node-id') or a.get('data-chunk-id'),'link_type':a.get('data-linktype'),'text':''};self.links.append(self.link)
 def handle_endtag(self,tag):
  if tag in ('p','div','li','tr','h1','h2','h3','h4','h5','h6'):self.text.append('\n')
  if tag in ('p','div','li') and self.cell is not None:self.cell['text']+='\n'
  if tag in ('td','th'):self.cell=None
  if tag=='tr':self.row=None
  if tag=='table':self.table=None
  if tag=='a':self.link=None
 def handle_data(self,data):
  self.text.append(data)
  if self.cell is not None:self.cell['text']+=data
  if self.link is not None:self.link['text']+=data
 def parsed(self):
  t='\n'.join(re.sub(r'\s+',' ',s).strip() for s in ''.join(self.text).splitlines());t=re.sub(r'\n{3,}','\n\n',t).strip()
  for table in self.tables:
   for row in table:
    for cell in row:cell['text']=re.sub(r'\s+',' ',cell['text']).strip()
  return t

def normalize(folder,out=None):
 folder=Path(folder);out=Path(out) if out else folder/'normalized';out.mkdir(parents=True,exist_ok=True)
 samples=json.loads((folder/'samples.json').read_text());receipt=json.loads((folder/'receipt.json').read_text());records=[];checks=[]
 for sample in samples:
  node=sample['node'];docs=sample['content'].get('Docs',[]);matches=[d for d in docs if d.get('Id')==node['Id']]
  if len(matches)!=1:raise ValueError(f'Expected exactly one requested doc {node["Id"]}: {len(matches)}')
  doc=matches[0];html=doc.get('Content') or '';parser=LegalHTML();parser.feed(html);text=parser.parsed()
  if not text.strip():raise ValueError('Empty legal body '+node['Id'])
  title=LegalHTML();title.feed(doc.get('Title') or doc.get('TitleHtml') or node.get('Heading') or '')
  record={'node_id':node['Id'],'heading':title.parsed(),'toc_heading':node['Heading'],'path':node.get('path',[]),'text':text,'html':html,'tables':parser.tables,'links':parser.links,'list_count':parser.lists,'footnotes':doc.get('Footnotes'),'notes':doc.get('Notes'),'doc_order_id':doc.get('DocOrderId'),'product_id':receipt['product']['ProductID'],'job_id':receipt['job']['Id'],'source_url':receipt['url'].split('?')[0]+'?nodeId='+node['Id'],'body_sha256':hashlib.sha256(html.encode()).hexdigest(),'complete_corpus':False}
  records.append(record)
  checks.append({'node_id':node['Id'],'exact_requested_doc_present':True,'nonempty_body':True,'heading_present':bool(record['heading']),'table_count':len(parser.tables),'cross_reference_links':len([l for l in parser.links if 'nodeId=' in l['href'] or l.get('target_node_id')]),'source_html_retained':True})
 if len({r['node_id'] for r in records})!=len(records):raise ValueError('Duplicate requested nodes')
 (out/'sections.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
 with (out/'sections.csv').open('w',newline='') as f:
  fields=['node_id','heading','text','product_id','job_id','source_url','body_sha256'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in records)
 report={'record_count':len(records),'table_count':sum(len(r['tables']) for r in records),'list_count':sum(r['list_count'] for r in records),'link_count':sum(len(r['links']) for r in records),'checks':checks,'complete_corpus':False,'raw_samples_sha256':hashlib.sha256((folder/'samples.json').read_bytes()).hexdigest(),'parser_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'outputs_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/'sections.jsonl',out/'sections.csv']}}
 (out/'verification.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--out',type=Path);p.add_argument('--offline',action='store_true',help='All normalization is offline; explicit flag supported for replay');a=p.parse_args();print(json.dumps(normalize(a.folder,a.out),indent=2))
