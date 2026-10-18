"""Actual text-operator position ledger, never a rewritten PDF or legal text."""
import hashlib,json,socket,sys,collections
from pathlib import Path
from unittest.mock import patch,PropertyMock
from pypdf import PdfReader
from pypdf._page import PageObject
from font_proof import derive,decoder_from_original,SOURCE_SHA256
source,out=map(Path,sys.argv[1:]);raw=source.read_bytes();proof=derive(raw);decode=decoder_from_original(raw,proof);rows=[];calls=[]
def forbidden(*a,**k):calls.append('forbidden');raise AssertionError('No network/image API')
with patch('socket.socket',side_effect=forbidden),patch.object(PageObject,'images',new_callable=PropertyMock,side_effect=forbidden):
 reader=PdfReader(source,strict=True)
 for page_no,page in enumerate(reader.pages,1):
  font_refs=page.get('/Resources',{}).get('/Font',{});current=None;stack=[]
  for operator_index,(operands,operator) in enumerate(page.get_contents().operations):
   if operator==b'q':stack.append(current)
   elif operator==b'Q':current=stack.pop() if stack else None
   elif operator==b'Tf':current=font_refs.get(str(operands[0])).idnum
   elif operator in [b'Tj',b'TJ',b"'",b'"'] and current in [620,628]:
    strings=operands[0] if operator==b'TJ' else [operands[-1]]
    for operand_index,value in enumerate(strings):
     if not isinstance(value,(str,bytes)):continue
     data=value.original_bytes if isinstance(value,str) else bytes(value);units=decode(data,current)
     rows.append({'native_source_sha256':SOURCE_SHA256,'physical_page':page_no,'page_content_operator_index_zero_based':operator_index,'operator':operator.decode(),'string_operand_index_zero_based':operand_index,'source_font_object':current,'source_operand_sha256':hashlib.sha256(data).hexdigest(),'units':units,'diagnostic_only':True,'source_text_substituted':False,'all_units_qualified':all(x['qualified'] for x in units)})
counts=collections.Counter(x['qualified'] for row in rows for x in row['units']);assert counts[True]==3382 and counts[False]==4447;assert len(rows)==814;assert not calls;assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA256
p=out/'source-CID-recovery-ledger.jsonl';p.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows));(out/'source-CID-ledger-check.json').write_text(json.dumps({'passed':True,'source_runs':len(rows),'source_glyph_units':sum(counts.values()),'source_proven_Unicode_units':counts[True],'unresolved_units':counts[False],'native_source_sha256':SOURCE_SHA256,'ledger_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_unchanged':True,'network_requests':0,'image_APIs':False,'legal_text_or_PDF_rewritten':False},indent=2)+'\n');print(json.dumps({'runs':len(rows),'proven':counts[True],'unresolved':counts[False]}))
