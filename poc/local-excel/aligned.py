"""Approved opt-in instruction alignment; no supplied Excel analyzer."""
from copy import deepcopy
from pathlib import Path
import poc
import shortflow

VERSION = 'excel-aligned-v1'
SYSTEM_PROMPT = (
    'You are a local Excel analysis agent. openpyxl is already installed in this workspace uv environment. '
    'Follow the user-provided target directory exactly. Autonomously write and execute a short runnable Python inspection first. '
    'On directory or workbook read errors, report the actual exception and exact failing path, then stop; '
    'do not search parent directories or other locations, create substitute inputs, or produce an analysis result. '
    'Only after successful inspection, autonomously write and execute analysis.py with bash: uv run --locked --offline python analysis.py. '
    'The python command also points to this session uv environment. Actually read and calculate workbook data. '
    'Do not install packages. Follow the requested answer format and reply in Traditional Chinese.'
)


def configuration(base: dict) -> dict:
    result = deepcopy(base)
    result['agent']['excel']['prompt'] = SYSTEM_PROMPT
    return result


def validate(config: dict) -> None:
    if config != configuration(poc.config(poc.MODEL)):
        raise ValueError('aligned config may change only the approved agent.excel.prompt')


def prompt(folder: Path, negative: bool = False) -> str:
    text = shortflow.prompt(folder, negative)
    text = text.replace(
        'analysis.py 寫 answer.json，stdout 只印相同 JSON，僅含 total_sales、monthly_sales、regional_sales、region_ranking。',
        f'analysis.py 寫 {folder.parent / "answer.json"}（本次 workspace 內），stdout 只印相同 JSON，僅含 '
        'total_sales（數字）、monthly_sales（YYYY-MM 到數字的物件）、regional_sales（區域到數字的物件）、'
        'region_ranking（依金額遞減的區域名稱陣列）。')
    return text.replace('若實際列目錄／開啟檔案失敗，印出 JSON：',
                        '若實際列目錄／開啟檔案失敗，stdout 僅印一個錯誤 JSON：')


def review(run: Path, manifest: dict, tools: list[dict], final: str) -> list[str]:
    errors = []
    try:
        validate(poc.read_json(run / 'workspace/opencode.json'))
    except (OSError, ValueError, KeyError) as exc:
        errors.append('aligned workflow: ' + str(exc))
    return errors + shortflow.review(run, manifest, tools, final)
