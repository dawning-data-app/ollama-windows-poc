from pathlib import Path
import json,subprocess
root=Path('/private/tmp/local-excel-extensions/isolation');run=Path('/private/tmp/local-excel-extensions/runs/isolated/20261105T091434-ecdfbe5e');env=json.loads((root/'env.json').read_text());prefix=['/usr/bin/sandbox-exec','-f',str(root/'profile.sb')]
code='''import json,urllib.request
from pathlib import Path
out={}
for label,path in [('sibling','/private/tmp/local-excel-extensions/runs/isolated/outside-canary.txt'),('oracle','/Users/andrew/.codex/worktrees/7e4a/ollama-windows-poc/poc/local-excel/oracle.json'),('symlink','outside-link')]:
 try:Path(path).read_bytes();out[label]='UNEXPECTED_ALLOWED'
 except PermissionError:out[label]='denied'
try:list(Path.cwd().parent.parent.iterdir());out['parent_list']='UNEXPECTED_ALLOWED'
except PermissionError:out['parent_list']='denied'
p=Path('inside-canary.txt');p.write_text('NO_ANSWERS');out['inside_rw']=p.read_text()=='NO_ANSWERS'
try:
 with urllib.request.build_opener(urllib.request.ProxyHandler({})).open('http://localhost:11434/api/version',timeout=10) as f:out['loopback']=json.load(f)['version']
except Exception as e:out['loopback']=str(e)
print(json.dumps(out))
'''
for name,args in [('paths', ['uv','run','--locked','--offline','python','-c',code]),('backend-config',['uv','run','--locked','--offline',json.loads((run/'manifest.json').read_text())['binary'],'debug','config'])]:
 try:
  res=subprocess.run(prefix+args,cwd=run/'workspace',env=env,capture_output=True,text=True,timeout=35)
  (root/(name+'.stdout')).write_text(res.stdout);(root/(name+'.stderr')).write_text(res.stderr)
  print(name,'exit',res.returncode,'stdout',res.stdout[:150] if name=='backend-config' else res.stdout,'stderr',res.stderr[:1800])
 except subprocess.TimeoutExpired:print(name,'timeout')
