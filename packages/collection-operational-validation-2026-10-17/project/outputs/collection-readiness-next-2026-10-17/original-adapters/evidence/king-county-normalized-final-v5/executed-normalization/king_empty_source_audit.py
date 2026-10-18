"""Source-bound empty Charter own-body corroboration; no legal-status inference, images never extracted."""
import argparse,io,re,sys
from pathlib import Path
from bs4 import BeautifulSoup
from pypdf import PdfReader
from source_common import *
from king_normalize import parse
from word_model import inspect

def run(html_source,word_source,pdf_source,out):
 h=Path(html_source);w=Path(word_source);p=Path(pdf_source);out=Path(out)
 if out.exists():raise ValueError('Fresh audit output required')
 profile=load(Path(__file__).parent/'source_dispositions.json')['confirmed_empty_sections'][0];url=profile['source_url'];hc=load(h/'checkpoint.json');wc=load(w/'checkpoint.json');pc=load(p/'checkpoint.json')
 ha=next(a for a in hc['artifacts'] if a['role']=='content' and a['source_url']==url);wa=next(a for a in wc['artifacts'] if a['role']=='native-word' and a['document_id']==url);pa=pc['artifacts'][0]
 html=(h/ha['path']).read_bytes();word=(w/wa['path']).read_bytes();pdf=(p/pa['path']).read_bytes()
 for raw,a,expected in [(html,ha,profile['html_sha256']),(word,wa,profile['word_sha256']),(pdf,pa,profile['pdf_sha256'])]:
  if a['status']!=200 or sha(raw)!=a['sha256'] or a['sha256']!=expected:raise ValueError('Corrupt/wrong exact source corroboration')
 if pa['source_url']!=profile['evidence']['pdf_url']:raise ValueError('Wrong publisher PDF source')
 doc=next(d for d in hc['inventory'] if d['url']==url);rr,report=parse(html,doc);target=next(r for r in rr if r['number']==profile['number']);worddata=inspect(word);text=worddata['text'];native=re.search(r'(?:Section\s+)?650\.40\s+Transitional Provisions\.\s+(?:Section\s+)?670\s+Recall\.',text)
 reader=PdfReader(io.BytesIO(pdf),strict=True)
 if reader.is_encrypted or len(reader.pages)!=profile['evidence']['pdf_pages']:raise ValueError('Wrong/unqualified native PDF')
 page=profile['evidence']['page'];pt=clean(reader.pages[page-1].extract_text(extraction_mode='plain') or '');pdf_match=re.search(r'Section 650\.40\s+Transitional Provisions\.\s+Section 670\s+Recall\.',pt)
 qualified=target['body_qualification']=='confirmed_published_empty_own_body' and bool(native) and bool(pdf_match)
 result={'schema':'king-source-empty-corroboration-1','qualified_empty_source_disposition':qualified,'whole_publication_complete':False,'number':profile['number'],'heading':profile['heading'],'source_profile':profile,'html_record_id':target['record_id'],'html_source_blocks':target['block_indices'],'word_context':native.group(0) if native else None,'pdf_page':page,'pdf_context':pdf_match.group(0) if pdf_match else None,'images_extracted':False,'image_members_never_read':worddata['image_members_never_read'],'legal_status_inference':None,'source_only_observation':'Published own-body is empty across exact HTML/DOCX/PDF; preserve heading and IDs. No statement that this parent section is repealed.','source_checkpoints':{'html':sha((h/'checkpoint.json').read_bytes()),'word':sha((w/'checkpoint.json').read_bytes()),'pdf':sha((p/'checkpoint.json').read_bytes())},'code_fingerprint':{n:sha((Path(__file__).parent/n).read_bytes()) for n in ['king_empty_source_audit.py','king_normalize.py','word_model.py','model.py','source_common.py','source_dispositions.json']}};save(out,result);return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--html-source',required=True);ap.add_argument('--word-source',required=True);ap.add_argument('--pdf-source',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();r=run(a.html_source,a.word_source,a.pdf_source,a.out);print(json.dumps(r,indent=2));sys.exit(0 if r['qualified_empty_source_disposition'] else 2)
