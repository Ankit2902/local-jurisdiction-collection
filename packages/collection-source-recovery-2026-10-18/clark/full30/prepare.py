import pathlib,sys,json,shutil,hashlib
ROOT=pathlib.Path('/Users/oliverflint/My Drive/Claude/Projects/CompliSolv 2.00')
OUT=pathlib.Path(__file__).parent
SRC=ROOT/'github/local-jurisdiction-collection/collectors/official'
sys.path.insert(0,str(SRC));import collect
runtime=OUT/'runtime';runtime.mkdir()
for name in collect.runtime_scripts():shutil.copyfile(SRC/name,runtime/name)
for name in ['requirements.txt','requirements-lock.txt']:
 if (SRC/name).exists():shutil.copyfile(SRC/name,runtime/name)
c=json.loads((OUT.parent/'clark-title30-discovery-v1/proposed-official-config.json').read_text())
(OUT/'config.json').write_text(json.dumps(c,indent=2)+'\n')
(OUT/'source-binding.json').write_text(json.dumps({'scripts':collect.runtime_scripts(),'runtime_python':sys.version,'source_directory':str(SRC),'snapshot':str(runtime)},indent=2)+'\n')
