"""Serial standalone browser validation driver. Bounded three provision samples per primary code."""
import argparse,json,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SLUGS={1:'houston',3:'san_antonio',6:'jacksonville',7:'austin',8:'charlotte',9:'columbus',10:'indianapolis_-_marion_county',11:'metro_government_of_nashville_and_davidson_county',12:'oklahoma_city',13:'el_paso',14:'las_vegas',16:'detroit',19:'memphis'}
def slug(r):return re.sub('[^a-z0-9]+','-',r['selection_name'].lower())
def main():
 p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true');p.add_argument('--skip-houston',action='store_true');p.add_argument('--output-root',type=Path,help='Fresh output root for a new live run');a=p.parse_args();from normalize import normalize
 outcomes=[]
 for r in json.loads((ROOT/'assignment.json').read_text()):
  if a.skip_houston and r['sequence']==1:continue
  target=(a.output_root or ROOT/'samples')/slug(r)
  if not a.output_root and r['sequence']==1 and (ROOT/'samples/houston-v2/receipt.json').exists():target=ROOT/'samples/houston-v2'
  url=f"https://library.municode.com/{r['state'].lower()}/{SLUGS[r['sequence']]}/codes/code_of_ordinances"
  if not a.offline and not (target/'receipt.json').exists():
   target.mkdir(parents=True,exist_ok=True);cmd=[os.environ.get('NODE','node'),str(ROOT/'collect_browser.cjs'),url,str(target),'3'];print('START',r['jurisdiction'],flush=True)
   with (target/'command.log').open('w') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'MUNICODE_LEAN':'1'}).returncode
   print('FINISH',r['jurisdiction'],rc,flush=True)
  if (target/'samples.json').exists():
   try:report=normalize(target);print('NORMALIZED',r['jurisdiction'],report['record_count'],flush=True)
   except Exception as e:print('PARSE_FAIL',r['jurisdiction'],str(e),flush=True)
if __name__=='__main__':main()
