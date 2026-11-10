# 本機 Excel 分析 POC

在 VS Code 的 OpenCode 對話提供資料夾路徑，由 Ollama 的本機 Qwen 自主寫 Python、讀 Excel 並計算。先驗收 Mac，再以同一模型 digest、資料與 uv 鎖檔到原生 Windows 重現。既有 tinyllama CLI 不變。

本次預設候選已選為 `qwen3.5:9b`；[實測紀錄與待驗證項目](docs/verification.md)。

這是可核對的最小情境：12 筆合成銷售資料，不代表大型或髒資料的效能評估。`poc.py` 只準備環境與核對結果，不替受測代理提供分析程式。

本機互動流程圖：[workflow.html](diagrams/workflow.html)；[驗證 receipt](diagrams/receipt.json)。圖件是流程說明，不是 E2E 通過證據。

## VS Code extension 增量

官方 extension 的終端 TUI 與 OpenChamber 側邊欄操作見 [extension 教程](docs/extensions.md)、[最小可行性 E001](../../experiments/E001/README.md)／[E002](../../experiments/E002/README.md) 及 [各介面驗證紀錄](docs/extension-verification.md)。固定版本與現有 backend 分開核對；原 CLI/TUI 基準保留。 2026-11-06 的兩介面三輪正常 JSON 皆為 2/3 符合，仍有分析／敘述錯誤，側欄 corrupt 最後 GUI 回答已於解鎖後補看，仍有敘述限制；Mac 未通過完整驗收，Windows 未開始。

2026-11-10 修正續作：[新批次紀錄](docs/repair-verification.md)。兩版探索流程 MVP 未成立，正式十例未執行；原結果保留，Mac 驗收目標仍未達成。

使用者追加的 30 分鐘 [E006 短式流程 MVP](docs/short-verification.md) 已到限：正常未完成、missing 錯誤／路徑契約失敗、corrupt 未送出；完整三例仍有缺口，不進正式重驗。

## 受測 profile

使用專用 `excel` primary agent，明確告知 openpyxl 已安裝，但不提供分析程式或標準答案。主／輔模型都是本機同一 Qwen。採 coding sampler：temperature 0.6、top_p 0.95、top_k 20、min_p 0、presence_penalty 0、repeat_penalty 1；OpenCode 宣告 reasoning 能力與 `reasoning_content` replay，並以 `reasoningEffort: none` 關閉本次對話的 thinking。這個模式組合是本 POC 的測試選擇，採樣數值參照官方 coding 建議。[Qwen 官方 coding 建議](https://huggingface.co/Qwen/Qwen3.5-4B#best-practices)。診斷過程使用過的預設、未調整採樣的 non-thinking 及 thinking profile 分開留證，不算這組配置通過。

執行器用 `uv run --locked --offline` 啟動 OpenCode，並把該 session 的 `.venv` 放在 PATH 首位，因此代理的 `python ...` 短命令也使用該次 uv 環境。`evidence/python-runtime.stdout` 記錄實際 interpreter；不依賴全域 openpyxl。推薦分析命令仍是 `uv run --locked --offline python analysis.py`。

## 1. 準備工具

Mac 先安裝並啟動 VS Code、Ollama，以及 Node.js、uv。已有者沿用。[Ollama](https://ollama.com/download)、[VS Code](https://code.visualstudio.com/)、[uv 安裝](https://docs.astral.sh/uv/getting-started/installation/)。

在 **feature worktree** 的本目錄開 VS Code：

```sh
cd <feature-worktree>/poc/local-excel
code .
uv sync --locked
npm install --prefix /private/tmp/local-excel-poc/opencode opencode-ai@1.19.5 --no-audit --no-fund
ollama pull qwen3.5:9b
```

這裡的 OpenCode 僅安裝到暫存工具目錄。固定 Python 3.12.12、openpyxl 3.1.5，uv 鎖檔也會複製至受測 session。不要把其他分析腳本、oracle 或過往回答複製進去。

## 2. 設定真實 context

OpenCode 模型宣告的 `limit.context` **不會**自動設定 Ollama 的執行 context。[官方整合要求 64k+](https://docs.ollama.com/integrations/opencode)。本 POC 使用官方 [Modelfile](https://docs.ollama.com/modelfile) 將本次候選模型的 `num_ctx` 與 coding 參數明確固定。不要改既有 tinyllama 配置。記錄任何模型參數調整前後的 digest，Windows 必須重現同一 digest。

若要保留既有 Ollama 服務，不改全域 context，可只調整**本次新下載的 Qwen tag**。先記錄原始 digest，再設定參數；這會產生新的本機 manifest digest，必須在 Windows 做相同步驟並核對。不要對既有 tinyllama 操作：

```sh
ollama list
ollama stop qwen3.5:9b
cat > /private/tmp/local-excel-poc/Modelfile <<'MODEL'
FROM qwen3.5:9b
PARAMETER num_ctx 65536
PARAMETER temperature 0.6
PARAMETER top_p 0.95
PARAMETER top_k 20
PARAMETER min_p 0
PARAMETER presence_penalty 0
PARAMETER repeat_penalty 1
MODEL
ollama create qwen3.5:9b -f /private/tmp/local-excel-poc/Modelfile
ollama list
```

在沒有其他服務佔用 11434 時，可於另一個終端啟動專用的本機服務：

```sh
OLLAMA_HOST=127.0.0.1:11434 OLLAMA_CONTEXT_LENGTH=65536 OLLAMA_NO_CLOUD=1 ollama serve
```

服務已在運作時不要再啟動第二個相同埠；由操作者決定適當的服務重啟時機。設定後實際檢查，不能因下載成功或記憶體為 18 GB 就判定可用：

```sh
uv run --locked python poc.py preflight --output /private/tmp/local-excel-poc/qualification.json
ollama ps
```

資格檢查會驗證本機模型、tools capability、最小工具呼叫及實際 65536 context。失敗就停該階段；不切雲端、不降 context。本次依原先的 4b → 9b 篩選順序選用 9b；4b 未達完整對話重現門檻。9b 已完成三次 CLI 重現，GUI 與 Windows 狀態另見驗證紀錄。若要重測 4b，先為該 tag 準備相同參數，再用 `prepare --model qwen3.5:4b-q4_K_M`，結果分開記錄。

## 3. VS Code 對話操作

在 VS Code 的整合終端執行：

```sh
uv run --locked python poc.py prepare
```

輸出是一個全新 run 目錄，例如 `/private/tmp/local-excel-poc/runs/<run-id>`；實際系統暫存根目錄可能不同。把它存成 `$Run`，再啟動受控的 OpenCode TUI：

```sh
Run="<上一步輸出的完整run目錄>"
cat "$Run/workspace/prompt.txt"
# 先複製這份提示，再啟動 TUI 並貼上
uv run --locked python poc.py tui "$Run" --opencode /private/tmp/local-excel-poc/opencode/node_modules/.bin/opencode
```

啟動器先核對設定，在終端印出本次完整提示。進入 OpenCode 後，貼上該提示：請分析 workspace 內「銷售 資料」資料夾，計算總額、月額與區域排名。代理必須自行寫 `analysis.py`，並真正執行 `uv run --locked --offline python analysis.py`。

`answer.json` 是機器核對用證據，不是額外交付的報表產品。對話中也要有繁體中文的結果。若終端暫時空白，可先按 Ctrl+L 重新繪製；不要盲目重送提示。保存 session ID、畫面及工具軌跡供人核對；`tui` 狀態是 `interactive-needs-review`，不會自動宣稱 E2E 通過。

## 4. 三次可重跑的 CLI 驗證

自動 CLI 與 VS Code TUI 使用相同配置，但 CLI 通過不能取代實際 VS Code 操作證據。在本目錄每次重新執行：

```sh
uv run --locked python poc.py prepare
Run="<本次輸出的完整run目錄>"
uv run --locked python poc.py run "$Run" --opencode /private/tmp/local-excel-poc/opencode/node_modules/.bin/opencode
uv run --locked python poc.py check "$Run"
```

共做三次 sales；每次使用新的 run，不使用 `--continue`，不重用生成的程式。`run` 先 `uv sync --locked`，然後代理執行時不新增依賴。`--timeout 900` 是避免失控等待的操作上限，不是效能合格線。

再分別 `prepare --case missing` 與 `prepare --case corrupt`，同樣 run/check。核對錯誤敘述且沒有編造結果。不存在的資料夾可在導覽時直接報錯，不要求為失敗輸入建立分析腳本。負面案例的敘述需人審，check 不會自動判定其通過。

`check` 僅能判定數值及部分工具證據；成功時仍是 `needs-review`、`e2e_passed: false`。測試者還須檢視生成程式確實讀 XLSX、程式執行輸出、主／輔模型身份與路由、答案未污染、實際 VS Code 操作；完成後另記錄人審結論。工作區分開不等於 OS sandbox，Python 仍有本機程式權限，僅測公開合成資料。

## 5. Windows 原生重現

**Mac 完整驗收前不執行 Windows E2E。** 先在 Windows 安裝 VS Code、Git、Ollama、Node.js 與 uv，確認 GPU／RAM／磁碟，取得同一 feature 分支。在 VS Code 的 PowerShell：

```powershell
Set-Location <feature-worktree>\poc\local-excel
uv sync --locked
$ToolRoot = Join-Path $env:TEMP 'local-excel-poc\opencode'
npm install --prefix $ToolRoot opencode-ai@1.19.5 --no-audit --no-fund
$OpenCode = Join-Path $ToolRoot 'node_modules\.bin\opencode.cmd'
ollama pull qwen3.5:9b
# 完全結束原 Ollama 後，於另一個 PowerShell 啟動：
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_CONTEXT_LENGTH = '65536'
$env:OLLAMA_NO_CLOUD = '1'
ollama serve
```

回到原 PowerShell，確認模型 digest 與 Mac 相同；若 Mac 使用了本機 Modelfile 參數，Windows 同樣建置後再比對：

```powershell
$ModelFile = Join-Path $env:TEMP 'local-excel-poc\Modelfile'
ollama stop qwen3.5:9b
@'
FROM qwen3.5:9b
PARAMETER num_ctx 65536
PARAMETER temperature 0.6
PARAMETER top_p 0.95
PARAMETER top_k 20
PARAMETER min_p 0
PARAMETER presence_penalty 0
PARAMETER repeat_penalty 1
'@ | Set-Content -Encoding ascii $ModelFile
ollama create qwen3.5:9b -f $ModelFile
ollama list
```

不要悄悄改模型或硬體配置後稱為同配置重現。

```powershell
$RunRoot = Join-Path $env:TEMP 'local-excel-poc\runs'
uv run --locked python poc.py preflight --output (Join-Path $RunRoot 'qualification.json')
$Run = uv run --locked python poc.py prepare --runs-root $RunRoot
Get-Content -Raw -Encoding utf8 (Join-Path $Run 'workspace\prompt.txt')
# 先複製完整提示；進入 TUI 後貼上並送出
uv run --locked python poc.py tui $Run --opencode $OpenCode
# CLI 三次驗證，每次重新 prepare：
$Run = uv run --locked python poc.py prepare --runs-root $RunRoot
uv run --locked python poc.py run $Run --opencode $OpenCode
uv run --locked python poc.py check $Run
```

Windows shell、CLI 與 GPU 的實際相容性必須在該機驗證；本 repo 的單元測試不代表 Windows E2E 已通過。

## 排查與測試

| 現象 | 處理 |
|---|---|
| connection refused | 檢查本機 Ollama 是否啟動及 11434；不改連雲端。 |
| model missing / tools 不支援 | 檢查完整 tag 與 `/api/show`；不可拿 tinyllama 取代。 |
| context 不足 / OOM | 查 `ollama ps` 與服務參數；停階段留證，不縮 context 冒充通過。 |
| effective-config 失敗 | 檢查 `evidence`；使用安裝版本支援的設定。主模型、小模型、allowlist 與 endpoint 都須正確。 |
| 工具被拒或 answer.json 缺失 | 看工具軌跡；由代理修正工具使用，不先提供固定分析腳本。 |
| 数值對但 needs-review | 完成獨立人審；數值對不等於真實讀檔、路由與答案隔離已證實。 |

```sh
uv run --locked python -m unittest discover -s tests -v
# repo 根目錄：既有功能回歸
python3 -m unittest discover -s tests -v
```

設定依據：[OpenCode 配置](https://opencode.ai/docs/config/)、[權限](https://opencode.ai/docs/permissions/)、[uv 鎖檔](https://docs.astral.sh/uv/concepts/projects/sync/)。

Extension 增量的 Mac 執行邊界：[隔離架構圖](diagrams/extensions-isolated.html)／[receipt](diagrams/extensions-isolated.receipt.json)。新 fresh session 必須使用已驗證的 policy；此圖不代表完整 E2E 通過。

上述 OS 邊界涵蓋 ide.py 的 extension sessions；原 CLI/TUI 基準保留其已記錄的非 OS 隔離限制，請勿混稱為受限驗證。

E007 [單視窗基線與三例結果](docs/baseline-verification.md)：GUI／API 可觀察，但正常格式、missing、corrupt 流程仍不通過。使用者已同意限定指令修訂與另一輪三例 MVP；不直接進正式重驗。

[E008 限定指令修訂](docs/aligned-verification.md) 已以新 config hash實作，40/40 POC測試通過；正常只完成探索後自行停止，missing／corrupt因GUI不可得未送出。完整MVP與Mac驗收未完成，原預設保留。
