"""Experimental opt-in IDE instructions and evaluator checks; no supplied analyzer."""
from __future__ import annotations
import json
import math
from pathlib import Path
import re
import shlex

VERSION = 'excel-evidence-v2'
NORMAL_LEAD = '已完成實際讀檔與 Python 計算，結果如下。'
ERROR_LEAD = '無法分析指定路徑，實際錯誤如下。'
HEADERS = {'date', 'region', 'product', 'quantity', 'unit_price'}


def prompt(folder: Path, negative: bool = False) -> str:
    task = ('讀取失敗時回報真實錯誤，不可編造數字，不可建立 answer.json。' if negative else
            '計算總銷售額、各月銷售額、各區域銷售額與銷售額由高到低排名。金額=quantity*unit_price。'
            'answer.json 僅含 total_sales（數字）、monthly_sales（YYYY-MM 到數字的物件）、'
            'regional_sales（區域到數字的物件）、region_ranking（區域名稱陣列）。')
    return f'''請分析這個資料夾內的 Excel：{folder}
{task}
請自主撰寫並執行 Python；沒有提供任何分析程式或答案。openpyxl 已安裝，使用工作表 Sales。
依次完成以下流程，不可猜欄位位置或資料型別：
1. 先用檔案寫入工具建立短小完整的 explore_excel.py，再執行 `uv run --locked --offline python explore_excel.py`。
   Python 必須實際列舉上面完整、精確的資料夾路徑，再以 openpyxl 開啟其中 .xlsx；不可換成 workspace 根目錄或其他路徑。不可先寫完整分析器而跳過探索。
   成功時探索真實欄名、第一筆資料各欄 Python 型別、region 與 product 各自所有不同值；依欄名定位，不能假設第幾欄。
   把探索結果存成 inspection.json 並在 stdout 印出相同 JSON：path（指定資料夾完整路徑）、file（實際 Excel 完整路徑）、sheet、headers（欄名陣列）、types（欄名到 Python 型別名稱）、region_values、product_values。
   若實際列舉／開啟失敗：捕獲真實例外，在 stdout 僅印一個 JSON，欄位 path（真正失敗的完整路徑）、error_type（例外類別名稱）、error_message（原始例外訊息），以非零結束；到此停止，不寫 answer.json、不建立輸入資料夾、不改查父目錄。不要依大小猜格式或猜刪除／傳輸原因。
2. 探索成功後，才自主用寫入工具建立短小完整的 analysis.py。根據剛才實際觀察的欄名與型別，按欄名讀 date、region、product、quantity、unit_price；region 分組只取 region，不能取 product。
   日期依真實型別轉 YYYY-MM，不能靜默跳過無法處理的資料。只跳過一次表頭。區域結果的鍵須與實際探索的 region_values 相符，排名包含同一集合且按金額遞減；月額加總及區域額加總均須等於總額。用 Python 檢查這些條件，失敗先自行修程式，不要宣稱完成。
   執行 `uv run --locked --offline python analysis.py`；成功時由這支自主程式寫 answer.json，stdout 僅印相同的四欄位 JSON。讀回 answer.json 核對與實際執行 stdout 一致後才回答。
3. 最後用繁體中文回答。成功只寫「{NORMAL_LEAD}」接一個 json 程式碼區塊，內容逐項取自實際執行的四欄位 JSON。
   失敗只寫「{ERROR_LEAD}」接一個 json 程式碼區塊，內容與實際錯誤 stdout 的三欄位 JSON 相同。
   最後回答不要加入其他句子、數字、筆數、比例、成長率、幣別、推測原因、檔案大小門檻或未計算的交叉分組；不要把失敗說成分析成功。
不要用 read 工具直接讀二進位 Excel，不安裝套件，不讀工作區外檔案。資料、uv.lock、opencode.json 保持原樣。不要只交尚未執行的程式碼。
'''


def executed(part: dict, filename: str, exit_code: int) -> bool:
    state = part.get('state', {})
    if part.get('tool') != 'bash' or state.get('status') != 'completed' or state.get('metadata', {}).get('exit') != exit_code:
        return False
    try:
        args = shlex.split(state.get('input', {}).get('command', ''))
    except ValueError:
        return False
    prefix = ['uv', 'run', '--locked', '--offline', 'python']
    return any((i == 0 or args[i-1] in ('&&', ';')) and args[i:i+5] == prefix
               and Path(args[i+5]).name == filename for i in range(max(0, len(args)-5)))


def payload(final: str, negative: bool) -> dict:
    lead = ERROR_LEAD if negative else NORMAL_LEAD
    match = re.fullmatch(re.escape(lead) + r'\s*```json\s*(\{.*\})\s*```\s*', final.strip(), re.S)
    if not match:
        raise ValueError('final must contain only the Traditional Chinese lead and one JSON block')
    value = json.loads(match[1])
    if not isinstance(value, dict):
        raise ValueError('final JSON must be an object')
    return value


def output(part: dict) -> dict | None:
    try:
        value = json.loads(part.get('state', {}).get('output', '').strip())
        return value if isinstance(value, dict) else None
    except (ValueError, TypeError):
        return None


def review(run: Path, manifest: dict, tools: list[dict], final: str) -> list[str]:
    """Evaluator only: actual stdout/ordering/final checks; oracle remains separate."""
    errors = []
    negative = manifest['case'] != 'sales'
    target = str(run / 'workspace/銷售 資料')
    try:
        response = payload(final, negative)
    except ValueError as exc:
        return ['workflow: ' + str(exc)]
    if negative:
        expected_path = target if manifest['case'] == 'missing' else str(Path(target) / 'sales.xlsx')
        expected_type = 'FileNotFoundError' if manifest['case'] == 'missing' else 'BadZipFile'
        if (set(response) != {'path', 'error_type', 'error_message'} or response.get('path') != expected_path
                or response.get('error_type') != expected_type or not response.get('error_message')):
            errors.append('workflow: error must identify the exact failing input path and real exception')
        if not any(executed(t, 'explore_excel.py', 1) and output(t) == response for t in tools):
            errors.append('workflow: no actual inspection Python error matching final response')
        return errors
    try:
        inspection = json.loads((run / 'workspace/inspection.json').read_text())
        answer = json.loads((run / 'workspace/answer.json').read_text())
        if (inspection.get('path') != target or inspection.get('file') != str(Path(target) / 'sales.xlsx')
                or inspection.get('sheet') != 'Sales' or set(inspection.get('headers', [])) != HEADERS
                or set(inspection.get('types', {})) != HEADERS
                or not all(isinstance(v, str) and v for v in inspection.get('types', {}).values())
                or not inspection.get('region_values') or not inspection.get('product_values')):
            errors.append('workflow: incomplete actual path/header/type/group exploration')
        types = inspection.get('types', {})
        if (types.get('date') not in ('datetime', 'datetime.datetime', 'date', "<class 'datetime.datetime'>")
                or any(types.get(k) not in ('str', "<class 'str'>") for k in ('region', 'product'))
                or any(types.get(k) not in ('int', 'float', "<class 'int'>", "<class 'float'>") for k in ('quantity', 'unit_price'))):
            errors.append('workflow: reported types do not match the frozen nonempty workbook schema')
        if set(answer['regional_sales']) != set(inspection['region_values']):
            errors.append('workflow: regional groups differ from inspected region values')
        values = [answer['total_sales'], *answer['monthly_sales'].values(), *answer['regional_sales'].values()]
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values):
            errors.append('workflow: amounts must be finite numbers')
        if not all(re.fullmatch(r'\d{4}-\d{2}', k) for k in answer['monthly_sales']):
            errors.append('workflow: months must use YYYY-MM keys')
        if (not math.isclose(sum(answer['monthly_sales'].values()), answer['total_sales'], abs_tol=1e-9)
                or not math.isclose(sum(answer['regional_sales'].values()), answer['total_sales'], abs_tol=1e-9)):
            errors.append('workflow: monthly/regional totals do not reconcile')
        if answer['region_ranking'] != sorted(answer['regional_sales'], key=answer['regional_sales'].get, reverse=True):
            errors.append('workflow: ranking does not follow actual regional amounts')
        if response != answer:
            errors.append('workflow: final response differs from actual answer.json')
        inspections = [i for i,t in enumerate(tools) if executed(t, 'explore_excel.py', 0) and output(t) == inspection]
        if not inspections or not any(i > inspections[0] and executed(t, 'analysis.py', 0) and output(t) == answer for i,t in enumerate(tools)):
            errors.append('workflow: inspection must execute before analysis with matching JSON stdout')
    except (OSError, ValueError, KeyError, TypeError):
        errors.append('workflow: missing or invalid inspection/answer evidence')
    return errors
