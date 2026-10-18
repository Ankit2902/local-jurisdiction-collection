"""Full retained native Word import; complete XML ownership without opening image members."""
import argparse,json,re,sys
from pathlib import Path
from source_common import *
from king_acquire import inventory,URL
from king_normalize import datevalue
from word_model import inspect
from model import redact_image_metadata

def run(source,out):
 src=Path(source).resolve();out=Path(out).resolve()
 if out.exists() and any(out.iterdir()):raise ValueError('Fresh Word normalization output required')
 out.mkdir(parents=True,exist_ok=True);s=load(src/'checkpoint.json');errors=[];art=s['artifacts'];start=next((a for a in art if a['role']=='index-start'),None);end=next((a for a in art if a['role']=='index-end'),None)
 for a in art:
  if sha((src/a['path']).read_bytes())!=a['sha256']:raise ValueError('Corrupt original Word acquisition '+a['path'])
 if not start or not end:raise ValueError('Native opening/closing source receipts required')
 docs=inventory((src/start['path']).read_bytes());closing=inventory((src/end['path']).read_bytes())
 if docs!=closing:errors.append('Native opening/closing inventory mismatch')
 records=[];reports=[];relationships=[]
 for d in docs:
  matches=[a for a in art if a['role']=='native-word' and a.get('document_id')==d['id'] and a['status']==200]
  if len(matches)!=1:errors.append('Missing/duplicate native document '+d['id']);continue
  a=matches[0];raw=(src/a['path']).read_bytes();word=inspect(raw)
  if d['kind']=='title':
   title=re.match(r'Title\s+(\d+[A-Z]?)',d['heading'],re.I).group(1)
   if not re.search(r'\bTitle\s+'+re.escape(title)+r'(?![A-Z0-9])',word['text'][:2500],re.I):errors.append('Wrong native title identity '+d['id'])
  conflict=bool(word['updated_markers'] and datevalue(d['updated']) not in [datevalue(x) for x in word['updated_markers']])
  if conflict:errors.append('Index/native updated-date conflict '+d['id'])
  if word['missing_notes']:errors.append('Missing native note bodies '+d['id'])
  if word['tracked_change_elements']:errors.append('Unresolved native tracked changes '+d['id'])
  for u in word['units']:
   record=dict(u,record_id=sha((d['url']+'::word-unit-'+str(u['source_ordinal'])).encode()),source_document_id=d['id'],source_url=a['source_url'],source_native_sha256=sha(raw),document_heading=d['heading'],jurisdiction='King County, WA',publication='Charter' if d['kind']=='charter' else 'King County Code');records.append(record)
  for note in word['notes']:records.append(dict(note,record_id=sha((d['url']+'::word-'+note['kind']+'-'+str(note['source_id'])).encode()),source_document_id=d['id'],source_url=a['source_url'],source_native_sha256=sha(raw),document_heading=d['heading'],jurisdiction='King County, WA',publication='Charter' if d['kind']=='charter' else 'King County Code',kind=note['kind']))
  for rel in word['relationships']:
   relationships.append(dict(rel,source_document_id=d['id']))
   if rel['required'] and rel['status']=='unresolved_nonimage_dependency':errors.append('Unresolved native nonimage dependency '+d['id']+' '+rel['target'])
  reports.append({'document_id':d['id'],'heading':d['heading'],'native_url':a['source_url'],'native_sha256':sha(raw),'owned_units':len(word['units']),'owned_notes':len(word['notes']),'tables':word['tables'],'image_placeholders':word['image_placeholder_count'],'source_index_updated':d['updated'],'body_updated':word['updated_markers'],'edition_conflict':conflict,'missing_notes':word['missing_notes'],'tracked_changes':word['tracked_change_elements'],'members_read':word['members_read'],'image_members_never_read':word['image_members_never_read'],'image_member_names_omitted':word['image_member_names_omitted']})
 transport.atomic(out/'records.jsonl',b''.join(canon(redact_image_metadata(r))+b'\n' for r in records));save(out/'document-audits.json',reports);save(out/'relationships.json',relationships)
 summary={'schema':'king-native-word-full-import-1','source':str(src),'complete':not errors and not s['errors'],'publication_body_complete':len(reports)==len(docs) and not any('Missing' in e or 'Wrong' in e or 'tracked' in e for e in errors),'edition_complete':not any('updated-date' in e for e in errors),'attachments_complete':not any('dependency' in e for e in errors),'whole_jurisdiction_complete':False,'source_documents':len(docs),'imported_documents':len(reports),'records':len(records),'owned_units':sum(r['owned_units'] for r in reports),'owned_notes':sum(r['owned_notes'] for r in reports),'tables':sum(r['tables'] for r in reports),'image_placeholders':sum(r['image_placeholders'] for r in reports),'image_members_never_read':all(r['image_members_never_read'] for r in reports),'images_extracted':False,'opening_closing_inventory_equal':docs==closing,'errors':sorted(set(errors)),'code_fingerprint':{n:sha((Path(__file__).parent/n).read_bytes()) for n in ['king_word_import.py','word_model.py','king_acquire.py','king_normalize.py','source_common.py','shared_transport.py','model.py','legacy_html.py']}};save(out/'summary.json',summary);return summary
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=run(a.source,a.out);print(json.dumps(r,indent=2));sys.exit(0 if r['complete'] else 2)
