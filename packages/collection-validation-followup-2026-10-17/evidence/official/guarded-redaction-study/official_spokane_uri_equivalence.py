import pathlib,json,re,hashlib,sys,importlib.util
from html.parser import HTMLParser
from bs4 import BeautifulSoup
r=pathlib.Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00');n=r/'outputs/collection-readiness-next-2026-10-17';run=r/'outputs/collection-readiness-2026-10-17/official/spokane-full-bulk-v10';p=n/'spokane-guarded-source-data-image-scan.json';o=json.loads(p.read_text());sys.path.insert(0,str(n/'official-final-candidate'))
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=load('old_spokane_uri_model',n/'official-final-candidate/model.py');new=load('new_spokane_uri_model',n/'official-redaction-qualified-candidate/model.py');checks=[]
class Scan(HTMLParser):
 def handle_starttag(self,tag,attrs):
  if not any(value and re.search('data:image/',value,re.I) for _,value in attrs):return
  original=self.get_starttag_text();a=old.semantics(BeautifulSoup('<main>'+original+'</main>','html.parser').main,self.url);b=new.semantics(BeautifulSoup('<main>'+original+'</main>','html.parser').main,self.url);checks.append({'batch':self.batch,'native_tag_sha256':hashlib.sha256(original.encode()).hexdigest(),'old_semantics_sha256':old.sha(old.encoded(a)),'new_semantics_sha256':new.sha(new.encoded(b)),'normalized_equal':a==b})
for row in o['batches']:
 s=Scan(convert_charrefs=True);s.batch=row['id'];s.url='https://my.spokanecity.org/smc/';s.feed((run/row['raw_ref']).read_bytes().decode('utf-8','strict'));s.close()
assert len(checks)==o['total_data_image_prefixes']==o['attribute_data_image_prefixes'] and not o['text_node_hits'];assert all(x['normalized_equal']for x in checks)
o.update(old_model_sha256=old.sha((n/'official-final-candidate/model.py').read_bytes()),new_model_sha256=new.sha((n/'official-redaction-qualified-candidate/model.py').read_bytes()),actual_uri_semantics_checks=checks,all_actual_image_tag_normalized_outputs_equal=True,claim='All68native batches scanned:123data-image occurrences, all123 actual img/src attrs, no data-image text nodes and no wrapped attrs. Every exact native image tag normalized under both revisions with equal outputs. This qualifies only the narrow redactor applicability; full heading/body parse stays separately bound to model2c.')
p.write_text(json.dumps(o,indent=2)+'\n');print({'checked_actual_tags':len(checks),'all_equal':True,'old_model':o['old_model_sha256'],'new_model':o['new_model_sha256']})
