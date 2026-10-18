"""Run the real CLI replay/verify with browser and network tripwires; no alternate success path."""
import sys,socket,urllib.request
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path:sys.path.insert(0,str(HERE))
import cli,shared_transport

def blocked(*args,**kwargs):raise AssertionError('Offline proof attempted network or browser startup')
def main(argv=None):
 argv=list(sys.argv[1:] if argv is None else argv)
 if not argv or argv[0] not in ('replay','verify'):raise ValueError('Offline proof supports actual CLI replay or verify only')
 with patch.object(socket.socket,'connect',blocked),patch.object(socket,'create_connection',blocked),patch.object(urllib.request.OpenerDirector,'open',blocked),patch.object(shared_transport,'fetch',blocked),patch('playwright.sync_api.sync_playwright',blocked):
  return cli.main(argv)
if __name__=='__main__':sys.exit(main())
