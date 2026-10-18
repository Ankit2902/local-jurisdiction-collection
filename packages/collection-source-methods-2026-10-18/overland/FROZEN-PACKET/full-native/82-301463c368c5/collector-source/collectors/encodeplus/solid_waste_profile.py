"""Only the original 2011 six-page source SHA is qualified. No legal body is hardcoded."""
SOURCE_SHA256='1af70bb8170cf2701cfb9e7ede2b274bf848309ca6fcaa3b7a7eeba9cd426c39'
PUBLICATION='native-82-4b983dc51ab6'
SOURCE_URL='https://codes.opkansas.org/municipal-code/doclibrary.aspx?id=68642c1d-ce7d-4ab0-a9e3-cf56d6def79a'
IMAGE_POLICY='literal-[IMAGE]-no-image-fetch-v1'

def bindings():
 rows=[]
 def add(tag,key,parent,kind,label=None,x=90,prefix=None,bold=False,size=11.52):
  rows.append({'source_tag_id':tag,'key':key,'parent_key':parent,'unit_type':kind,'source_label':label,'first_glyph_x':x,'first_glyph_size':size,'text_prefix':prefix if prefix is not None else (label+'. ' if label else None),'bold_nonspace':bold})
 add('tag:0.0','document',None,'document-title',x=111.24,prefix='Regulations for the Collection and Storage of Solid Waste and Recyclables in Overland Park, Kansas',bold=True,size=18)
 add('tag:0.1','document.year','document','front-matter',x=294,prefix='2011',size=12)
 add('tag:0.4','document.preamble','document','preamble',prefix='Pursuant to O.P.M.C. Chapter 7.36,')
 titles={1:'Hauler and Hauler Vehicle Permits.',2:'Required Hauler Services.',3:'Hauler Communication Requirements to Customers.',4:'Hauler Communication Requirements to the City.',5:'Additional Hauler Collection Requirements and Provisions.'}
 for number,tag in [(1,'tag:0.6'),(2,'tag:0.17'),(3,'tag:0.33'),(4,'tag:0.47'),(5,'tag:0.53')]:add(tag,'7.36-'+str(number),'document','section','7.36-'+str(number),prefix='7.36-'+str(number)+' '+titles[number],bold=True)
 add('tag:0.7','7.36-1.intro','7.36-1','paragraph',prefix='The following Hauler and Hauler Vehicle Permit')
 add('tag:0.9','7.36-1.A','7.36-1','list-item','A')
 for i in range(5):add(f'tag:0.10.{i}.0',f'7.36-1.A.{i+1}','7.36-1.A','list-item',str(i+1),126)
 add('tag:0.12','7.36-1.B','7.36-1','list-item','B')
 for i in range(6):add(f'tag:0.13.{i}.0',f'7.36-1.B.{i+1}','7.36-1.B','list-item',str(i+1),126)
 for i,label in enumerate('abcdefghijk'):add(f'tag:0.13.1.0.1.{i}.0',f'7.36-1.B.2.{label}','7.36-1.B.2','list-item',label,162)
 for i,label in enumerate('abcd'):add(f'tag:0.13.{i+6}.0',f'7.36-1.B.6.{label}','7.36-1.B.6','list-item',label,162)
 add('tag:0.14','7.36-1.B.6.paragraph','7.36-1.B.6','paragraph',x=162,prefix='Vehicles of a Hauler’s subcontractor')
 for i,label in enumerate('ab'):add(f'tag:0.15.0.{i}.0',f'7.36-1.B.6.paragraph.{label}','7.36-1.B.6.paragraph','list-item',label,162)
 add('tag:0.18','7.36-2.intro','7.36-2','paragraph',prefix='The following minimum required Hauler services')
 add('tag:0.20.0.0','7.36-2.A','7.36-2','list-item','A')
 for i in range(2):add(f'tag:0.20.0.0.1.{i}.0',f'7.36-2.A.{i+1}','7.36-2.A','list-item',str(i+1),126)
 for i,label in enumerate('abc'):add(f'tag:0.{21+i}',f'7.36-2.A.2.{label}','7.36-2.A.2','list-item',label,162)
 add('tag:0.24.0.0.0','7.36-2.A.3','7.36-2.A','list-item','3',126)
 for i,label in enumerate('abc'):add(f'tag:0.{25+i}',f'7.36-2.A.3.{label}','7.36-2.A.3','list-item',label,162)
 add('tag:0.29.0.0.0','7.36-2.A.4','7.36-2.A','list-item','4',126)
 add('tag:0.31','7.36-2.B','7.36-2','list-item','B')
 add('tag:0.35','7.36-3.A','7.36-3','list-item','A')
 add('tag:0.37','7.36-3.B','7.36-3','list-item','B')
 add('tag:0.39','7.36-3.B.paragraph','7.36-3.B','paragraph',x=126,prefix='The written notice to customers required by this subsection B.')
 add('tag:0.41','7.36-3.B.Residential','7.36-3.B','subheading',x=126,prefix='Residential Customers',bold=True)
 for i in range(9):add(f'tag:0.42.0.{i}.0',f'7.36-3.B.Residential.{i+1}','7.36-3.B.Residential','list-item',str(i+1),126)
 add('tag:0.44','7.36-3.B.Commercial','7.36-3.B','subheading',x=126,prefix='Commercial Customers',bold=True)
 for i in range(6):add(f'tag:0.45.0.{i}.0',f'7.36-3.B.Commercial.{i+1}','7.36-3.B.Commercial','list-item',str(i+1),126)
 for label,tag in [('A','tag:0.49.0.0'),('B','tag:0.51.0.0')]:add(tag,'7.36-4.'+label,'7.36-4','list-item',label)
 for i,label in enumerate('ABCDEFGHI'):add(f'tag:0.55.{i}.0','7.36-5.'+label,'7.36-5','list-item',label)
 for i in range(4):add(f'tag:0.55.8.0.1.{i}.0',f'7.36-5.I.{i+1}','7.36-5.I','list-item',str(i+1),126)
 assert len(rows)==88 and len({r['source_tag_id'] for r in rows})==88 and len({r['key'] for r in rows})==88
 return rows
