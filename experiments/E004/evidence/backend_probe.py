from pathlib import Path
import json,subprocess,os,time,hashlib
r=Path('/private/tmp/local-excel-extensions/isolation-round2');run=Path('/private/tmp/local-excel-extensions/runs/isolated/20261105T091434-ecdfbe5e');w=run/'workspace'
env=json.loads(Path('/private/tmp/local-excel-extensions/isolation/env.json').read_text());binary=json.loads((run/'manifest.json').read_text())['binary']
prefix=['/usr/bin/sandbox-exec','-f',str(r/'profile.sb')]
for name in ['inside-canary.txt','outside-link']:
 p=w/name
 if p.is_symlink() or p.exists():p.unlink()
for name,args in [('ls-parent',['/bin/ls',str(run.parent)]),('find-parent',['/usr/bin/find',str(run.parent),'-name','*.xlsx'])]:
 p=subprocess.run(prefix+args,cwd=w,env=env,text=True,capture_output=True,timeout=15)
 (r/(name+'.stdout')).write_text(p.stdout);(r/(name+'.stderr')).write_text(p.stderr)
 print(name,'exit',p.returncode,'output',p.stdout[:200],p.stderr[:200],flush=True)
prompt='請只做環境探測，不做 Excel 分析、不新增依賴。請用 bash 工具執行 pwd，並實際用 uv run --locked --offline python 執行一段 Python，輸出 sys.executable 與 os.getcwd()；讀取 context-probe.txt，最後以繁體中文說明實際環境。不要探索工作區外的檔案。'
(r/'prompt.txt').write_text(prompt)
args=prefix+['uv','run','--locked','--offline',binary,'run','--format','json','--agent','excel','--model','ollama/qwen3.5:9b',prompt]
(r/'command.json').write_text(json.dumps(args,ensure_ascii=False,indent=2))
start=time.time()
with (r/'backend.stdout').open('w') as out,(r/'backend.stderr').open('w') as err:
 p=subprocess.Popen(args,cwd=w,env=env,stdout=out,stderr=err,start_new_session=True)
 (r/'process.json').write_text(json.dumps({'pid':p.pid,'start':start,'cwd':str(w)}))
 try:exitcode=p.wait(timeout=420)
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,15);exitcode=p.wait(timeout=15)
(r/'result.json').write_text(json.dumps({'exit':exitcode,'seconds':time.time()-start}))
print((r/'result.json').read_text(),flush=True)
