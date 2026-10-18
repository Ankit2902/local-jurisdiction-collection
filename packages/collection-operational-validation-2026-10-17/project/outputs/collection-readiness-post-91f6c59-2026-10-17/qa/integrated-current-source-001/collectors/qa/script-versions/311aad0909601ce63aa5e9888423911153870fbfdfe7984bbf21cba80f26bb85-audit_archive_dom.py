"""Independent original-archive HTML ownership and DOM table audit; no adapters."""
import argparse,collections,hashlib,json,re,zipfile
from pathlib import Path
from html.parser import HTMLParser
from lxml import html as lxml_html
from playwright.sync_api import sync_playwright
class Headings(HTMLParser):
 def __init__(self):super().__init__();self.article=0;self.ids=[]
 def handle_starttag(self,tag,attrs):
  if tag=='article':self.article+=1
  if self.article and re.fullmatch('h[1-6]',tag):
   value=dict(attrs).get('id')
   if value:self.ids.append(value)
 def handle_endtag(self,tag):
  if tag=='article':self.article-=1

def audit(run,record_path=None):
 record_path=record_path or run/'records.jsonl'
 records=[json.loads(x) for x in record_path.read_text().splitlines() if x];coverage=json.loads((run/'coverage.json').read_text());disps=coverage['dispositions'];expected={d['id'] for d in disps};member_ids={d['member']:d['id'] for d in disps};byid={r['id']:r for r in records};inventory=json.loads((run/'inventory.json').read_text());zipref=inventory[0]['raw_ref'];errors=[];unknown=[];ownerrors=[];network=[];table_records=[r for r in records if r['tables']];counts=collections.Counter();headings_by_member={};embedded_errors=[];embedded_owners=set();body_checks=[]
 with zipfile.ZipFile(run/zipref) as z:
  # This scan validates the source premise used to assign child heading ranges.
  # It uses original bytes and an independent HTML event parser, not records.
  for member,owner in member_ids.items():
   doc=lxml_html.fromstring(z.read(member));ids=doc.xpath('//article//*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]/@id');ids=[value for value in ids if value];own=ids.count(owner)
   if own!=1:ownerrors.append({'member':member,'owner_heading_count':own})
   headings_by_member[member]=ids
   for hid in ids:
    if hid in expected:continue
    unknown.append({'member':member,'id':hid});embedded_owners.add(owner);record=byid.get(owner)
    if not record or lxml_html.fromstring(record.get('html') or '<div></div>').xpath('count(//*[@id=$target])',target=hid)!=1:embedded_errors.append({'member':member,'owner_id':owner,'source_embedded_heading_id':hid,'kind':'source_embedded_heading_not_owned_exactly_once'})
  selected={r['id']:r for r in table_records}
  selected.update({owner:byid[owner] for owner in embedded_owners if owner in byid})
  with sync_playwright() as pw:
   browser=pw.chromium.launch(channel='chrome',headless=True);context=browser.new_context(java_script_enabled=False);context.route('**/*',lambda route:(network.append(route.request.url),route.abort()));page=context.new_page()
   for r in selected.values():
    member=r['raw_ref'].split('!',1)[1];raw=z.read(member)
    if hashlib.sha256(raw).hexdigest()!=r['raw_sha256']:raise ValueError('Original member hash binding failed')
    page.set_content(raw.decode(),timeout=120000)
    source=page.evaluate(r'''({owner,canonical})=>{let a=document.querySelector('article');for(let n of a.querySelectorAll('nav,script,style'))n.remove();let hs=Array.from(a.querySelectorAll('h1[id],h2[id],h3[id],h4[id],h5[id],h6[id]'));for(let h of hs){if(!h.id||h.id===owner||!canonical.includes(h.id))continue;let next=h.nextSibling;while(next){let n=next.nextSibling;if(/^H[1-6]$/.test(next.nodeName)&&next.id)break;next.remove();next=n;}h.remove()}for(let h of a.querySelectorAll('[id]'))if(h.id===owner)h.remove();
for(let e of Array.from(a.querySelectorAll('img,picture,svg,image,input'))){if(!e.parentNode)continue;if(e.tagName.toLowerCase()==='input'&&(e.type||'').toLowerCase()!=='image')continue;e.replaceWith(document.createTextNode('[IMAGE]'))}
for(let e of a.querySelectorAll('object,embed,source'))if((e.type||'').trim().toLowerCase().startsWith('image/')||/\.(png|jpe?g|svg|gif|webp|avif)([?#]|$)/i.test(e.data||e.src||'')||/^data:image\//i.test(e.data||e.src||''))e.replaceWith(document.createTextNode('[IMAGE]'));
for(let e of a.querySelectorAll('[background],[poster],[style]')){for(let attr of ['background','poster'])if(e.hasAttribute(attr)){e.prepend(document.createTextNode('[IMAGE]'));e.removeAttribute(attr)}let style=e.getAttribute('style')||'';let n=(style.match(/url\s*\(/gi)||[]).length;if(n){e.prepend(document.createTextNode('[IMAGE]'.repeat(n)));e.removeAttribute('style')}}
let ts=Array.from(a.querySelectorAll('table'));return {text:a.innerText,tables:ts.map(t=>({parent_table_index:ts.indexOf(t.parentElement.closest('table'))<0?null:ts.indexOf(t.parentElement.closest('table')),rows:Array.from(t.rows).map(tr=>Array.from(tr.cells).map(c=>({text:c.innerText,tag:c.tagName.toLowerCase(),rowspan:Number(c.getAttribute('rowspan')||1),colspan:Number(c.getAttribute('colspan')||1)})))}))}}''',{'owner':r['id'],'canonical':[hid for hid in headings_by_member[member] if hid in expected]})
    if r['id'] in embedded_owners:
     text=' '.join(source['text'].split());normalized=' '.join(r['text'].split());body_checks.append({'id':r['id'],'source_text':text,'normalized_text':normalized,'passed':text==normalized})
     if text!=normalized:errors.append({'id':r['id'],'field':'embedded-owner-body-text','source':text,'normalized':normalized})
    source=source['tables']
    if len(source)!=len(r['tables']):errors.append({'id':r['id'],'field':'table_count','source':len(source),'output':len(r['tables'])})
    for ti,t in enumerate(source):
     counts['tables']+=1;n=r['tables'][ti] if ti<len(r['tables']) else {};nrows=n.get('rows',[])
     if t['parent_table_index']!=n.get('parent_table_index'):errors.append({'id':r['id'],'table':ti,'field':'parent_table_index'})
     if len(t['rows'])!=len(nrows):errors.append({'id':r['id'],'table':ti,'field':'row_count'})
     for ri,row in enumerate(t['rows']):
      counts['rows']+=1;nr=nrows[ri] if ri<len(nrows) else []
      if len(row)!=len(nr):errors.append({'id':r['id'],'table':ti,'row':ri,'field':'cell_count'})
      for ci,c in enumerate(row):
       counts['cells']+=1
       for field,value in c.items():
        v=nr[ci].get(field) if ci<len(nr) else None
        if field=='text':value=' '.join(value.split());v=' '.join((v or '').split())
        if field in ['rowspan','colspan']:value=str(value);v=str(v)
        if value!=v:errors.append({'id':r['id'],'table':ti,'row':ri,'cell':ci,'field':field,'source':value,'normalized':v})
   browser_version=browser.version;browser.close()
 return {'schema_version':1,'kind':'original-archive-heading-ownership-and-browser-DOM-tables','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'records_sha256':hashlib.sha256(record_path.read_bytes()).hexdigest(),'canonical_source_pages_scanned':len(member_ids),'unknown_nonempty_heading_ids':unknown,'embedded_heading_ownership_errors':embedded_errors,'embedded_owner_body_checks':body_checks,'canonical_owner_heading_errors':ownerrors,'table_records':len(table_records),**counts,'browser':browser_version,'network_requests_sent':0,'resource_requests_aborted':len(network),'mismatches':errors,'passed':not(errors or embedded_errors or ownerrors),'limits':['Table text compared after whitespace collapse; legal body serialization outside tables is not established by this check.','Structural navigation-only exclusions are inventoried here, not independently semantically adjudicated.']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--records',type=Path);a=p.parse_args()
 if a.out.exists() or a.run.resolve() in a.out.resolve().parents:raise SystemExit('fresh report outside evidence required')
 result=audit(a.run,a.records);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['mismatches','unknown_nonempty_heading_ids']},indent=2));print('mismatch sample',result['mismatches'][:5]);raise SystemExit(0 if result['passed'] else 2)
