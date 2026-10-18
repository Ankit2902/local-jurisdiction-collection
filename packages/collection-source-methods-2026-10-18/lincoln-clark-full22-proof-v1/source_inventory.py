"""Independent stdlib source-row ownership audit, no native/network/image operations."""
from html.parser import HTMLParser
import re
ROUTE='https://www.clarkcountynv.gov/government/elected_officials/county_clerk/county-code'
BASE_CODE='https://library.municode.com/nv/clark_county/codes/code_of_ordinances'
class Node:
 def __init__(self,tag='',attrs=()):self.tag=tag;self.attrs=dict(attrs);self.children=[]
 def text(self):return re.sub(r'\s+',' ',' '.join(x.text()if isinstance(x,Node)else x for x in self.children)).strip()
 def nodes(self,tag=None):
  for c in self.children:
   if isinstance(c,Node):
    if tag is None or c.tag==tag:yield c
    yield from c.nodes(tag)
class Tree(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.root=Node('root');self.stack=[self.root]
 def handle_starttag(self,tag,attrs):
  n=Node(tag,attrs);self.stack[-1].children.append(n)
  if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:self.stack.append(n)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==tag:del self.stack[i:];break
 def handle_data(self,s):self.stack[-1].children.append(s)
def projection(data):
 p=Tree();p.feed(data.decode());tables=[n for n in p.root.nodes('div')if {'table','bordered','bid'}<=set(n.attrs.get('class','').split())];assert len(tables)==1,'Exact one Clerk ordinance source table required';rows=[];headers=[]
 for row in [n for n in tables[0].children if isinstance(n,Node)and n.tag=='div']:
  cells=[n for n in row.children if isinstance(n,Node)and n.tag=='div'];assert len(cells)==4,'Four source-labelled columns required';anchors=list(cells[0].nodes('a'))
  if not anchors:headers.append([c.text()for c in cells]);continue
  assert len(anchors)==1;anchor=anchors[0];rows.append({'ordinance':anchor.text(),'url':anchor.attrs['href'],'title':cells[1].text(),'adopted_literal':cells[2].text(),'effective_literal':cells[3].text()})
 assert headers==[['Ordinance/ Bill No.','Title','Adopted','Effective']],'Source column meaning changed'
 aliases=[n.attrs['href']for n in p.root.nodes('a')if'library.municode.com'in n.attrs.get('href','')];assert aliases==[BASE_CODE],'Required codified county-code link changed/foreign'
 return rows
def validate(data,source_url,expected):
 assert source_url==ROUTE==expected['source_url'],'Wrong government source route'
 rows=projection(data);keys=['ordinance','url','title','adopted_literal','effective_literal'];wanted=[{k:r[k]for k in keys}for r in expected['uncodified_ordinances']]
 assert rows==wanted and len(rows)==22,'Missing/extra/reordered or altered source-owned ordinance rows/dates'
 return rows
