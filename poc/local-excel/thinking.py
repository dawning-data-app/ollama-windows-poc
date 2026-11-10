"""Approved thinking-only experiment and evaluator; no Excel analyzer."""
from copy import deepcopy
from pathlib import Path
import json
import re
import aligned
import poc
import shortflow
import workflow

VERSION = 'excel-thinking-v1'
EFFORT = 'medium'
PROBE_LEAD = '本機工具已完成。'
MARKER = 'LOCAL_TOOL_OK'


def configuration(base: dict) -> dict:
    result = aligned.configuration(base)
    result['provider']['ollama']['models'][poc.MODEL]['options']['reasoningEffort'] = EFFORT
    return result


def validate(config: dict) -> None:
    if config != configuration(poc.config(poc.MODEL)):
        raise ValueError('thinking config differs from approved aligned baseline plus medium effort')


def probe_prompt(workspace: Path) -> str:
    return f'''這是本機工具鏈探測，不分析 Excel。
請在本次工作區 {workspace} 自主寫 runtime_probe.py，實際以 `uv run --locked --offline python runtime_probe.py` 執行。
程式 stdout 只印一個 JSON，欄位為 marker（字串 {MARKER}）、python（實際 sys.executable）、prefix（實際 sys.prefix）。
最後只回「{PROBE_LEAD}」及一個 json 區塊，複製實際 stdout。不要只給計畫或尚未執行的程式碼。
不讀 Excel，不安裝套件，不改設定／鎖檔，不查工作區外資料。'''


def review(run: Path, manifest: dict, tools: list[dict], final: str) -> list[str]:
    errors = []
    try:
        validate(poc.read_json(run / 'workspace/opencode.json'))
    except (OSError, ValueError, KeyError) as exc:
        errors.append('thinking workflow: ' + str(exc))
    try:
        messages = poc.read_json(run / 'evidence/session-export.json')['messages']
        traces = [p.get('text', '').strip() for m in messages if m['info']['role'] == 'assistant'
                  for p in m['parts'] if p['type'] == 'reasoning' and p.get('text', '').strip()]
    except (OSError, ValueError, KeyError):
        traces = []
    poc.write_json(run / 'evidence/thinking-observation.json',
                   {'nonempty_reasoning_parts': len(traces), 'reasoning_characters': sum(map(len, traces)),
                    'content_not_used_as_final_answer': True})
    if not traces:
        errors.append('thinking workflow: no actual nonempty reasoning signal observed')
    if not manifest.get('probe'):
        return errors + shortflow.review(run, manifest, tools, final)
    match = re.fullmatch(re.escape(PROBE_LEAD) + r'\s*```json\s*(\{[\s\S]*\})\s*```\s*', final.strip())
    try:
        response = json.loads(match.group(1)) if match else None
    except ValueError:
        response = None
    expected = {'marker': MARKER, 'python': str(run / 'workspace/.venv/bin/python'),
                'prefix': str(run / 'workspace/.venv')}
    if response != expected:
        errors.append('thinking probe: final must match actual session Python JSON')
    if not any(workflow.executed(t, 'runtime_probe.py', 0) and workflow.output(t) == expected for t in tools):
        errors.append('thinking probe: no real successful uv Python probe matching final')
    return errors
