# 原生 Windows local-excel POC

Windows 增量以 `e41369371053702483b964a6cac575e4f176bd04` 為 Mac 對照。用獨立的 `feat/andrew/local-excel-windows` worktree。以下命令在 `poc/local-excel` 執行。受測 run、工具、模型、控制技能與證據使用不同的 repo 外目錄。

## 固定工具與檔案

- 使用 Git for Windows、VS Code 1.137.0、Node 24.19.0、uv 0.9.2、CPython 3.12.12、OpenCode 1.19.5、Ollama 0.31.1、`sst-dev.opencode@1.0.0`、`fedaykindev.openchamber@1.24.2`。用官方 x64 資產與發行方可取得的 SHA-256／簽章。VS Code 分別使用專用的 `official` 和 `chamber` extensions 目錄。各次 GUI 啟動另建獨立的 VS Code home 與 user-data。
- `UV_PROJECT_ENVIRONMENT` 指向專用 evaluator 環境，執行 `uv sync --locked --python <Python 3.12.12>`，保留驗證過的 `UV_CACHE_DIR` 供各 run 離線同步。準備案建立 `runtime\Scripts\python.exe`，用複製模式隔開共享 cache，實際核對 3.12.12 和 openpyxl 3.1.5。固定 uv 成立時優先使用這條路。本機 Python 3.13 僅限獨立可行性探測。
- `sales.xlsx` SHA-256 `9d88b6da7175a8e86188b359cf663b16610cdadeca485a9b773f71bb74858fc4`。`uv.lock` SHA-256 `02428609b416acb248ddbf9cde9ca2b9365c8237aff057ad0a9c9e3554d20926`。worktree checkout 用單次 `core.autocrlf=false`，先核對再準備 run。oracle 只由 evaluator 存取。
- 私有模型目錄採 registry 的 `qwen3.5:9b-q4_K_M`，原始 manifest digest `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90`。以該 manifest 核對所有 blob 的 size 和 SHA-256，放入 Ollama store，原樣作為私有的 `qwen3.5:9b` 起點。依原 Modelfile 建立參數化 tag，再核對 `5eb3a683cbfed5baef1d1f24e2f54afd93e8a9ba344ca71eb8bb37129cf545fe` 與實際載入 context `65536`。既有服務使用 11434，Windows POC 專用 21434。

## 事前 OS 政策與資源

準備案的 `policy-request.json` 列出專用 AppContainer 名稱、只讀工具樹、可寫 run 目錄、須拒絕的路徑與網路。準備案成功只代表 fixture、固定工具及離線 Python 建立成功。

由公司核准的管理工具或 IT 提供本案政策，範圍如下。

- 以 run 的 AppContainer SID 授權精確目錄的讀取／執行及寫入；控制 checkout、evaluator／oracle、其他 runs、證據與模型 store 均在代理邊界之外。backend 和其子程序用同一受限 token。以 Job Object 管理擁有的程序樹。
- Windows Filtering Platform 規則須讓該 AppContainer 的 outbound 只到 `127.0.0.1:21434/TCP`，拒絕其他 IPv4／IPv6、DNS、LAN 及 Internet 路由。對 `opencode.exe` 允許受控 loopback listener。官方 1.0.0 會從 16384–65535 選取 TUI 埠，側欄固定 21435。測試期間專用 Ollama 程序亦須封鎖外部 outbound，避免工具經由本機模型 API 取得額外網路能力。 [官方擴充套件固定版原始碼](https://github.com/anomalyco/opencode/blob/v1.19.5/sdks/vscode/src/extension.ts)
- 在 evaluator 端提供 `provisioned-policy.json`，含 `kind`、`run`、`container`、`request_sha256`、`sid`、`wfp_filter_ids` 及 `ollama_wfp_filter_ids`。兩組數字 ID 分別對應該 run 和專用 Ollama 的生效規則，控制帳號需能唯讀查驗。另提供公司核准、可由控制端 TCP 連線的外部測試 IP 與埠作正對照。探測僅建立 TCP 連線，不送資料。收據存在、規則活躍與 sentinel 探測都需成立。
- 需要新增 profile、ACL 或 WFP 規則時，先由使用者與公司管理方決定，範圍只含 POC SID、專用路徑與 listener。先核對停止本輪 Job 和專用埠，再撤除本輪政策、ACL 與 profile。避開全機 loopback exemption 或公司全域政策變更。 [WFP 存取控制](https://learn.microsoft.com/en-us/windows/win32/fwp/access-control)

模型前先連續 30 秒每 5 秒採樣。可用 RAM ≥10 GiB、commit 餘裕 ≥12 GiB、C 槽 ≥10 GiB、run 槽 ≥25 GiB。執行中每 5 秒記錄資源。RAM ≤4 GiB 或 commit 餘裕 ≤6 GiB 連續兩次、pagefile 30 秒內增加 ≥512 MiB、GPU／driver 新錯誤、ready 後 API 連續兩次逾時、或 GUI 15 秒無回應，停止本次 Job 並保存收據。每案最多 600 秒，總截止優先。

## 命令與驗收順序

先記錄台北時間起點與 4 小時總截止。前置 60 分鐘、最小 Excel MVP 30 分鐘、正式 150 分鐘。前置最多兩次有證據的修正。以下為公司政策和資源前提達成後的命令順序。

```powershell
$Root = 'D:\code\python\ollama-windows-poc-local'
$Py = Join-Path $Root 'tools\locked-evaluator\Scripts\python.exe'
# 從本次事前登記的窗口填入帶時區的截止時間。
$Deadline = '<ISO-8601 截止時間>'
$Run = & $Py windows_poc.py prepare --interface chamber --case sales `
    --runs-root (Join-Path $Root 'runs') --tools-root (Join-Path $Root 'tools') `
    --git-root 'C:\Program Files\Git' --deadline $Deadline
# 完成此 run 的 IT provisioning 後，在單獨終端監督本次 Ollama。
& $Py windows_poc.py serve-ollama $Run
```

```powershell
# 另一個控制終端，且 Ollama 21434 ready。
& $Py windows_poc.py boundary-probe $Run --external-ip $ApprovedIP --external-port $ApprovedPort
& $Py windows_poc.py qualify-model $Run
# 於另一控制終端保留這個本次 OpenCode supervisor。
& $Py windows_poc.py serve $Run
```

```powershell
# 真正從 OpenChamber 側欄送出 workspace/prompt.txt 並目視工具及最終回答。
& $Py windows_poc.py launch $Run
# 回答完成並取得 GUI 證據後，停止本次 backend，再收同一 session。
& $Py windows_poc.py finish $Run
& $Py ide.py capture $Run
& $Py ide.py capture $Run --session-id $SessionId
```

- 正常、missing、corrupt 各建立 fresh run，逐案完成相符政策和 sentinel 探測。先做一次單一凍結候選的三案側欄 MVP。三案均成立後，另建正式 CLI、官方 TUI 與側欄各 3 正常、1 missing、1 corrupt，共 15 個 fresh cases。受測時一次只有一個 OpenCode backend 與視窗。到期或安全停止後只做收證。
- CLI 用 `poc.py run <run> --timeout 600` 和 `poc.py check <run>`。官方入口用 `windows_poc.py launch <run>` 開專用視窗後，實測 `Ctrl+Esc`、`Ctrl+Shift+Esc`、`Ctrl+Alt+K`。OS 攔截時記錄實際狀況並用官方 Command Palette 命令。用 `context-probe.txt` 收引用行範圍。確認 scope、參數、cwd、shell、interpreter、實際工具與最終繁中回答。GUI 自動操作不可用時保留同一 session，由操作員完成真正送出與目視收證。
- 正常案以獨立 oracle 檢查 stdout、`answer.json`、最後繁中回答和所有額外事實。欄位包含 `total_sales`、`YYYY-MM` 的 `monthly_sales`、按 region 的 `regional_sales`、金額遞減的 `region_ranking`。missing 需精確指定路徑的真實目錄例外，corrupt 需確實嘗試開啟工作簿並取得真實例外。兩種異常都須留繁中回報且沒有 `answer.json`。
- 各案保留 prompt、fixture、uv.lock、config 的前後 hashes，實際 digest、主輔推論路由、Python source／stdout／stderr／exit、原始 user parts、附加上下文與 GUI 證據。取得全部證據才判斷成功。無最後回答、假例外、額外錯誤敘述和繞查其他路徑均保留為失敗樣本。
- 所有測試完成或停止後，以 `windows_poc.py stop-ollama <run>` 請擁有專用 21434 的 supervisor 停止。檢查埠、PID 及停止收據，再交公司管理方撤除已授權的 POC 政策。

## 九欄位契約

| 欄位 | 本輪範圍 |
|---|---|
| Goal | 原生 Windows 的兩個 VS Code 入口以本機 Qwen 自主撰寫及執行 Python，回報正確分析或真實錯誤。 |
| Non-Goal | 報表產品、模型排名、雲端推論。 |
| In-Scope | Windows adapter、OS 隔離 MVP、資源 watchdog、CLI 與兩 GUI 入口、收證及教程。 |
| Out-Of-Scope | WSL／VM、固定 runtime 升級、自製擴充套件、放寬隔離、全機政策調整、tinyllama 重構、PR 合併。 |
| ReadOnly | Mac 歷史、tinyllama 原始碼、固定 prompt／模型契約、`sales.xlsx`、`uv.lock`、`oracle.json`、OneDrive 技能源目錄。 |
| Written | Windows 模組、回歸測試、E010、教程和可公開摘要。原始證據存 repo 外。 |
| Modify | `poc.py` 加入 Windows CLI 路由及 Windows endpoint，`ide.py` 接 Windows 收證，既有測試只修跨平台 fixture／UTF-8，README 指向新教程，checkpoint 增加 Windows 狀態。 |
| Deleted | 僅本輪經核對的暫存、程序及其專用資源。 |
| TestCase | 原生工具鏈、檔案／網路隔離、Job／資源、回歸、三案 MVP、正式 15 案、GUI 引用、證據與人工審查。 |

實測結果與待辦見 [E010](../../../experiments/E010/README.md)。
