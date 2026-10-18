"""Independent finite native Word header/footer inventory, cached text and field audit.
Never reads ZIP media/OLE members or invokes Word/image rendering.
"""
import argparse,collections,hashlib,io,json,posixpath,socket,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
MC='{http://schemas.openxmlformats.org/markup-compatibility/2006}'
R='{http://schemas.openxmlformats.org/package/2006/relationships}'
def sha(b):return hashlib.sha256(b).hexdigest()
def clean(v):return ' '.join(v.split())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--normalized',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh report required')
 rb=(a.normalized/'records.jsonl').read_bytes();allrows=[json.loads(x) for x in rb.split(b'\n') if x.strip()];rows=[r for r in allrows if r['kind'] in ('source_header','source_footer')];bykey={(r['source_url'],r['source_part']):r for r in rows};assert len(bykey)==len(rows)
 cpraw=(a.source/'checkpoint.json').read_bytes();cp=json.loads(cpraw);checks=[];parts=[];opened=[];images=0
 def check(name,ok):checks.append({'name':name,'passed':bool(ok)})
 def text(n):
  nonlocal images
  tag=n.tag.removeprefix(W)
  if tag in ('drawing','pict','object'):images+=1;return '[IMAGE]'
  if n.tag==MC+'AlternateContent':
   choices=n.findall(MC+'Choice');selected=choices[0] if choices else n.find(MC+'Fallback');return text(selected) if selected is not None else ''
  if tag=='t':return n.text or ''
  if tag=='tab':return '\t'
  if tag in ('br','cr'):return '\n'
  if tag=='noBreakHyphen':return '\u2011'
  if tag=='softHyphen':return '\u00ad'
  if tag=='sym':return '[SYMBOL '+str(n.get(W+'char'))+']'
  value=''.join(text(c) for c in n)
  return value+('\n' if tag in ('p','tr','tc') else '')
 def deny(*args,**kwargs):raise AssertionError('No network')
 seen=set()
 with patch.object(socket.socket,'connect',deny),patch.object(socket,'create_connection',deny):
  for item in cp['artifacts']:
   if item['role']!='native-word':continue
   raw=(a.source/item['path']).read_bytes();check('native_'+item['sha256'],sha(raw)==item['sha256'])
   with zipfile.ZipFile(io.BytesIO(raw)) as z:
    relpath='word/_rels/document.xml.rels'
    if relpath not in z.namelist():continue
    relbytes=z.read(relpath);opened.append({'native_sha256':item['sha256'],'member':relpath,'sha256':sha(relbytes)})
    observed={}
    for rel in ET.fromstring(relbytes):
     kind=rel.get('Type','').rsplit('/',1)[-1]
     if kind not in ('header','footer'):continue
     if rel.get('TargetMode')=='External':raise ValueError('External header/footer unexpected')
     target=rel.get('Target','');member=target.lstrip('/') if target.startswith('/') else posixpath.normpath('word/'+target)
     if not member.startswith('word/') or '..' in member.split('/') or not member.endswith('.xml'):raise ValueError('Unqualified ancillary path')
     observed[member]=kind
    for member,kind in observed.items():
     rawxml=z.read(member);root=ET.fromstring(rawxml);opened.append({'native_sha256':item['sha256'],'member':member,'sha256':sha(rawxml)})
     key=(item['source_url'],member);seen.add(key);r=bykey.get(key);check(member+'_owned_'+item['sha256'],r is not None)
     if r is None:continue
     expected=clean(text(root));instructions=[n.text or '' for n in root.iter(W+'instrText')];xsha=sha(ET.tostring(root))
     check(member+'_kind_'+item['sha256'],r['kind']=='source_'+kind)
     check(member+'_xml_'+item['sha256'],xsha==r['source_xml_sha256'])
     check(member+'_native_'+item['sha256'],r['source_native_sha256']==item['sha256'])
     check(member+'_text_'+item['sha256'],expected==clean(r['text']))
     check(member+'_fields_'+item['sha256'],instructions==r.get('field_instructions',[]))
     check(member+'_not_currency_'+item['sha256'],'not a publication currency/effective-date assertion' in r.get('source_part_role',''))
     parts.append({'native_sha256':item['sha256'],'source_url':item['source_url'],'member':member,'source_xml_sha256':xsha,'original_text':expected,'normalized_text':r['text'],'field_instructions':instructions,'image_placeholders':expected.count('[IMAGE]')})
 check('exact_ancillary_record_set',seen==set(bykey));check('seven_source_parts',len(parts)==7);check('one_ancillary_image_placeholder',images==1)
 check('source_and_output_unchanged',rb==(a.normalized/'records.jsonl').read_bytes() and cpraw==(a.source/'checkpoint.json').read_bytes())
 report={'passed':all(c['passed'] for c in checks),'checks':checks,'check_count':len(checks),'records_sha256':sha(rb),'source_checkpoint_sha256':sha(cpraw),'script_sha256':sha(Path(__file__).read_bytes()),'source_parts':parts,'members_opened':opened,'image_ole_members_read':0,'network_requests_sent':0,'no_separate_image_download_decode_render_extract_or_OCR':True,'scope':'Exact seven source-owned cached native header/footer parts, relationship-derived ownership, original XML hash, literal text/field instructions and one IMAGE. Not publication currency/effective date. Earlier body/table/glyph audits remain separate; King date/private-symbol/required-reference gaps remain.'};a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'checks':len(checks),'failures':[x['name'] for x in checks if not x['passed']]}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
