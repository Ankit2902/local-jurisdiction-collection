"""Network-free family preflight. The root ops launcher owns installation and environment setup."""
import json,os,subprocess,sys
from pathlib import Path
from pdf_integrity import runtime_check
HERE=Path(__file__).resolve().parent
SUPPORTED_PLAYWRIGHT=('1.62.1','1.64.0','1.64.0-beta-1791568591000')
def check(live=True):
 errors=[];ok,pdf=runtime_check()
 if sys.version_info<(3,12):errors.append('Use supported Python3.12 via collectors/ops launcher')
 if not ok:errors.append(pdf)
 result={'python':sys.version,'python_executable':sys.executable,'pdf_parser':pdf,'network_requests':0,'errors':errors}
 if live:
  node=os.environ.get('NODE','node');result['node_executable']=node
  try:
   version=subprocess.check_output([node,'--version'],text=True).strip();result['node']=version
   if int(version.lstrip('v').split('.')[0])<20:errors.append('Node20+ required; set NODE or use collectors/ops launcher')
   else:
    script="const{createRequire}=require('module');const r=createRequire(process.env.PLAYWRIGHT_MODULE_ROOT||process.argv[1]);console.log(r('playwright/package.json').version)"
    playwright=subprocess.check_output([node,'-e',script,str(HERE/'package.json')],text=True,stderr=subprocess.STDOUT).strip();result['playwright']=playwright
    result['supported_playwright_versions']=list(SUPPORTED_PLAYWRIGHT)
    if playwright not in SUPPORTED_PLAYWRIGHT:errors.append('Supported Playwright '+ ' or '.join(SUPPORTED_PLAYWRIGHT)+' required; use locked npm installation or root ops setup')
  except Exception as e:errors.append('Node/Playwright preflight failed: '+str(e))
 result['passed']=not errors
 return result
if __name__=='__main__':
 result=check();print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 2)
