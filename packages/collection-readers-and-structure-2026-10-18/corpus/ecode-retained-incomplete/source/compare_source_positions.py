"""QA-only all-raw comparison of stdlib position scanner against independent BS4 selector."""
import sys
sys.dont_write_bytecode=True
import hashlib,json,socket
from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup
from ecode_html import toc_positions

def main():
 root=Path(sys.argv[1]);out=Path(sys.argv[2]);cp=json.loads((root/'checkpoint.json').read_text());checks=[];calls=[]
 def no(*a,**k):calls.append('network');raise AssertionError('No network')
 with patch.object(socket.socket,'connect',no),patch.object(socket,'create_connection',no):
  for a in cp['artifacts']:
   data=(root/a['path']).read_bytes();digest=hashlib.sha256(data).hexdigest();assert digest==a['sha256']
   sp=BeautifulSoup(data,'html.parser');expected=[(e['data-guid'],e['data-position']) for e in sp.select('#toc .contentTitle[data-guid][data-position]')];actual=toc_positions(data);assert expected==actual,a['path']
   checks.append({'path':a['path'],'raw_sha256':digest,'entries':len(actual),'positions_sha256':hashlib.sha256(json.dumps(actual,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),'equal':True})
 report={'schema':1,'raw_artifacts':len(checks),'all_equal':True,'scanner_source_sha256':hashlib.sha256((Path(__file__).parent/'ecode_html.py').read_bytes()).hexdigest(),'comparison_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'reference':'Independent BS4.15 selector #toc .contentTitle[data-guid][data-position], compared with narrow stdlibHTMLParser across every retained rawartifact including refusalemptyHEAD','checks':checks,'network_requests':0,'forbidden_calls':calls,'source_modified':False};out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'all_equal':True,'raw_artifacts':len(checks),'forbidden_calls':calls}))
if __name__=='__main__':main()
