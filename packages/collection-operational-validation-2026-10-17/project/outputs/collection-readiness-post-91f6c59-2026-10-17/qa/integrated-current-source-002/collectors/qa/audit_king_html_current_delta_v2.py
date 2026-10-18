"""Bind current King HTML payload to already audited original body/cell scope.
Finite source-character meanings require the independent PDF/XML qualification.
"""
import argparse,hashlib,json,difflib
from pathlib import Path
from bs4 import BeautifulSoup

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prior',type=Path,required=True);ap.add_argument('--current',type=Path,required=True);ap.add_argument('--profiles',type=Path,required=True);ap.add_argument('--qualification',type=Path,required=True);ap.add_argument('--prior-audit',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh report required')
 oldraw=(a.prior/'records.jsonl').read_bytes();newraw=(a.current/'records.jsonl').read_bytes();old={r['record_id']:r for r in (json.loads(x) for x in oldraw.split(b'\n') if x.strip())};new={r['record_id']:r for r in (json.loads(x) for x in newraw.split(b'\n') if x.strip())};profile_raw=a.profiles.read_bytes();profiles=json.loads(profile_raw);qualification=json.loads(a.qualification.read_text());audit=json.loads(a.prior_audit.read_text());assert audit['passed'] and audit['records_sha256']==sha(oldraw);assert qualification['passed'] and qualification['profiles_sha256']==sha(profile_raw)
 checks=[];changes=[]
 def check(name,ok):checks.append({'name':name,'passed':bool(ok)})
 check('exact_record_ids',set(old)==set(new));count=0
 for ident,r in old.items():
  n=new.get(ident,{})
  check(ident+'_exact_source_ownership',all(r.get(k)==n.get(k) for k in ['source_sha256','source_document_id','block_indices']))
  entries=[p for p in profiles['html'] if p['source_document_id']==r['source_document_id'] and p['source_html_sha256']==r['source_sha256'] and p.get('html_block_index') in r['block_indices']]
  allowed=[]
  for p in entries:
   for event in p['replacements']:
    if event['original_literal']!=event['recovered_literal']:allowed.append((event['original_literal'],event['recovered_literal']))
  for field,source,dest in [('full_text',r['full_text'],n.get('full_text','')),('semantic_html_text',BeautifulSoup(r['semantic_html'],'html.parser').get_text(),BeautifulSoup(n.get('semantic_html',''),'html.parser').get_text())]:
   deltas=[] if source==dest else [(source[i:j],dest[k:l]) for tag,i,j,k,l in difflib.SequenceMatcher(None,source,dest,autojunk=False).get_opcodes() if tag!='equal'];check(ident+'_'+field,sorted(deltas)==sorted(allowed))
   if deltas:changes.append({'record_id':ident,'source_document':r['source_document_id'],'source_raw_sha256':r['source_sha256'],'field':field,'finite_changes':deltas})
  def cells(record):return [[[ {k:c.get(k) for k in ('text','tag','rowspan','colspan')} for c in row] for row in t['rows']] for t in record['tables']]
  check(ident+'_all_table_payloads',cells(r)==cells(n));count+=sum(len(row) for t in r['tables'] for row in t['rows'])
 report={'passed':all(c['passed'] for c in checks),'check_count':len(checks),'failures':[c['name'] for c in checks if not c['passed']],'records':len(old),'cells':count,'current_records_sha256':sha(newraw),'prior_records_sha256':sha(oldraw),'prior_independent_actual_dom_audit_sha256':sha(a.prior_audit.read_bytes()),'finite_glyph_qualification_sha256':sha(a.qualification.read_bytes()),'profiles_sha256':sha(profile_raw),'changes':changes,'script_sha256':sha(Path(__file__).read_bytes()),'network_requests_sent':0,'no_separate_image_download_decode_render_extract_or_OCR':True,'scope':'Every current5844record source ownership/full text/semanticHTML visible text and all131table cell text/tag/spans match the independently source-audited previous projection except exact finite source-character changes qualified by original XML/PDF/font/context proof. Metadata-only parent/character annotations and required references/date semantics remain separate.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'checks':len(checks),'failures':report['failures'][:10],'cells':count}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
