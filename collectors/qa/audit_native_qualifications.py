"""Bind exact native configs to literal publisher anchors and retained file receipts."""
import argparse,hashlib,json
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pypdf import PdfReader

def sha(b):return hashlib.sha256(b).hexdigest()
def audit(project,index):
 rows=[]
 for r in json.loads(index.read_text())['rows']:
  cfgpath=project/'github/local-jurisdiction-collection'/r['config'];cfgbytes=cfgpath.read_bytes();cfg=json.loads(cfgbytes);errors=[]
  if sha(cfgbytes)!=r['config_sha256'] or cfg['id']!=r['id'] or cfg['url']!=r['url'] or cfg['expected_sha256']!=r['expected_sha256'] or cfg['expected_pages']!=r['expected_pages']:errors.append('configuration mismatch')
  data=(project/r['native_bytes']).read_bytes();receiptbytes=(project/r['native_receipt']).read_bytes();receipt=json.loads(receiptbytes)
  if sha(data)!=cfg['expected_sha256'] or sha(receiptbytes)!=r['native_receipt_sha256'] or receipt['sha256']!=sha(data) or receipt['url']!=cfg['url'] or receipt.get('status',receipt.get('http_status'))!=200:errors.append('native bytes/receipt mismatch')
  pdf=PdfReader(project/r['native_bytes'],strict=True)
  if pdf.is_encrypted or len(pdf.pages)!=cfg['expected_pages']:errors.append('native physical page count mismatch')
  witnesses=[]
  for w in r['source_anchor_witnesses']:
   if any(v['path']==w['raw_path'] for v in witnesses):continue
   raw=(project/w['raw_path']).read_bytes();rec=json.loads((project/w['receipt']).read_text());base=rec.get('url') or rec.get('request_url')
   if sha(raw)!=w['raw_sha256'] or rec['sha256']!=sha(raw) or rec.get('status',rec.get('http_status'))!=200:errors.append('anchor raw receipt mismatch')
   soup=BeautifulSoup(raw,'html.parser');anchors=[a for a in soup.select('a[href]') if urljoin(base,a['href'])==cfg['url']]
   # Alternate old alias-relative anchors are retained as nonqualifying evidence.
   # At least one current exact absolute/receipt-base anchor must qualify.
   witnesses.append({'path':w['raw_path'],'sha256':sha(raw),'source_url':base,'matching_anchor_count':len(anchors),'labels':[' '.join(a.stripped_strings) for a in anchors]})
  if not any(w['matching_anchor_count'] for w in witnesses):errors.append('No exact publisher anchor binds selected native URL')
  rows.append({'id':r['id'],'config':r['config'],'config_sha256':sha(cfgbytes),'source_url':cfg['url'],'physical_pages':len(pdf.pages),'native_sha256':sha(data),'anchor_witnesses':witnesses,'configuration_dispatch_qualified':not errors,'legal_semantic_coverage_complete':False,'native_all_page_capture_tested_by_this_audit':False,'errors':errors})
 return {'schema_version':1,'kind':'independent-native-config-source-anchor-and-byte-qualification','script_sha256':sha(Path(__file__).read_bytes()),'source_index_sha256':sha(index.read_bytes()),'rows':rows,'network_requests':0,'image_extraction_or_decoding':False,'passed':all(r['configuration_dispatch_qualified'] for r in rows),'limits':['Exact original native file configuration/physical page count only; not section segmentation, table semantics, full page-content traversal, current edition completeness, or legal-semantic equivalence.']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--index',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise SystemExit('Fresh output required')
 r=audit(a.project,a.index);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'rows':[(x['id'],x['physical_pages'],x['errors']) for x in r['rows']]}));raise SystemExit(0 if r['passed'] else 2)
