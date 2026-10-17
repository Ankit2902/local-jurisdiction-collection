"""Archive current standalone sources without importing prior packages."""
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'script-versions';out.mkdir(exist_ok=True)
for p in (ROOT/'scripts').glob('*'):
 if p.is_file() and p.suffix in ['.py','.cjs']:
  data=p.read_bytes();sha=hashlib.sha256(data).hexdigest();(out/(sha+'-'+p.name)).write_bytes(data)
