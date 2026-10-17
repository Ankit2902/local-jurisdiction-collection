#!/usr/bin/env python3
"""Network-free, source-preserving deterministic verification; writes only temporary outputs."""
import pathlib,json,tempfile,sys,csv
from parse import inventory,decode,parse_section,write_outputs,sha
from acquire import CONFIG
from pdf_qa import check
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 receipts=0;snapshots=0
 for p in sorted(ROOT.rglob('*.receipt.json')):
  if '.venv' in p.parts:continue
  m=json.loads(p.read_text());raw=p.with_name(p.name[:-len('.receipt.json')]);assert raw.exists(),str(p);assert sha(raw.read_bytes())==m['sha256'],str(raw);receipts+=1
 for p in ROOT.rglob('script-versions/*'):
  if p.is_file():assert p.stem==sha(p.read_bytes()),str(p);snapshots+=1
 rows=json.loads((ROOT/'results.json').read_text());assert [r['sequence'] for r in rows]==[67,82];report=[]
 for key,cfg in CONFIG.items():
  folder=ROOT/'live'/(key+'-v2');m=json.loads((folder/'toc.html.receipt.json').read_text());inv=inventory(decode((folder/'toc.html').read_bytes(),m['headers']),cfg['base'],cfg['identity']);assert inv==json.loads((folder/'inventory.json').read_text());nodes={n['section_id']:n for n in inv['nodes']};records=[];checks=[]
  for ident in cfg['nodes']:
   raw=folder/('section-'+ident+'.html');m=json.loads(raw.with_name(raw.name+'.receipt.json').read_text());r,c,_=parse_section(decode(raw.read_bytes(),m['headers']),nodes[ident],m['url'],cfg['jurisdiction'],m['sha256']);records.append(r);checks.append(c)
  with tempfile.TemporaryDirectory(prefix='encodeplus-replay-') as td:
   parsed=write_outputs(records,checks,pathlib.Path(td));assert parsed['outputs_sha256']==json.loads((folder/'run.json').read_text())['outputs_sha256']
   for name in ['sections.jsonl','sections.csv']:assert (pathlib.Path(td)/name).read_bytes()==(folder/'normalized'/name).read_bytes()
  native=ROOT/'native'/(key+'-qualified');pdf=check(key,native);assert pdf==json.loads((native/'qa.json').read_text());row=rows[0 if key=='lincoln' else 1];assert row['record_count']==len(records) and row['table_count']==parsed['table_count'];assert row['publisher_download']['status']=='passed'
  for path in row['evidence_paths']+row['script_paths']:assert not pathlib.Path(path).is_absolute() and (ROOT/path).exists(),path
  report.append({'jurisdiction':cfg['jurisdiction'],'record_count':len(records),'table_count':parsed['table_count'],'table_cells':sum(t['cells'] for c in checks for t in c['table_checks']),'inventory_nodes':inv['node_count'],'hierarchy_anomalies':len(inv['hierarchy_anomalies']),'normalized_bytes_match':True,'native_pdf_pages':pdf['page_count'],'native_pdf_identity_table_anchors_match':True})
 if (ROOT/'MANIFEST.sha256').exists():
  for line in (ROOT/'MANIFEST.sha256').read_text().splitlines():
   digest,relative=line.split('  ',1);assert sha((ROOT/relative).read_bytes())==digest,relative
 print(json.dumps({'status':'passed','read_only':True,'network_used':False,'raw_receipts_verified':receipts,'script_snapshots_verified':snapshots,'targets':report},indent=2))
if __name__=='__main__':main()
