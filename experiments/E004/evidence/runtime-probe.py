import socket,urllib.request,json,os,sys
from pathlib import Path
from openpyxl import load_workbook
out={'cwd':os.getcwd(),'python':sys.executable,'addresses':socket.getaddrinfo('localhost',11434,type=socket.SOCK_STREAM)}
p=Path('inside-canary.txt');p.write_text('NO_ANSWERS');out['inside_rw']=p.read_text()=='NO_ANSWERS'
w=load_workbook('銷售 資料/sales.xlsx',read_only=True);out['xlsx_read']=w.sheetnames==['Sales'];w.close()
for label,path in [('sibling','/private/tmp/local-excel-extensions/runs/isolated/outside-canary.txt'),('oracle','/Users/andrew/.codex/worktrees/7e4a/ollama-windows-poc/poc/local-excel/oracle.json'),('symlink','outside-link')]:
 try:Path(path).read_bytes();out[label]='UNEXPECTED_ALLOWED'
 except PermissionError:out[label]='denied'
try:list(Path.cwd().parent.parent.iterdir());out['parent_list']='UNEXPECTED_ALLOWED'
except PermissionError:out['parent_list']='denied'
for host in ['localhost','127.0.0.1','[::1]']:
 try:
  with urllib.request.build_opener(urllib.request.ProxyHandler({})).open('http://'+host+':11434/api/version',timeout=3) as f:out[host]=json.load(f)
 except Exception as e:out[host]=str(e)
print(json.dumps(out))
