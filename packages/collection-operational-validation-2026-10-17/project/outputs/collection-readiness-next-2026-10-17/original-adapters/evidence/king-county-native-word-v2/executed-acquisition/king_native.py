"""Acquire source-listed native Word alternatives to resolve source edition/HTML discrepancies."""
import argparse,sys,zipfile,io,re,xml.etree.ElementTree as ET
from pathlib import Path
from source_common import *
from king_acquire import URL,inventory

def run(source,out):
 src=Path(source);out=Path(out).resolve()
 if out.exists() and any(out.iterdir()):raise ValueError('Fresh native output required')
 out.mkdir(parents=True,exist_ok=True);base=load(src/'checkpoint.json');state={'schema':'king-native-alternatives-1','started_at':stamp(),'source_inventory_sha256':base['inventory_sha256'],'provenance_source':str(src.resolve()),'artifacts':[],'errors':[],'code_fingerprint':source_snapshot(out,['king_native.py','king_acquire.py','source_common.py','shared_transport.py'])};save(out/'checkpoint.json',state)
 try:
  raw,a=acquire(out,state,'index-start',URL)
  if inventory(raw)!=base['inventory']:raise ValueError('Original/native opening inventory differs')
  for d in base['inventory']:
   choices=[x for x in d['native_alternatives'] if x['url'].lower().endswith('.docx')]
   if len(choices)!=1:raise ValueError('Native Word alternative absent/nonunique '+d['url'])
   raw,a=acquire(out,state,'native-word',choices[0]['url']);a['document_id']=d['id'];a['index_updated']=d['updated'];a['heading']=d['heading'];save(out/'checkpoint.json',state)
   with zipfile.ZipFile(io.BytesIO(raw)) as z:
    if z.testzip():raise ValueError('Native Word archive CRC failed')
    xml=z.read('word/document.xml');tree=ET.fromstring(xml);ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};paragraphs=[clean(''.join(x.itertext())) for x in tree.findall('.//w:p',ns)];a['body_updated_markers']=[p for p in paragraphs if p.upper().startswith('UPDATED')];a['native_xml_sha256']=sha(xml);a['native_table_count']=len(tree.findall('.//w:tbl',ns))
   save(out/'checkpoint.json',state);print(json.dumps({'heading':d['heading'],'bytes':len(raw),'updated':a['body_updated_markers']}),flush=True)
  raw,a=acquire(out,state,'index-end',URL)
  state['opening_closing_equal']=inventory(raw)==base['inventory']
 except Exception as e:state['errors'].append({'type':type(e).__name__,'message':str(e),'at':stamp()})
 state.update(finished_at=stamp(),complete=False,scope='Native publisher alternatives, independent HTML/body reconciliation still required');save(out/'checkpoint.json',state);return state
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=run(a.source,a.out);print(json.dumps({'native_documents':sum(x['role']=='native-word' for x in r['artifacts']),'errors':r['errors']}));sys.exit(3 if r['errors'] else 0)
