"""One short experimental prompt; evaluator only, never an Excel analyzer."""
from pathlib import Path
import json
import workflow

VERSION = 'excel-short-v1'


def prompt(folder: Path, negative: bool = False) -> str:
    return f'''請分析資料夾：{folder}
請自主寫 Python 並實際執行，openpyxl 已安裝，工作表 Sales。
先寫 check_excel.py：實際列舉這個精確目錄，找到 .xlsx；用 iter_rows(values_only=True) 讀出欄名及首筆資料的 Python 型別並印出。不能猜檔名、欄位位置或改查父目錄。
成功後才寫 analysis.py，按欄名計算 quantity*unit_price 的總額、YYYY-MM 月額、region 區域額及遞減排名；region 不是 product。核對兩種分組加總等於總額。
兩支程式都用 `uv run --locked --offline python 檔名.py` 執行。analysis.py 寫 answer.json，stdout 只印相同 JSON，僅含 total_sales、monthly_sales、regional_sales、region_ranking。
若實際列目錄／開啟檔案失敗，印出 JSON：path（真正失敗的完整目錄或檔案路徑）、error_type、error_message（原始例外），非零結束，停止、不寫 answer.json。不要猜原因或檔案大小門檻。
最後只寫「{workflow.ERROR_LEAD if negative else workflow.NORMAL_LEAD}」及一個 json 區塊，複製實際結果／錯誤 JSON，不加其他數字、幣別或推測。
不安裝套件，不讀工作區外資料，不改 Excel、uv.lock、opencode.json。'''


def review(run: Path, manifest: dict, tools: list[dict], final: str) -> list[str]:
    negative = manifest['case'] != 'sales'
    try:
        response = workflow.payload(final, negative)
    except ValueError as exc:
        return ['short workflow: '+str(exc)]
    if negative:
        target=run/'workspace/銷售 資料'
        expected=str(target if manifest['case']=='missing' else target/'sales.xlsx')
        kind='FileNotFoundError' if manifest['case']=='missing' else 'BadZipFile'
        errors=[]
        if set(response)!={'path','error_type','error_message'} or response.get('path')!=expected or response.get('error_type')!=kind or not response.get('error_message'):
            errors.append('short workflow: exact failing path/exception missing')
        if not any(workflow.executed(t,'check_excel.py',1) and workflow.output(t)==response for t in tools):
            errors.append('short workflow: no real failed inspection matching final error')
        return errors
    try:
        answer=json.loads((run/'workspace/answer.json').read_text())
    except (OSError,ValueError):
        return ['short workflow: missing answer.json']
    errors=[]
    if response!=answer:errors.append('short workflow: final differs from answer.json')
    inspect=[i for i,t in enumerate(tools) if workflow.executed(t,'check_excel.py',0)
             and all(word in t.get('state',{}).get('output','') for word in (*workflow.HEADERS,'datetime','str','int'))]
    if not inspect or not any(i>inspect[0] and workflow.executed(t,'analysis.py',0) and workflow.output(t)==answer for i,t in enumerate(tools)):
        errors.append('short workflow: actual header/type exploration must precede JSON analysis stdout')
    return errors
