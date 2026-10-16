"""Inspect bounded PDF pages; no corpus extraction or legal currency inference."""
import argparse,datetime,hashlib,json
from pathlib import Path
from pypdf import PdfReader

def inspect(path,pages=(1,2)):
    path=Path(path);data=path.read_bytes()
    if not data.startswith(b'%PDF-'):raise ValueError('Source is not original PDF bytes; HTML/error shell rejected')
    reader=PdfReader(path);selected=sorted(set(pages)|{len(reader.pages)})
    if len(selected)>8:raise ValueError('Bounded qualification limit is eight pages')
    if reader.is_encrypted:raise ValueError('Encrypted PDF requires a separate profile')
    extracted=[{'page':n,'text':reader.pages[n-1].extract_text()} for n in selected if 1<=n<=len(reader.pages)]
    return {'input':path.name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'pages':len(reader.pages),'inspected_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selected_pages':extracted,'text_status':'text_available' if any(x['text'].strip() for x in extracted) else 'ocr_required','coverage':'bounded PDF structure/text pilot; no full extraction','layout_fidelity_verified':False}
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--page',type=int,action='append');a=ap.parse_args();result=inspect(a.input,a.page or (1,2));a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='selected_pages'},indent=2))
