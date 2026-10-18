"""Read-only compact peer packet check; no source parser/native/image imports."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 m=json.loads((H/'MANIFEST.json').read_bytes());actual={str(p.relative_to(H)):sha(p)for p in H.rglob('*')if p.is_file()and p.name!='MANIFEST.json'};assert m['files']==actual
 r=json.loads((H/'review.json').read_bytes());assert r['passed']is True and r['publication_complete']is False
 c=json.loads((H/'consumer-review.json').read_bytes());assert c['records_exact16fields']==3006 and c['source_nodes_and_dispositions']==3253 and c['IMAGE_count']==28
 print(json.dumps({'passed':True,'files':len(actual),'reviewed_reader_scope':'retained_incomplete_ecode_HTML_only','publication_complete':False},indent=2))
if __name__=='__main__':main()
