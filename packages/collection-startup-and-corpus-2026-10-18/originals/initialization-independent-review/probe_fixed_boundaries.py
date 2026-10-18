from pathlib import Path
import sys,tempfile,json,hashlib,socket,base64
from unittest.mock import patch
source=Path(sys.argv[1]);out=Path(sys.argv[2]);sys.path.insert(0,str(source));import flagstaff_initialization as m,flagstaff_inventory
cases=[];forbidden=[]
def no(*a,**kw):forbidden.append('network_or_image');raise AssertionError('No network/image APIs')
from PIL import Image
with patch.object(socket.socket,'connect',no),patch.object(socket,'create_connection',no),patch.object(base64,'b64decode',no),patch.object(Image,'open',no):
 for status in [403,429]:
  with tempfile.TemporaryDirectory()as tmp:
   base=Path(tmp);work=base/'source';work.mkdir();calls=[]
   def first(folder):
    calls.append('first');folder.mkdir();m.save(folder/'network-events.json',[{'status':status,'url':m.URL}]);raise KeyboardInterrupt()
   def second(folder):calls.append('second');raise AssertionError('Refused generation restarted')
   with patch.object(m.transport,'ROOT',base/'gate'),patch.object(flagstaff_inventory,'run',first):
    try:m.initialize(work,['flagstaff_initialization.py'],lambda p:None)
    except KeyboardInterrupt:pass
   data=(work/'inventory-attempt-0001/network-events.json').read_bytes();assert not(work/'inventory-attempt-0001/receipt.json').exists();error=None
   with patch.object(m.transport,'ROOT',base/'gate'),patch.object(flagstaff_inventory,'run',second):
    try:m.initialize(work,['flagstaff_initialization.py'],lambda p:None,resume=True)
    except ValueError as e:error=str(e)
   assert error and 'refusal retained'in error and calls==['first']and (work/'inventory-attempt-0001/network-events.json').read_bytes()==data
   cases.append({'kind':'missing_receipt_retained_status','status':status,'refused_before_restart':True,'retained_event_unchanged':True})
 with tempfile.TemporaryDirectory()as tmp:
  base=Path(tmp);work=base/'source';work.mkdir();calls=[]
  def before_dir(folder):calls.append('initial');raise KeyboardInterrupt()
  def finish(folder):calls.append('resumed');folder.mkdir();m.save(folder/'receipt.json',{'source_url':m.URL,'whole_publication_selected_values':['code'],'checked_values':['code']})
  with patch.object(m.transport,'ROOT',base/'gate'),patch.object(flagstaff_inventory,'run',before_dir):
   try:m.initialize(work,['flagstaff_initialization.py'],lambda p:None)
   except KeyboardInterrupt:pass
  assert not(work/'inventory-attempt-0001').exists()
  with patch.object(m.transport,'ROOT',base/'gate'),patch.object(flagstaff_inventory,'run',finish):
   m.initialize(work,['flagstaff_initialization.py'],lambda p:None,resume=True)
   m.initialize(work,['flagstaff_initialization.py'],lambda p:None,resume=True)
   assert calls==['initial','resumed'];state=m.load(work/m.NAME);assert state['attempts'][0]['directory_exists']is False and state['attempts'][0]['manifest']=={}
   (work/'inventory-attempt-0001').mkdir();error=None
   try:m.initialize(work,['flagstaff_initialization.py'],lambda p:None,resume=True)
   except ValueError as e:error=str(e)
   assert error and 'generation changed'in error and calls==['initial','resumed']
  cases.append({'kind':'absent_native_directory','normal_resume_once_without_reacquisition':True,'recorded_absence_retained':True,'later_directory_insertion_refused':True})
assert not forbidden
r={'passed':True,'helper_sha256':hashlib.sha256((source/'flagstaff_initialization.py').read_bytes()).hexdigest(),'cases':cases,'forbidden_calls':forbidden,'raw_generation_mutations_are_controlled_temp_faults_only':True,'production_source_or_sealed_evidence_modified':False,'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};(out/'independent-boundary-probe.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
