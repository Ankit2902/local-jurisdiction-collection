"""Planning-only subprocess guard: refuse network/native/image imports."""
import sys
class BlockNative:
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0]in('pypdf','pypdfium2','pdfplumber','pdfminer','PIL','fitz','pymupdf','requests','urllib3','playwright'):raise AssertionError('Planning imported transport/native/image module:'+fullname)
sys.meta_path.insert(0,BlockNative())
def audit(event,args):
 if event.startswith('socket.'):raise AssertionError('Planning network API:'+event)
sys.addaudithook(audit)
