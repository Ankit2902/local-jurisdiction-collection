"""Adjudicate exact native image-bearing heading metadata after a full DOM audit."""
import argparse,hashlib,json,re
from pathlib import Path
from lxml import html
from bs4 import BeautifulSoup
from urllib.parse import urldefrag

def sha(b):return hashlib.sha256(b).hexdigest()
def clean(t):return ' '.join(t.split())
def native_heading(n):return (n.text or '')+''.join((' ' if c.tag=='br' else native_heading(c))+(c.tail or '') for c in n)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--normalized',type=Path,required=True);ap.add_argument('--browser-report',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh report required')
 auditraw=a.browser_report.read_bytes();audit=json.loads(auditraw);cpraw=(a.source/'checkpoint.json').read_bytes();cp=json.loads(cpraw);rr=(a.normalized/'records.jsonl').read_bytes();records={r['record_id']:r for r in (json.loads(x) for x in rr.split(b'\n') if x.strip())};rows=[];errors=[]
 assert sha(rr)==audit['records_sha256'] and sha(cpraw)==audit['source_checkpoint_sha256'];assert not audit['body_text_mismatches']
 for e in audit['errors']:
  if e['kind']!='source_heading_metadata_or_boundary':raise ValueError('Unexpected nonheading issue requires separate audit')
  item=next(r for r in cp['artifacts'] if r['role']=='content' and r['source_url']==e['url']);raw=(a.source/item['path']).read_bytes();assert sha(raw)==item['sha256'];doc=html.fromstring(raw,parser=html.HTMLParser(encoding='utf-8'));record=records[e['owner']]
  heads=[n for n in doc.xpath('//*[@id="mainContent"]//*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6 or (self::p and contains(concat(" ",normalize-space(@class)," ")," Division "))]') if clean(native_heading(n))==record['heading']]
  qualified=len(heads)==1 and len(heads[0].xpath('.//img'))==1 and e['source']==record['heading']+'[IMAGE]' and record['block_indices'][0]==e['block']
  semantic=BeautifulSoup(record['semantic_html'],'html.parser');first=semantic.find(['h1','h2','h3','h4','h5','h6','p']);qualified=qualified and first is not None and clean(native_heading(html.fromstring(str(first))))==e['source'] and not semantic.find(['img','svg','picture'])
  if not qualified:errors.append(e)
  rows.append({'source_url':e['url'],'source_raw_sha256':item['sha256'],'record_id':record['record_id'],'block_index':e['block'],'native_literal_heading':record['heading'],'normalized_heading_with_intentional_image':e['source'],'original_heading_fragment_sha256':sha(html.tostring(heads[0])) if len(heads)==1 else None,'passed':qualified,'disposition':'Native textual heading metadata retains literal words; the same original heading has one image whose exact[IMAGE] marker is retained in normalized semanticHTML/fulltext.'})
 report={'passed':not errors,'script_sha256':sha(Path(__file__).read_bytes()),'source_checkpoint_sha256':sha(cpraw),'records_sha256':sha(rr),'full_browser_report':str(a.browser_report),'full_browser_report_sha256':sha(auditraw),'source_documents':len(audit['documents']),'records':audit['records'],'source_blocks':audit['source_blocks'],'substantive_source_headings':audit['substantive_source_headings'],'tables':audit['tables'],'rows':audit['rows'],'cells':audit['cells'],'exact_heading_image_dispositions':rows,'errors':errors,'network_requests_sent':0,'source_image_resources_opened':0,'scope':'Complete native body/block/table/browser comparison plus exact source-bound heading-image metadata adjudication. Every source heading boundary and literal label is retained;14image markers remaininsemanticHTML/fulltext. No general removal of literal[IMAGE] text or pixels.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['passed','source_documents','records','source_blocks','substantive_source_headings','tables','rows','cells','errors']}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
