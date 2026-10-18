import sys
sys.dont_write_bytecode=True
import pathlib,json,subprocess,time,hashlib
H=pathlib.Path(__file__).resolve().parent;ids=['82-cfe47a936088','82-7a796760f2f3','82-301463c368c5','82-02572b382672'];d=H/'full-native';d.mkdir(exist_ok=True);results=[]
for id in ids:
 out=d/id;cmd=[sys.executable,'-B',str(H/'captured/collectors/encodeplus/retained_native.py'),'--config',str(H/'configs'/('native-'+id+'.json')),'--input',str(H/'native-discovery'/(id+'.bin')),'--receipt',str(H/'native-discovery'/(id+'.bin.receipt.json')),'--out',str(out)];start=time.monotonic()
 with(d/(id+'.stdout')).open('wb')as stdout,(d/(id+'.stderr')).open('wb')as stderr:p=subprocess.run(cmd,stdout=stdout,stderr=stderr)
 r={'id':id,'command':cmd,'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-start,'config_sha256':hashlib.sha256((H/'configs'/('native-'+id+'.json')).read_bytes()).hexdigest()};results.append(r);(d/'terminal.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(r),flush=True)
