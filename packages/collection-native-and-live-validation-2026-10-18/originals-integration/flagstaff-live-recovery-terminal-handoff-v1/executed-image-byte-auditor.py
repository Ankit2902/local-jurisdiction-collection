"""Read-only terminal raw MIME, normalized image, and prior source-byte bridge audit. No network/render/OCR."""
import argparse,datetime,hashlib,json,re
from pathlib import Path
from bs4 import BeautifulSoup
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--prior',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();out=a.out.resolve();prior=a.prior.resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_text())
if a.receipt.exists():raise FileExistsError('Fresh audit receipt required')
def snapshot(d):return {str(p.relative_to(d)):sha(p) for p in d.rglob('*') if p.is_file()}
before=snapshot(out);state=load(out/'source/checkpoint.json');priorstate=load(prior/'source/checkpoint.json');rows=[json.loads(l) for l in (out/'normalized/records.jsonl').read_text().splitlines()];mime=[];image_bodies=[]
artifacts=[(out/'source',r,'source_checkpoint') for r in state['artifacts']]+[(out/'source/inventory-origin',r,'native_inventory') for r in load(out/'source/inventory-origin/network-bodies.json') if r.get('path')]
for root,r,kind in artifacts:
 body=root/r['path'];digest=sha(body)
 if digest!=r['sha256']:raise AssertionError('Corrupt retained raw source')
 headers={k.lower():str(v) for k,v in r.get('headers',{}).items()};ct=headers.get('content-type','');head=body.read_bytes()[:512].lstrip();magic=head.startswith((b'\x89PNG\r\n\x1a\n',b'GIF87a',b'GIF89a',b'\xff\xd8\xff')) or head.startswith(b'RIFF') and head[8:12]==b'WEBP' or bool(re.match(br'(?:<\?xml[^>]*>\s*)?<svg(?:\s|>)',head,re.I))
 item={'ledger':kind,'path':str(body.relative_to(out)),'url':r.get('source_url',r.get('url')),'mime':ct,'bytes':body.stat().st_size,'sha256':digest,'separate_image_mime_or_magic':ct.lower().startswith('image/') or magic};mime.append(item)
 if item['separate_image_mime_or_magic']:image_bodies.append(item)
assert not image_bodies
image_responses=[event for event in load(out/'source/inventory-origin/network-events.json') if any(str(k).lower()=='content-type' and str(v).lower().startswith('image/') for k,v in event.get('headers',{}).items())]
assert not image_responses
bad=[];placeholder_fields=0;placeholder_html=0
for row in rows:
 delivered=json.dumps(row,ensure_ascii=False)
 if re.search(r'data:image/|data:[^\s"<>]*;base64,',delivered,re.I):bad.append({'record_id':row['record_id'],'kind':'inline_payload_in_delivered_record'})
 html=row.get('semantic_html','');dom=BeautifulSoup(html,'html.parser')
 if dom.find(['img','picture','svg','image','object','embed','iframe','source']):bad.append({'record_id':row['record_id'],'kind':'active_visual_element'})
 for tag in dom.find_all(True):
  if any(k.lower() in ['src','srcset','poster','background','xlink:href'] for k in tag.attrs):bad.append({'record_id':row['record_id'],'kind':'active_image_source_attribute'})
 placeholder_fields+=row['image_placeholder_count'];placeholder_html+=dom.get_text().count('[IMAGE]')
assert not bad and placeholder_fields==placeholder_html
content=[r for r in state['artifacts'] if r['role']=='content'];old={r['source_url']:r['sha256'] for r in priorstate['artifacts'] if r['role']=='content'};bridge=[{'source_url':r['source_url'],'sha256':r['sha256'],'prior_sha256':old.get(r['source_url']),'same':old.get(r['source_url'])==r['sha256']} for r in content];allmatch=len(content)==len(old)==len({r['source_url'] for r in content}) and all(r['same'] for r in bridge);same_records=sha(out/'normalized/records.jsonl')==sha(prior/'normalized/records.jsonl')
assert snapshot(out)==before
receipt={'schema':'originals-live-terminal-image-and-byte-bridge-audit-1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'raw_source_files_checked':len(mime),'raw_mime_ledger':mime,'separate_image_bodies':0,'native_browser_image_mime_response_events':len(image_responses),'normalized_records':len(rows),'normalized_records_sha256':sha(out/'normalized/records.jsonl'),'normalized_body_image_placeholders':placeholder_fields,'nested_record_note_link_asset_pixel_metadata_checked':True,'active_image_elements_or_source_attributes':0,'inline_pixel_payloads':0,'all_actual_body_raw_bytes_equal_prior':allmatch,'all_actual_record_bytes_equal_prior':same_records,'prior':str(prior),'body_raw_bridge':bridge,'source_broken_links':load(out/'normalized/source-link-defects.json'),'input_files_unchanged':True,'new_source_requests':0,'scope':'Read-only current terminal raw/normalized image audit and exact byte bridge. No render, OCR, image decode or source mutation; bridge is false if publisher source changed and must not inherit independent source dimensions in that case.'};a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k not in ['raw_mime_ledger','body_raw_bridge','source_broken_links']},indent=2))
