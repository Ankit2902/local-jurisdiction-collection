import pathlib,json,zipfile,io,hashlib,importlib.util,sys,re
from bs4 import BeautifulSoup
r=pathlib.Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');n=r/'outputs/collection-readiness-next-2026-10-17';sys.path.insert(0,str(n/'official-final-candidate'))
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=module('old_official_metadata',n/'official-final-candidate/model.py');new=module('new_official_metadata',n/'official-redaction-qualified-candidate/model.py');report=json.loads((n/'baltimore-guarded-source-data-image-scan.json').read_text());run=n/'baltimore-final-live-v3';data=(run/report['source_raw_ref']).read_bytes();z=zipfile.ZipFile(io.BytesIO(data));checks=[]
for name in report['members_with_data_image_prefix']:
 b=z.read(name);soup=BeautifulSoup(b,'html.parser');article=soup.select_one('article');url='https://codes.baltimorecity.gov/'+name.split('/us/md/cities/baltimore/',1)[1].removesuffix('/index.html');values=[]
 for el in article.find_all(True):
  for key,value in el.attrs.items():
   if isinstance(value,str) and re.search('data:image/',value,re.I):values.append({'element':el.name,'attribute':key,'value_sha256':hashlib.sha256(value.encode()).hexdigest(),'characters':len(value),'linebreak_count':value.count('\n')+value.count('\r')})
 a=old.semantics(article,url);b=new.semantics(article,url);a=old.encoded(a);b=new.encoded(b);checks.append({'member':name,'source_sha256':hashlib.sha256(z.read(name)).hexdigest(),'inline_image_attribute_metadata':values,'old_semantics_sha256':hashlib.sha256(a).hexdigest(),'new_semantics_sha256':hashlib.sha256(b).hexdigest(),'normalized_equal':a==b})
report.update(old_model_sha256=hashlib.sha256((n/'official-final-candidate/model.py').read_bytes()).hexdigest(),new_model_sha256=hashlib.sha256((n/'official-redaction-qualified-candidate/model.py').read_bytes()).hexdigest(),actual_uri_pages=checks,all_actual_image_pages_normalized_equal=all(x['normalized_equal']for x in checks),claim='All8445canonical source members scanned; seven contain inline image URIs. Each of those complete article semantic outputs independently compared under old/new redactor. This binds the narrow redactor delta only; no native multiline leakage instance is presumed.')
(n/'baltimore-guarded-source-data-image-scan.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'actual_pages':len(checks),'all_equal':report['all_actual_image_pages_normalized_equal'],'inline_refs':sum(len(x['inline_image_attribute_metadata'])for x in checks),'linebreaks':sum(v['linebreak_count']for x in checks for v in x['inline_image_attribute_metadata'])},indent=2))
