"""Independent original form inventory, native headings and all browser DOM tables.

No official parser imports. This checks source presence/heading occurrences and
cell fidelity; whole legal body ownership and external attachments remain separate.
"""
import argparse,collections,hashlib,json,re
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from lxml import html
from playwright.sync_api import sync_playwright
from inert_browser_source import attach_inert_html,provenance

def sha(b):return hashlib.sha256(b).hexdigest()
def clean(t):return ' '.join(t.split())
def table_key(t):return json.dumps([[{k:clean(str(v)) if k=='text' else str(v) for k,v in c.items() if k in ['text','tag','rowspan','colspan']} for c in row] for row in t['rows']],sort_keys=True)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--normalized',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh report required')
 cp=json.loads((a.source/'checkpoint.json').read_text());rep=json.loads((a.normalized/'replay.json').read_text());recordbytes=(a.normalized/'records.jsonl').read_bytes();rs=[json.loads(x) for x in recordbytes.splitlines()];groups=collections.defaultdict(list)
 for r in rs:groups[r['document_id']].append(r)
 inv=json.loads((a.source/'inventory.json').read_text());items={v['id']:v for v in inv};ref=cp['identity']['section_inventory_ref'];rawtoc=(a.source/ref).read_bytes();toc=html.fromstring(rawtoc);controls=toc.xpath('//form[@name="formSMC"]//input[@name="Section"]');labels=collections.defaultdict(set);enabled=[];disabled=[]
 for e in controls:
  ident=e.get('value').strip();row=e.getparent()
  while row is not None and row.tag!='tr':row=row.getparent()
  anchors=row.xpath('.//a[@href]') if row is not None else [];label=clean(''.join((anchors[0].getparent() if anchors else row).itertext()))
  labels[ident].add(label);(disabled if 'disabled' in e.attrib else enabled).append(ident)
 errors=[];checks=[];counts=collections.Counter();blocked=[];allheaders=collections.Counter()
 planned=[value.strip() for item in inv for key,value in item['post_fields'] if key=='Section']
 if len(planned)!=len(set(planned)) or set(planned)!=set(enabled):errors.append({'kind':'independent_form_vs_request_inventory','planned':len(planned),'source_enabled_unique':len(set(enabled))})
 with sync_playwright() as pw:
  browser=pw.chromium.launch(channel='chrome',headless=True);ctx=browser.new_context(java_script_enabled=False);ctx.route('**/*',lambda route:(blocked.append(route.request.url),route.abort()));p=ctx.new_page()
  for batch in rep['batches']:
   item=items[batch['item_id']];raw=(a.source/batch['raw_ref']).read_bytes();assert sha(raw)==batch['raw_sha256'];root=html.fromstring(raw);scope=root.get_element_by_id('hideRepealed');headers=collections.Counter()
   for anchor in scope.xpath('.//a[@href]'):
    query=parse_qs(urlparse(anchor.get('href')).query);ident=query.get('Section',[''])[0].strip()
    if ident not in labels or clean(''.join(anchor.itertext()))!='Section '+ident:continue
    title=anchor.tail or '';next_=anchor.getnext()
    while next_ is not None and next_.tag in ['span','b','i','em','strong','sup','sub']:
     title+=''.join(next_.itertext())+(next_.tail or '');next_=next_.getnext()
    if next_ is not None and next_.tag=='br' and 'Section '+ident+' '+clean(title) in labels[ident]:headers[(ident,clean(title))]+=1
   output=collections.Counter((r.get('citation',r['id']),r['heading']) for r in groups[item['id']] if r['unit'] in ['legal_section','legal_section_version'])
   if headers!=output:errors.append({'kind':'native_header_occurrence_vs_output','item':item['id'],'missing':list((headers-output).elements()),'extra':list((output-headers).elements())})
   allheaders.update(headers);attach_inert_html(p,raw)
   source=p.evaluate(r'''()=>Array.from(document.querySelector('#hideRepealed').querySelectorAll('table')).map(t=>({rows:Array.from(t.rows).map(row=>Array.from(row.cells).map(c=>({text:c.innerText,tag:c.tagName.toLowerCase(),rowspan:c.getAttribute('rowspan')||'1',colspan:c.getAttribute('colspan')||'1'})))}))''')
   normalized=[t for r in groups[item['id']] for t in r['tables']];sc=collections.Counter(table_key(t) for t in source);nc=collections.Counter(table_key(t) for t in normalized)
   if sc!=nc:errors.append({'kind':'native_table_multiset','item':item['id'],'missing_tables':list((sc-nc).elements()),'extra_tables':list((nc-sc).elements())})
   counts['tables']+=len(source);counts['rows']+=sum(len(t['rows']) for t in source);counts['cells']+=sum(len(row) for t in source for row in t['rows']);counts['native_heading_occurrences']+=sum(headers.values());checks.append({'item':item['id'],'source_sha256':batch['raw_sha256'],'headers':sum(headers.values()),'tables':len(source)})
  version=browser.version;browser.close()
 status={r['id'] for r in rs if r['unit']=='legal_status' and r['id'] in disabled}
 if status!=set(disabled):errors.append({'kind':'disabled_native_status','missing':list(set(disabled)-status)})
 report={'passed':not errors,'script_sha256':sha(Path(__file__).read_bytes()),'records_sha256':sha(recordbytes),'raw_section_inventory_sha256':sha(rawtoc),'source_controls':len(controls),'enabled_unique':len(set(enabled)),'disabled':disabled,'planned_requests':len(planned),'batch_checks':checks,**counts,'errors':errors,'inert_source_preparation':provenance(),'browser':version,'network_requests_sent':0,'resource_requests_aborted':len(blocked),'scope':'Actual full independent source form/control and heading occurrence reconciliation plus all native browser table cells. Table multisets stay bound to their source batch, not a claim of correct section-body ownership. Whole body/link/edition/external-asset semantics remain separate.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':not errors,**counts,'errors':len(errors)}));return 0 if not errors else 2
if __name__=='__main__':raise SystemExit(main())
