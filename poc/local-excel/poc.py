"""Prepare isolated sessions and verify evidence, never provide an analysis solution.

The oracle stays on the evaluator side. A separate directory prevents accidental
prompt contamination; it is not an operating-system sandbox.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.request import ProxyHandler, Request, build_opener
import uuid

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parent
MODEL = "qwen3.5:4b-q4_K_M"
CONTEXT = 65536
BASE_URL = "http://localhost:11434"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def api(endpoint: str, body: dict | None = None, timeout: float = 30) -> dict:
    request = Request(BASE_URL + endpoint,
                      data=None if body is None else json.dumps(body).encode(),
                      headers={"Content-Type": "application/json"})
    # Always contact loopback directly, independent of inherited HTTP proxies.
    with build_opener(ProxyHandler({})).open(request, timeout=timeout) as response:
        result = json.load(response)
    if not isinstance(result, dict) or "error" in result:
        raise ValueError(f"Ollama API error: {result}")
    return result


def make_fixture(path: Path) -> None:
    book = Workbook()
    sheet = book.active
    sheet.title = "Sales"
    sheet.append(["date", "region", "product", "quantity", "unit_price"])
    quantity = 0
    for month in (1, 2):
        for region in ("北", "中", "南"):
            for product, price in (("A", 100), ("B", 200)):
                quantity += 1
                sheet.append([datetime(2026, month, 1), region, product, quantity, price])
    sheet.freeze_panes = "A2"
    sheet.column_dimensions["A"].width = 22
    path.parent.mkdir(parents=True, exist_ok=True)
    book.save(path)
    book.close()


def config(model: str) -> dict:
    model_id = f"ollama/{model}"
    return {
        "$schema": "https://opencode.ai/config.json",
        "model": model_id, "small_model": model_id,
        "enabled_providers": ["ollama"], "autoupdate": False,
        "share": "disabled", "snapshot": False, "plugin": [],
        "lsp": False, "formatter": False,
        "provider": {"ollama": {
            "npm": "@ai-sdk/openai-compatible", "name": "Local Ollama",
            "options": {"baseURL": BASE_URL + "/v1"},
            "models": {model: {"name": model, "tool_call": True,
                               "limit": {"context": CONTEXT, "output": 8192}}},
        }},
        "default_agent": "excel",
        "agent": {"excel": {"mode": "primary", "model": model_id,
                              "temperature": 0, "steps": 20,
                              "description": "Analyze local Excel using Python tools"}},
        "permission": {
            "*": "deny", "read": "allow", "glob": "allow", "grep": "allow",
            "edit": "allow", "external_directory": "deny",
            "bash": {"*": "deny", "uv run --locked --offline python *": "allow"},
        },
    }


def prompt(folder: Path, negative: bool = False) -> str:
    task = ("讀取失敗時請清楚說明錯誤，不可編造數字，也不要建立 answer.json。" if negative else
            '計算總銷售額、各月銷售額、各區域銷售額與由高到低排名。金額=quantity*unit_price。'
            '在對話中用繁體中文說明結果，並將核對用的結果存為 answer.json，欄位為 '
            'total_sales（數字）、monthly_sales（YYYY-MM到數字的物件）、regional_sales（區域到數字的物件）、'
            'region_ranking（區域名稱陣列）。數值必須來自實際讀檔與計算。')
    return (f'請分析這個資料夾內的 Excel：{folder}\n{task}\n'
            '工作表為 Sales，date是日期、region是區域、product是商品、quantity是數量、unit_price是單價。\n'
            '請自主使用檔案寫入工具建立 analysis.py，再以 bash 工具執行 '
            '`uv run --locked --offline python analysis.py`。使用 openpyxl 讀 .xlsx；'
            '不要用 read 工具直接讀二進位 Excel。不要安裝套件或讀取工作區外的檔案。'
            '不得改寫資料、uv鎖檔或OpenCode設定。不要只給使用者尚未執行的程式碼。')


def prepare(runs_root: Path, case: str = "sales", model: str = MODEL) -> Path:
    runs_root = runs_root.resolve()
    # Evaluation assets must never become descendants of an agent workspace.
    if runs_root == ROOT or ROOT in runs_root.parents:
        raise ValueError("runs-root must be outside the tracked POC assets")
    run = runs_root / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8])
    workspace = run / "workspace"
    workspace.mkdir(parents=True)
    for name in ("pyproject.toml", "uv.lock", ".python-version"):
        shutil.copy2(ROOT / name, workspace / name)
    folder = workspace / "銷售 資料"
    if case != "missing":
        folder.mkdir()
        if case == "corrupt":
            (folder / "sales.xlsx").write_bytes(b"This is not an Excel archive")
        else:
            shutil.copy2(ROOT / "sales.xlsx", folder / "sales.xlsx")
    write_json(workspace / "opencode.json", config(model))
    (workspace / "prompt.txt").write_text(prompt(folder, case != "sales"), encoding="utf-8")
    write_json(run / "manifest.json", {
        "case": case, "model": model, "context": CONTEXT,
        "platform": platform.platform(), "workspace": str(workspace),
        "fixture_sha256": sha256(folder / "sales.xlsx") if case != "missing" else None,
        "lock_sha256": sha256(workspace / "uv.lock"),
        "config_sha256": sha256(workspace / "opencode.json"),
        "status": "prepared", "blind_test": "not_os_isolated",
    })
    return run


def environment(run: Path) -> dict[str, str]:
    # Keep OS necessities; never inherit provider keys or OpenCode inline overrides.
    keys = ("PATH", "HOME", "USERPROFILE", "SYSTEMROOT", "WINDIR", "COMSPEC",
            "PATHEXT", "TEMP", "TMP", "LANG", "LC_ALL", "TERM")
    env = {key: os.environ[key] for key in keys if key in os.environ}
    for key, folder in (("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "state"),
                        ("XDG_STATE_HOME", "state"), ("XDG_CACHE_HOME", "cache")):
        env[key] = str(run / folder)
    env.update({"OPENCODE_CONFIG": str(run / "workspace" / "opencode.json"),
                "OPENCODE_CONFIG_CONTENT": (run / "workspace" / "opencode.json").read_text(encoding="utf-8"),
                "OPENCODE_DISABLE_AUTOUPDATE": "true", "OPENCODE_DISABLE_DEFAULT_PLUGINS": "true",
                "OPENCODE_DISABLE_MODELS_FETCH": "true", "OPENCODE_DISABLE_LSP_DOWNLOAD": "true"})
    return env


def validate_config(effective: dict, model: str) -> None:
    expected = f"ollama/{model}"
    if effective.get("model") != expected or effective.get("small_model") != expected:
        raise ValueError("effective main/small model differs from local candidate")
    if effective.get("enabled_providers") != ["ollama"]:
        raise ValueError("effective provider allowlist is not local-only")
    if effective.get("provider", {}).get("ollama", {}).get("options", {}).get("baseURL") != BASE_URL + "/v1":
        raise ValueError("effective Ollama endpoint differs from loopback")
    if effective.get("mcp") or effective.get("plugin"):
        raise ValueError("unexpected MCP/plugin in merged config; inspect before running")
    for name, agent in effective.get("agent", {}).items():
        if isinstance(agent, dict) and agent.get("model", expected) != expected:
            raise ValueError(f"agent {name} overrides local model")


def preflight(model: str) -> dict:
    started = time.monotonic()
    tags = api("/api/tags")["models"]
    found = next((entry for entry in tags if entry["name"] == model), None)
    if found is None:
        raise ValueError(f"model missing: ollama pull {model}")
    show = api("/api/show", {"model": model})
    if "tools" not in show.get("capabilities", []):
        raise ValueError("model does not advertise tools capability")
    # Native API probe qualifies actual loaded context and tool calling.
    response = api("/api/chat", {
        "model": model, "stream": False, "think": False,
        "options": {"num_ctx": CONTEXT, "temperature": 0}, "keep_alive": "10m",
        "messages": [{"role": "user", "content": "Call local_probe with value 7. Do not answer in text."}],
        "tools": [{"type": "function", "function": {"name": "local_probe", "description": "Local test",
                  "parameters": {"type": "object", "properties": {"value": {"type": "integer"}},
                                 "required": ["value"]}}}],
    }, timeout=300)
    calls = response.get("message", {}).get("tool_calls", [])
    if not any(c.get("function", {}).get("name") == "local_probe" and
               c["function"].get("arguments", {}).get("value") == 7 for c in calls):
        raise ValueError("model failed minimum tool call")
    # OpenCode uses the OpenAI-compatible route, whose context cannot be set
    # by its model.limit declaration. Confirm the real default on that route too.
    api("/v1/chat/completions", {"model": model, "stream": False, "max_tokens": 8,
        "messages": [{"role": "user", "content": "Reply OK."}]}, timeout=300)
    loaded = next((m for m in api("/api/ps")["models"] if m["name"] == model), None)
    if loaded is None or loaded.get("context_length", 0) < CONTEXT:
        raise ValueError("actual loaded context is below 65536")
    return {"status": "qualified", "model": model, "digest": found["digest"],
            "ollama_version": api("/api/version")["version"], "loaded": loaded,
            "model_parameters": show.get("parameters", ""),
            "tool_probe": calls, "elapsed_seconds": round(time.monotonic() - started, 3)}


def command(argv: list[str], run: Path, name: str, timeout: float, env: dict | None = None) -> subprocess.CompletedProcess:
    evidence = run / "evidence"
    evidence.mkdir(exist_ok=True)
    with (evidence / f"{name}.stdout").open("w", encoding="utf-8") as out, (evidence / f"{name}.stderr").open("w", encoding="utf-8") as err:
        return subprocess.run(argv, cwd=run / "workspace", env=env,
                              stdout=out, stderr=err, timeout=timeout, check=False)


def run_agent(run: Path, opencode: str, timeout: float) -> dict:
    run = run.resolve()
    manifest = read_json(run / "manifest.json")
    if manifest["status"] != "prepared":
        raise ValueError("run is not fresh; prepare a new session instead")
    binary = shutil.which(opencode) if not Path(opencode).is_absolute() else opencode
    if not binary or not Path(binary).is_file():
        raise ValueError("OpenCode executable missing; install during environment preparation")
    env = environment(run)
    manifest["status"] = "running"
    write_json(run / "manifest.json", manifest)
    try:
        qualified = preflight(manifest["model"])
        write_json(run / "evidence" / "qualification.json", qualified)
        for name, argv in (("uv-version", ["uv", "--version"]),
                           ("opencode-version", [binary, "--version"]),
                           ("uv-sync", ["uv", "sync", "--locked"]),
                           ("effective-config", [binary, "debug", "config"])):
            if command(argv, run, name, 180, env).returncode:
                raise ValueError(f"{name} failed; see evaluator evidence")
        effective = read_json(run / "evidence" / "effective-config.stdout")
        validate_config(effective, manifest["model"])
        start = time.monotonic()
        result = command([binary, "run", "--format", "json", "--agent", "excel",
                          "--model", f"ollama/{manifest['model']}",
                          (run / "workspace" / "prompt.txt").read_text(encoding="utf-8")],
                         run, "opencode-run", timeout, env)
        manifest["analysis_seconds"] = round(time.monotonic() - start, 3)
        manifest["returncode"] = result.returncode
        manifest["status"] = "recorded" if result.returncode == 0 else "failed"
        write_json(run / "evidence" / "loaded-after.json", api("/api/ps"))
        manifest["digest"] = qualified["digest"]
    except (OSError, ValueError, TimeoutError, subprocess.TimeoutExpired) as exc:
        manifest["status"] = "blocked"
        manifest["error"] = str(exc)
    write_json(run / "manifest.json", manifest)
    return manifest


def interactive(run: Path, opencode: str) -> dict:
    """Launch the same controlled configuration in a real VS Code terminal.

    TUI runs are manual evidence; CLI event verification is deliberately separate.
    """
    run = run.resolve()
    manifest = read_json(run / "manifest.json")
    if manifest["status"] != "prepared":
        raise ValueError("prepare a fresh session for the VS Code demonstration")
    env = environment(run)
    qualified = preflight(manifest["model"])
    write_json(run / "evidence" / "qualification.json", qualified)
    for name, argv in (("uv-sync", ["uv", "sync", "--locked"]),
                       ("effective-config", [opencode, "debug", "config"])):
        if command(argv, run, name, 180, env).returncode:
            raise ValueError(f"{name} failed; inspect evidence")
    validate_config(read_json(run / "evidence" / "effective-config.stdout"), manifest["model"])
    manifest["status"] = "interactive-needs-review"
    manifest["digest"] = qualified["digest"]
    write_json(run / "manifest.json", manifest)
    print((run / "workspace" / "prompt.txt").read_text(encoding="utf-8"), flush=True)
    result = subprocess.run([opencode, "--agent", "excel", "--model", f"ollama/{manifest['model']}"],
                            cwd=run / "workspace", env=env, check=False)
    manifest["returncode"] = result.returncode
    write_json(run / "manifest.json", manifest)
    return manifest


def compare_answer(actual: object, expected: object, path: str = "answer") -> list[str]:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or actual.keys() != expected.keys():
            return [f"{path}: missing or unexpected fields"]
        return [error for key in expected for error in compare_answer(actual[key], expected[key], path + "." + key)]
    if isinstance(expected, (int, float)):
        if isinstance(actual, bool) or not isinstance(actual, (int, float)) or not math.isfinite(actual) or actual != expected:
            return [f"{path}: numeric result differs"]
    elif actual != expected:
        return [f"{path}: value or ranking differs"]
    return []


def check(run: Path) -> dict:
    manifest = read_json(run / "manifest.json")
    workspace = run / "workspace"
    errors = []
    if manifest["status"] != "recorded":
        errors.append("agent run did not finish successfully")
    for filename, field in (("uv.lock", "lock_sha256"), ("opencode.json", "config_sha256")):
        if not (workspace / filename).is_file() or sha256(workspace / filename) != manifest[field]:
            errors.append(f"agent changed protected input: {filename}")
    fixture = workspace / "銷售 資料" / "sales.xlsx"
    if manifest["case"] != "missing" and (not fixture.is_file() or sha256(fixture) != manifest["fixture_sha256"]):
        errors.append("agent changed fixture")
    transcript = run / "evidence" / "opencode-run.stdout"
    events = []
    try:
        events = [json.loads(line) for line in transcript.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, ValueError):
        errors.append("missing or invalid JSON event evidence")
    tools = [event.get("part", {}) for event in events if event.get("type") == "tool_use"]
    executions = [p for p in tools if p.get("tool") == "bash" and p.get("state", {}).get("status") == "completed"
                  and "uv run --locked --offline python" in p.get("state", {}).get("input", {}).get("command", "")]
    if not executions:
        errors.append("no completed Python tool execution evidence")
    if not (workspace / "analysis.py").is_file():
        errors.append("no agent-generated analysis.py")
    if manifest["case"] == "sales":
        try:
            errors.extend(compare_answer(read_json(workspace / "answer.json"), read_json(ROOT / "oracle.json")))
        except (OSError, ValueError):
            errors.append("missing or invalid answer.json")
    else:
        if (workspace / "answer.json").exists():
            errors.append("negative case invented an answer file")
        # Tool output alone is insufficient; the human_checks below also
        # require independent inspection of the negative-case narrative.
    try:
        loaded = read_json(run / "evidence" / "loaded-after.json")["models"]
        if not any(m["name"] == manifest["model"] and m.get("digest") == manifest.get("digest")
                   and m.get("context_length", 0) >= CONTEXT for m in loaded):
            errors.append("post-run model digest/context not confirmed")
    except (OSError, ValueError, KeyError):
        errors.append("missing post-run model evidence")
    report = {"status": "needs-review" if not errors else "not-passed", "errors": errors,
              "case": manifest["case"], "run": run.name,
              "numeric_and_tool_checks_passed": not errors,
              "human_checks": ["inspect script really reads XLSX and computes results",
                               "confirm no oracle/old answers in prompt or tool trace",
                               "confirm session model identity and actual local inference route",
                               "VS Code terminal demo is separate from automated CLI run",
                               "negative-case narrative reports read failure without invented numbers"],
              "e2e_passed": False}
    write_json(run / "verification.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    fixture = commands.add_parser("fixture")
    fixture.add_argument("--output", type=Path, default=ROOT / "sales.xlsx")
    prep = commands.add_parser("prepare")
    prep.add_argument("--runs-root", type=Path, default=Path(tempfile.gettempdir()) / "local-excel-poc" / "runs")
    prep.add_argument("--case", choices=("sales", "missing", "corrupt"), default="sales")
    prep.add_argument("--model", choices=(MODEL, "qwen3.5:9b"), default=MODEL)
    probe = commands.add_parser("preflight")
    probe.add_argument("--model", choices=(MODEL, "qwen3.5:9b"), default=MODEL)
    probe.add_argument("--output", type=Path, required=True)
    runner = commands.add_parser("run")
    runner.add_argument("run_dir", type=Path)
    runner.add_argument("--opencode", default="opencode")
    runner.add_argument("--timeout", type=float, default=900)
    tui = commands.add_parser("tui")
    tui.add_argument("run_dir", type=Path)
    tui.add_argument("--opencode", default="opencode")
    verify = commands.add_parser("check")
    verify.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "fixture":
            make_fixture(args.output)
            print(args.output)
            return 0
        if args.action == "prepare":
            print(prepare(args.runs_root, args.case, args.model))
            return 0
        if args.action == "preflight":
            result = preflight(args.model)
            write_json(args.output, result)
        elif args.action == "run":
            result = run_agent(args.run_dir, args.opencode, args.timeout)
        elif args.action == "tui":
            result = interactive(args.run_dir, args.opencode)
        else:
            result = check(args.run_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") in ("qualified", "recorded", "needs-review", "interactive-needs-review") else 2
    except (OSError, ValueError, KeyError) as exc:
        print(f"POC_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
