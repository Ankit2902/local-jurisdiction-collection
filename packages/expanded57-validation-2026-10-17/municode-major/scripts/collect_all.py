import json,os,subprocess,sys,hashlib,platform
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
URLS={22:'https://library.municode.com/ca/fresno/codes/code_of_ordinances',24:'https://library.municode.com/ga/atlanta/codes/code_of_ordinances',25:'https://library.municode.com/mo/kansas_city/codes/code_of_ordinances',26:'https://library.municode.com/az/mesa/codes/code_of_ordinances',27:'https://library.municode.com/nc/raleigh/codes/code_of_ordinances',29:'https://library.municode.com/fl/miami/codes/code_of_ordinances',30:'https://library.municode.com/ne/omaha/codes/code_of_ordinances',31:'https://library.municode.com/va/virginia_beach/codes/code_of_ordinances',32:'https://library.municode.com/ca/long_beach/codes/municipal_code',34:'https://library.municode.com/ok/tulsa/codes/code_of_ordinances',35:'https://library.municode.com/co/aurora/codes/code_of_ordinances',36:'https://library.municode.com/ks/wichita/codes/code_of_ordinances',37:'https://library.municode.com/la/new_orleans/codes/code_of_ordinances'}
if __name__=='__main__':
 for a in json.loads((ROOT/'assignment.json').read_text()):
  seq=a['sequence'];name=a['jurisdiction'].lower().replace(' ','-');out=ROOT/'browser'/name
  if out.joinpath('receipt.json').exists():print('already retained',name,flush=True);continue
  version=ROOT/'script-versions';version.mkdir(exist_ok=True)
  code=(ROOT/'scripts/collect_browser.cjs').read_bytes();digest=hashlib.sha256(code).hexdigest();snap=version/(digest+'.cjs');snap.write_bytes(code)
  cmd=[os.environ.get('NODE','node'),str(ROOT/'scripts/collect_browser.cjs'),URLS[seq],str(out),'3'];print('START',name,flush=True)
  cp=subprocess.run(cmd,capture_output=True,text=True,env=os.environ)
  out.mkdir(parents=True,exist_ok=True);(out/'command.json').write_text(json.dumps({'command':cmd,'returncode':cp.returncode,'collector_sha256':digest,'collector_snapshot':str(snap.relative_to(ROOT)),'platform':platform.platform(),'python':platform.python_version()},indent=2));(out/'stdout.log').write_text(cp.stdout);(out/'stderr.log').write_text(cp.stderr);print('DONE',name,cp.returncode,cp.stdout[-400:],flush=True)
