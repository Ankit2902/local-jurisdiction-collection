import sys
sys.dont_write_bytecode=True
import json,hashlib,re,collections
from pathlib import Path
from bs4 import BeautifulSoup
B=Path(__file__).resolve().parent;S=Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00/github/local-jurisdiction-collection/packages/collection-source-recovery-2026-10-18/ecode/corrected-corpus-v3/evidence/input');old=json.loads((B/'original-review-ledger.json').read_text());rawcache={};counter=collections.Counter();records=[];errata=[]
for index,row in enumerate(old['records']):
 path=row['raw_path'];data=(S/path).read_bytes();assert hashlib.sha256(data).hexdigest()==row['raw_sha256'];s=rawcache.setdefault(path,BeautifulSoup(data,'html.parser'));roots=s.find_all(id=row['owner_id']+'_content');assert len(roots)==1;root=roots[0];matches=[]
 for a in root.find_all('a',href=True):
  nearest=next((p for p in a.parents if p.get('id') and re.fullmatch(r'[0-9]+_content',p['id'])),None)
  if nearest is root and a['href']==row['url'] and a.get_text(' ',strip=True)==row['label']:matches.append(a)
 key=(row['owner_id'],path,row['url'],row['label']);occ=counter[key];counter[key]+=1;assert occ<len(matches);a=matches[occ];context=a.find_parent(['p','li','dd','td','div']) or a.parent;actual=context.get_text(' ',strip=True);record={**row,'source_parent_context':actual,'source_anchor':str(a),'owner_URL_label_occurrence_ordinal':occ,'same_owner_URL_label_total_occurrences':len(matches),'raw_anchor_sourceline':a.sourceline,'raw_anchor_sourcepos':a.sourcepos,'source_context_html_sha256':hashlib.sha256(str(context).encode()).hexdigest(),'source_anchor_html_sha256':hashlib.sha256(str(a).encode()).hexdigest(),'source_classification':'external statutory citation, law not acquired','source_classes':a.get('class',[])}
 if actual!=row['source_parent_context']:errata.append({'ledger_index':index,'owner_id':row['owner_id'],'url':row['url'],'occurrence_ordinal':occ,'previous_context':row['source_parent_context'],'correct_context':actual,'impact':'Corrects source-review witness only; runtime link_refs walks every source anchor and did not use this ledger.'})
 records.append(record)
assert len(records)==21 and len(errata)==3
out={'unresolved_occurrences':21,'unique_URLs':18,'records':records,'source_review_errata':errata,'supersedes_context_pins':'original-review-ledger and source-anchor-and-four-PDF-audit repeated first context for three duplicateownerURL references; originals retained immutable','source_byte_changes':0,'publisher_requests':0};(B/'corrected-statref-source-census.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'occurrences':len(records),'unique_urls':18,'corrected_review_contexts':len(errata)}))
