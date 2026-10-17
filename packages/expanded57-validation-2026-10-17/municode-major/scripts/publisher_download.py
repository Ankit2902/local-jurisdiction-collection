"""Publisher-native PDF continuation using observed ClientContent eligibility."""
import json,sys
from pathlib import Path
from municode_shared import fetch,api

def run(folder):
 d=Path(folder);r=json.loads((d/'receipt.json').read_text());cc=json.loads((d/'client-content.json').read_text());productId=r['product']['ProductID'];p=next((p for p in cc.get('codes',[]) if p['productId']==productId),{})
 result={'status':'unavailable','reason':'ClientContent primary entry does not enable a PDF download','publication':p}
 if p.get('hasPdf') and p.get('hasPdfDownloadEnabled') and p.get('publicationId'):
  try:
   b,rc=fetch(api('PublicationPdfDownload/'+str(p['publicationId'])),d/'pdf-url.json');pdf=json.loads(b);url=pdf if isinstance(pdf,str) else pdf.get('url',pdf.get('Url'))
   if not url:raise ValueError('Unknown PDF URL response shape')
   b,rc=fetch(url,d/'publisher-export-response.bin',timeout=120)
   if not b.startswith(b'%PDF-'):raise ValueError('Publisher response is not PDF magic')
   (d/'publisher-export-response.bin').replace(d/'publisher-export.pdf');result={'status':'passed','url':url,'reason':'Automated publisher-native publication PDF acquired; retained source, bounded HTML normalization measured separately','sha256':rc['sha256'],'bytes':len(b)}
  except Exception as ex:result={'status':'blocked','reason':str(ex),'publication_id':p['publicationId']}
 r['publisher_download']=result;(d/'receipt.json').write_text(json.dumps(r,indent=2));print(json.dumps(result),flush=True)
if __name__=='__main__':run(sys.argv[1])
