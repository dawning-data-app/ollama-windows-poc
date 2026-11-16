from pathlib import Path
import json,subprocess,os,sys
run=Path('/private/tmp/local-excel-extensions/runs/isolated/20261105T091434-ecdfbe5e')
root=Path('/private/tmp/local-excel-extensions/isolation')
for n in ['tmp','config','cache','state']:(run/n).mkdir(exist_ok=True)
read_roots=['/bin','/sbin','/usr/bin','/usr/sbin','/opt/homebrew','/Users/andrew/.local/share/uv/python/cpython-3.12.12-macos-aarch64-none','/private/tmp/local-excel-poc/opencode']
rw=[str(run/n) for n in ['workspace','tmp','config','cache','state']]
profile='''(version 1)
(deny default)
(import "system.sb")
(allow syscall* mach-bootstrap process-exec process-fork sysctl-read)
(allow process-info* (target same-sandbox))
(allow signal (target same-sandbox))
(allow file-read-metadata file-test-existence)
(allow mach-lookup (global-name "com.apple.bsd.dirhelper") (global-name "com.apple.system.opendirectoryd.libinfo") (global-name "com.apple.SystemConfiguration.configd"))
(allow file-read* file-map-executable\n'''+''.join(' (subpath '+json.dumps(p)+')\n' for p in read_roots)+')\n(allow file-read* file-write* file-map-executable\n'+''.join(' (subpath '+json.dumps(p)+')\n' for p in rw)+''')
(allow file-read* file-write* file-ioctl (subpath "/dev"))
(allow file-read-data (literal "/private/etc/hosts") (literal "/private/etc/resolv.conf") (literal "/private/etc/apache2/mime.types"))
(allow network-outbound (remote ip "localhost:11434") (remote ip "127.0.0.1:11434"))
(allow network-bind network-inbound (local ip "localhost:*"))
'''
(root/'profile.sb').write_text(profile)
canary=run.parent/'outside-canary.txt';canary.write_text('CANARY_NO_ANSWERS\n')
link=run/'workspace/outside-link'
if link.is_symlink():link.unlink()
link.symlink_to(canary)
env=json.loads((run/'launch-env.json').read_text());env.update(TMPDIR=str(run/'tmp')+'/',TMP=str(run/'tmp'),TEMP=str(run/'tmp'))
(root/'env.json').write_text(json.dumps(env))
code='''from pathlib import Path
import json,os,sys,urllib.request
from openpyxl import load_workbook
r={run!r}; outside={outside!r}; oracle={oracle!r}
result={{"cwd":os.getcwd(),"python":sys.executable}}
p=Path("inside-canary.txt");p.write_text("NO_ANSWERS");result["inside_rw"]=p.read_text()=="NO_ANSWERS"
wb=load_workbook("銷售 資料/sales.xlsx",read_only=True);result["xlsx_read"]=wb.sheetnames==["Sales"];wb.close()
for key,path in [("sibling_read",outside),("oracle_read",oracle),("symlink_read","outside-link")]:
 try:Path(path).read_bytes();result[key]="UNEXPECTED_ALLOWED"
 except PermissionError:result[key]="denied"
try:list(Path(r).parent.iterdir());result["parent_list"]="UNEXPECTED_ALLOWED"
except PermissionError:result["parent_list"]="denied"
try:
 with urllib.request.build_opener(urllib.request.ProxyHandler({{}})).open("http://localhost:11434/api/version",timeout=10) as f:result["loopback"]=json.load(f)["version"]
except Exception as exc:result["loopback"]=type(exc).__name__+":"+str(exc)
print(json.dumps(result))
'''.format(run=str(run),outside=str(canary),oracle='/Users/andrew/.codex/worktrees/7e4a/ollama-windows-poc/poc/local-excel/oracle.json')
result=subprocess.run(['/usr/bin/sandbox-exec','-f',str(root/'profile.sb'),'uv','run','--locked','--offline','python','-c',code],cwd=run/'workspace',env=env,capture_output=True,text=True,timeout=40)
(root/'filesystem.stdout').write_text(result.stdout);(root/'filesystem.stderr').write_text(result.stderr)
print('exit',result.returncode,'stdout',result.stdout,'stderr',result.stderr[:2500])
