"""Terminal-only read-only raw/native generations, normalized streams, and source-byte bridge audit."""
import argparse,hashlib,json,re,csv,datetime,collections,sys
csv.field_size_limit(sys.maxsize)
from pathlib import Path
from bs4 import BeautifulSoup
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--proof',type=Path,required=True);p.add_argument('--prior',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();out=a.out.resolve();proof=a.proof.resolve();prior=a.prior.resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_text())
if a.receipt.exists():raise FileExistsError('Fresh external audit receipt required')
def tree(folder):return {str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
before=tree(out);terminal=load(proof/'terminal.json');state=load(out/'source/checkpoint.json');init=load(out/'source/inventory-initialization.json');initial=load(proof/'initial-terminal.json');rows=[json.loads(l) for l in (out/'normalized/records.jsonl').read_text().splitlines()];old=load(prior/'source/checkpoint.json');assert terminal['real_ordinary_chrome'] and terminal['recorded_fake_backend'] is False
mime=[];image_responses=[];generation_reports=[]
def inspect_body(base,row,ledger):
 rawpath=base/row['path'];digest=sha(rawpath)
 if digest!=row['sha256']:raise AssertionError('Raw source hash mismatch '+str(rawpath))
 ct=next((str(v) for k,v in row.get('headers',{}).items() if str(k).lower()=='content-type'),'');head=rawpath.open('rb').read(512).lstrip();magic=head.startswith((b'\x89PNG\r\n\x1a\n',b'GIF87a',b'GIF89a',b'\xff\xd8\xff')) or head.startswith(b'RIFF') and head[8:12]==b'WEBP' or bool(re.match(br'(?:<\?xml[^>]*>\s*)?<svg(?:\s|>)',head,re.I));item={'ledger':ledger,'role':row.get('role'),'started_at':row.get('started_at',row.get('captured_at')),'finished_at':row.get('finished_at'),'status':row.get('status'),'path':str(rawpath.relative_to(out)),'url':row.get('source_url',row.get('url')),'mime':ct,'bytes':rawpath.stat().st_size,'sha256':digest,'separate_image_mime_or_magic':ct.lower().startswith('image/') or magic};mime.append(item)
 if item['separate_image_mime_or_magic']:raise AssertionError('Separate image body acquired')
for row in state['artifacts']:inspect_body(out/'source',row,'source_checkpoint')
for attempt in init['attempts']:
 folder=out/'source'/attempt['path'];report={'path':attempt['path'],'status':attempt['status'],'files':len(tree(folder))}
 if attempt['status']=='interrupted_preserved':
  assert folder.exists()==attempt['directory_exists'] and tree(folder)==attempt['manifest']
  if attempt['path']==Path(initial['native_generation']).name:assert tree(folder)==initial['generation_after_shutdown']
 elif attempt['status']=='selected':assert tree(folder)==init['selected_manifest']
 else:raise AssertionError('Native generation still incomplete at terminal')
 for row in load(folder/'network-bodies.json'):
  if row.get('path'):inspect_body(folder,row,'native_generation:'+attempt['path'])
 for event in load(folder/'network-events.json'):
  if any(str(k).lower()=='content-type' and str(v).lower().startswith('image/') for k,v in event.get('headers',{}).items()):image_responses.append({'generation':attempt['path'],'event':event})
 generation_reports.append(report)
assert not image_responses
# Independent source-control projections from exact opening/resumed/closing bytes.
def projection(entry,root=False):
 soup=BeautifulSoup((out/'source'/entry['path']).read_bytes(),'html.parser');scope=soup.select_one('#divmuni') if root else soup
 if scope is None:raise AssertionError('Primary native root container absent')
 result=[]
 for node in scope.find_all('p',recursive=not root):
  box=node.select_one('input[name=code]');anchor=node.find('a',href=True)
  if not anchor or not root and not box:continue
  result.append({'value':box['value'] if box else anchor['href'],'href':anchor['href'],'id':anchor.get('id'),'label':' '.join(anchor.get_text(' ',strip=True).split())})
 return result
arts=state['artifacts'];reader_checks=[]
for reader in state['observed_readers']:
 triples=[]
 for phase in ['opening','resumed','closing']:
  choices=[r for r in arts if r['source_url']==reader['url'] and (r['role']=='toc-start' if phase=='opening' else r['role']=='toc-end' if phase=='closing' else r['role'].startswith('toc-resume-validation-'))]
  if len(choices)!=1:raise AssertionError('Missing or duplicate reader phase '+phase)
  triples.append(choices[0])
 projected=[projection(r) for r in triples]
 if not projected[0]==projected[1]==projected[2]:raise AssertionError('Opening/resumed/closing native reader controls differ')
 reader_checks.append({'source_url':reader['url'],'opening_sha256':triples[0]['sha256'],'resumed_sha256':triples[1]['sha256'],'closing_sha256':triples[2]['sha256'],'source_controls':len(projected[0]),'projections_equal':True})
roots=[]
for role in ['root-toc-start','root-resume-validation','root-toc-end']:
 choices=[r for r in arts if r['role']==role]
 if len(choices)!=1:raise AssertionError('Missing/duplicate native roots '+role)
 roots.append(projection(choices[0],True))
assert roots[0]==roots[1]==roots[2] and len(roots[0])==len(state['observed_readers'])
bad=[];count=0
for row in rows:
 html=row['semantic_html'];dom=BeautifulSoup(html,'html.parser')
 if dom.find(['img','picture','svg','image','object','embed','iframe','source']):bad.append({'record_id':row['record_id'],'kind':'active_visual_element'})
 for tag in dom.find_all(True):
  if any(str(k).lower() in ['src','srcset','poster','background','xlink:href'] for k in tag.attrs):bad.append({'record_id':row['record_id'],'kind':'active_image_source_attribute'})
 if dom.get_text().count('[IMAGE]')!=row['image_placeholder_count']:bad.append({'record_id':row['record_id'],'kind':'placeholder_count_differs'})
 count+=row['image_placeholder_count']
normalized_streams=[]
for path in sorted((out/'normalized').iterdir()):
 if path.is_file() and path.suffix in ['.json','.jsonl','.csv']:
  text=path.read_text()
  if re.search(r'data:image/|data:[^\s"<>]*;base64,',text,re.I):bad.append({'path':path.name,'kind':'inline_payload_in_normalized_stream'})
  normalized_streams.append({'path':str(path.relative_to(out)),'sha256':sha(path),'bytes':path.stat().st_size})
assert not bad
with (out/'normalized/records.csv').open(newline='') as stream:
 reader=csv.DictReader(stream);fields=reader.fieldnames;csvrows=list(reader)
assert len(csvrows)==len(rows) and all({k:str(row[k]) for k in fields}==crow for row,crow in zip(rows,csvrows))
prior_map={r['source_url']:r['sha256'] for r in old['artifacts'] if r['role']=='content'};content=[r for r in state['artifacts'] if r['role']=='content'];bridge=[{'source_url':r['source_url'],'sha256':r['sha256'],'prior_sha256':prior_map.get(r['source_url']),'same':r['sha256']==prior_map.get(r['source_url'])} for r in content];same_bodies=len(content)==len(prior_map)==len({r['source_url'] for r in content}) and all(r['same'] for r in bridge);same_records=sha(out/'normalized/records.jsonl')==sha(prior/'normalized/records.jsonl')
assert tree(out)==before
receipt={'schema':'originals-early-native-live-terminal-image-source-audit-1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'out':str(out),'controller_terminal_sha256':sha(proof/'terminal.json'),'native_generations':generation_reports,'phase_receipt_counts':dict(collections.Counter(r['role'] for r in arts)),'reader_opening_resumed_closing_checks':reader_checks,'native_root_projections_equal':True,'all_partial_and_selected_native_generations_checked':True,'raw_source_files_checked':len(mime),'raw_mime_ledger':mime,'separate_image_bodies':0,'native_browser_image_mime_response_events':0,'normalized_streams_checked':normalized_streams,'records':len(rows),'csv_rows_equal_json_projection':True,'record_sha256':sha(out/'normalized/records.jsonl'),'body_image_placeholders':count,'active_image_elements_source_attributes':0,'inline_pixel_payloads':0,'all_actual_body_raw_bytes_equal_prior':same_bodies,'all_actual_record_bytes_equal_prior':same_records,'prior':str(prior),'body_raw_bridge':bridge,'source_target_coverage':load(out/'normalized/source-target-coverage.json'),'source_broken_links':load(out/'normalized/source-link-defects.json'),'input_files_unchanged':True,'new_publisher_requests':0,'scope':'Read-only terminal actualbytes/native/browserresponse/allnormalizedstream image and source bridge. No image extraction, decode, render, OCR or network. Prior independent source scopes inherit only if all source/record hashes match.'};a.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k not in ['raw_mime_ledger','body_raw_bridge','source_target_coverage','source_broken_links']},indent=2))
