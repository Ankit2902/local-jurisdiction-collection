"""Independent native UTF8 source form/heading scan; reuse prior bound table audit."""
import argparse,collections,hashlib,json
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from lxml import html

def sha(b):return hashlib.sha256(b).hexdigest()
def clean(s):return ' '.join(s.split())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--normalized',type=Path,required=True);ap.add_argument('--table-report',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh report required')
 cp=json.loads((a.source/'checkpoint.json').read_text());rep=json.loads((a.normalized/'replay.json').read_text());recordbytes=(a.normalized/'records.jsonl').read_bytes();rows=[json.loads(x) for x in recordbytes.splitlines()];groups=collections.defaultdict(list)
 for row in rows:groups[row['document_id']].append(row)
 table=json.loads(a.table_report.read_text());assert table['records_sha256']==sha(recordbytes);assert not any(e['kind']!='native_header_occurrence_vs_output' for e in table['errors']);assert table['network_requests_sent']==0
 tocraw=(a.source/cp['identity']['section_inventory_ref']).read_bytes();toc=html.fromstring(tocraw.decode('utf-8'));controls=toc.xpath('//form[@name="formSMC"]//input[@name="Section"]');labels=collections.defaultdict(set);enabled=[];disabled=[]
 for control in controls:
  ident=control.get('value').strip();tr=control.getparent()
  while tr is not None and tr.tag!='tr':tr=tr.getparent()
  anchors=tr.xpath('.//a[@href]');label=clean(''.join((anchors[0].getparent() if anchors else tr).itertext()));labels[ident].add(label);(disabled if 'disabled' in control.attrib else enabled).append(ident)
 inv=json.loads((a.source/'inventory.json').read_text());planned=[v.strip() for i in inv for k,v in i['post_fields'] if k=='Section'];errors=[];checks=[];headings=0
 if len(planned)!=len(set(planned)) or set(planned)!=set(enabled):errors.append({'kind':'raw_form_vs_planned_requests'})
 for batch in rep['batches']:
  raw=(a.source/batch['raw_ref']).read_bytes();assert sha(raw)==batch['raw_sha256'];scope=html.fromstring(raw.decode('utf-8')).get_element_by_id('hideRepealed');source=collections.Counter()
  for anchor in scope.xpath('.//a[@href]'):
   ident=parse_qs(urlparse(anchor.get('href')).query).get('Section',[''])[0].strip()
   if ident not in labels or clean(''.join(anchor.itertext()))!='Section '+ident:continue
   title=anchor.tail or '';n=anchor.getnext()
   while n is not None and n.tag in ['span','b','i','em','strong','sup','sub']:title+=''.join(n.itertext())+(n.tail or '');n=n.getnext()
   if n is not None and n.tag=='br' and 'Section '+ident+' '+clean(title) in labels[ident]:source[(ident,clean(title))]+=1
  output=collections.Counter((r.get('citation',r['id']),r['heading']) for r in groups[batch['item_id']] if r['unit'] in ['legal_section','legal_section_version'])
  if source!=output:errors.append({'kind':'source_header_vs_records','item':batch['item_id'],'missing':list((source-output).elements()),'extra':list((output-source).elements())})
  checks.append({'item':batch['item_id'],'source_sha256':batch['raw_sha256']});headings+=sum(source.values())
 status={r['id'] for r in rows if r['unit']=='legal_status' and r['id'] in disabled}
 if status!=set(disabled):errors.append({'kind':'disabled_status_missing'})
 prior=[{k:b[k] for k in ['item','source_sha256']} for b in table['batch_checks']];assert prior==checks
 report={'passed':not errors,'script_sha256':sha(Path(__file__).read_bytes()),'records_sha256':sha(recordbytes),'source_toc_sha256':sha(tocraw),'encoding':'Explicit UTF8, preserving native Unicode codepoints; prior lxml byte-input Latin1 inference was a QA error.','source_controls':len(controls),'enabled_unique_sections':len(set(enabled)),'disabled_source_status_units':disabled,'source_heading_occurrences':headings,'records':len(rows),'batches':len(checks),'errors':errors,'table_evidence':{'path':str(a.table_report),'sha256':sha(a.table_report.read_bytes()),'same_records_and_all68_source_hashes':True,'native_table_errors':0,'tables':table['tables'],'rows':table['rows'],'cells':table['cells'],'inert_source_preparation':table['inert_source_preparation']},'network_requests_sent':0,'scope':'Independent complete native form controls/heading occurrences and previously bound all-source browser table cells. Whole-body legal ownership, external assets and current-version choice for multiple source versions remain separate.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':not errors,'headings':headings,'records':len(rows),'batches':len(checks),'errors':len(errors)}));return 0 if not errors else 2
if __name__=='__main__':raise SystemExit(main())
