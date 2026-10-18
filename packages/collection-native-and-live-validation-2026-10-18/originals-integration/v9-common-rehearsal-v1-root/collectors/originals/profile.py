"""Strict, portable configuration for two qualified original-source publication profiles."""
from dataclasses import dataclass,asdict
from enum import Enum
from pathlib import Path
import json
import hashlib
def canon(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def sha(value):return hashlib.sha256(value).hexdigest()
class Profile(str,Enum):
 FLAGSTAFF='flagstaff_html'
 KING='king_html_word'
EXPECTED={
 Profile.FLAGSTAFF:dict(target_id='original-flagstaff-az',jurisdiction='Flagstaff',state='AZ',source_url='https://www.codepublishing.com/AZ/Flagstaff/',publication='City Code including Charter'),
 Profile.KING:dict(target_id='original-king-county-wa',jurisdiction='King County',state='WA',source_url='https://kingcounty.gov/en/dept/council/governance-leadership/county-legislation-codes/king-county-code',publication='King County Code including source-listed Charter and editorial matter')}
@dataclass(frozen=True)
class PublicationConfig:
 schema_version:int
 target_id:str
 profile:Profile
 jurisdiction:str
 state:str
 source_url:str
 publication:str
 required_formats:tuple[str,...]
 def binding(self):
  data=asdict(self);data['profile']=self.profile.value;data['required_formats']=list(self.required_formats);return data
 @property
 def id(self):return self.target_id
 @property
 def digest(self):return sha(canon(self.binding()))
 def family(self,format='html'):
  if format not in ('html','word'):raise ValueError('Unsupported source format')
  if self.profile==Profile.FLAGSTAFF:
   if format!='html':raise ValueError('Flagstaff profile supports HTML only; native whole export attempts remain unqualified')
   return 'flagstaff-html'
  return 'king-word' if format=='word' else 'king'
def parse_config(value):
 if not isinstance(value,dict):raise ValueError('Publication config must be an object')
 fields=set(PublicationConfig.__dataclass_fields__)
 if set(value)!=fields:raise ValueError('Config fields must be exactly '+','.join(sorted(fields)))
 if type(value['schema_version']) is not int or value['schema_version']!=1:raise ValueError('Unsupported publication config schema_version')
 try:profile=Profile(value['profile'])
 except (ValueError,TypeError):raise ValueError('Unknown original publication profile')
 formats=['html'] if profile==Profile.FLAGSTAFF else ['html','word']
 if value['required_formats']!=formats:raise ValueError('Exact required source formats differ from qualified profile')
 for key,wanted in EXPECTED[profile].items():
  if value[key]!=wanted:raise ValueError('Publication source/profile identity mismatch: '+key)
 return PublicationConfig(**dict(value,profile=profile,required_formats=tuple(formats)))
def load_config(path):return parse_config(json.loads(Path(path).read_text()))
