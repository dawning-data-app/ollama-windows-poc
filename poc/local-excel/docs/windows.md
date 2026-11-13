# 原生 Windows local-excel POC

Windows 增量以 `e41369371053702483b964a6cac575e4f176bd04` 為 Mac 對照。用獨立的 `feat/andrew/local-excel-windows` worktree。以下命令在 `poc/local-excel` 執行。受測 run、工具、模型、控制技能與證據使用不同的 repo 外目錄。

## 2026-11-13 功能驗證結案

**Windows 端到端功能驗證通過，本次結案無需 IT 介入。** AppContainer 診斷依使用者指示停止。受限檔案、Python 與 named pipe 對照已有部分探測通過，完整 AppContainer 官方 TUI 流程、E010 正式隔離與 65,536 context 均未驗收。功能案例不計入正式驗收。

2026-11-13 在原生 Windows 的一般桌面程序中，操作者用 VS Code 1.137.0、官方 `sst-dev.opencode@1.0.0` 的 `Open opencode` 命令開啟 OpenCode 1.19.5 TUI，送出一次合成 Excel 提示。Session 為 `ses_e2d2ea9fdffeIGQmHWRu2fdLGa`。經本機 relay 呼叫 Ollama 0.31.1，三筆請求均回 HTTP 200。`/api/ps` 核對 Qwen 3.5 9B 衍生文字模型 `qwen3.5:9b-q4_k_m-text-smoke` 的實際 context 為 8,192，digest 為 `2c0b40d01b97bad9eb56ff380478a61fbd80ed626229b223cb362b8ecf558e60`。

OpenCode 生成 `analysis-01.py` 並呼叫 `excelpython_execute` 一次。CPython 3.12.12 以 openpyxl 實際開啟合成工作簿，exit 0、stderr 空白。Python stdout 和同一 session 的最終回答均符合獨立 oracle，總額 12,000，1 月 3,300、2 月 8,700，北／中／南分別為 2,800、4,000、5,200，排名南、中、北。

功能證據位於 `D:/codex/official-opencode-tui-1794537994488/`。以 `extension-activation.txt` 核對官方入口，`session-messages.json` 核對提交及回答，`analysis-01.py` 和 `python-attempt-01.json` 核對實際執行，`verified-answer.json` 核對模型、HTTP 狀態與答案。

AppContainer 診斷及原始證據索引見 [E010 結案紀錄](../../../experiments/E010/README.md#2026-11-13-功能驗證結案)。

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

## OpenChamber 側欄三案功能驗證（8192 context）

三案均在原生 Windows 的 VS Code OpenChamber 側欄各送出一次。OpenCode 自行撰寫 `analysis-01.py`，透過 `excelpython_execute` 執行，並依工具結果生成側欄回答。三案不計入正式驗收。E010 的 AppContainer、ACL、WFP、65536 context 與正式案例判準照舊。歷史嘗試及各案紀錄見 [Draft PR #2](https://github.com/dawning-data-app/ollama-windows-poc/pull/2) 與 [E010](../../../experiments/E010/README.md)。

使用原生 Windows PowerShell、既有 POC worktree、CPython 3.12.12／openpyxl 3.1.5、VS Code 1.133.0、OpenChamber 1.24.2、OpenCode 1.19.5 與 Ollama 0.31.1。各 runner 以獨立的 loopback 程序，從已準備的 `qwen3.5:9b-q4_K_M` model store 建立供本輪使用的文字模型。預載及結案均核對實際 8192 context 與 manifest digest `2c0b40d01b97bad9eb56ff380478a61fbd80ed626229b223cb362b8ecf558e60`。runner 設定 `use_mmap=true`、`LLAMA_ARG_REPACK=0` 與 `num_batch=256`。

| 案例 | 實測結果 | 證據 ZIP（執行主機） |
| --- | --- | --- |
| 正常 | 實際讀取合成 `sales.xlsx`，Python stdout 與側欄 JSON 均符合 oracle。 | `D:\codex\openchamber-generated-python-mapped-1794473316987-evidence.zip`<br>SHA-256 `2e92a6424808b5f7b4207dee6b2da14eb27776bf6209cd86a355339e3d0d0e38`<br>Session `ses_e310a636fffes6F06fdBZoDA2v` |
| missing | 對 `銷售 資料` 執行 `os.scandir`，取得 `FileNotFoundError`（WinError 3、errno 2）。側欄以繁中顯示原始路徑及目錄不存在。 | `D:\codex\openchamber-missing-utf8-1794535373743-evidence.zip`<br>SHA-256 `81b4eb5576a6643fde6e0e9e8c0c75f9854ee02e1f42e649c1f3151e5ac0de0c`<br>Session `ses_e2d58ac67ffeSAX09H7Ypwdqn5` |
| corrupt | 對 `銷售 資料\sales.xlsx` 執行 `openpyxl.load_workbook`，取得 `BadZipFile`。側欄以繁中顯示原始路徑及檔案格式錯誤。 | `D:\codex\openchamber-generated-errors-1794477825404-evidence.zip`<br>SHA-256 `13701d2b7bf842f3365f6161fd64cde6522a344bc72f3b885c4cf5e489c08eb6`<br>Session `ses_e30b3deaeffeSH4KT5hBW0oGP1` |

corrupt 的合成 `.xlsx` 刻意使用純文字內容，預期會觸發 `BadZipFile`。missing 與 corrupt 的 ZIP 根目錄都包含修正後的 UTF-8 MCP。corrupt ZIP 同時保留先前 missing 的失敗證據。

1. 每次選一案，將上表的 ZIP 路徑和 SHA-256 填入下列命令。確認 ZIP 後解壓，並建立該次專用的空白證據目錄。

   ```powershell
   $Zip = '<本案的 ZIP 完整路徑>'
   $ExpectedSha256 = '<本案的 SHA-256>'
   if ((Get-FileHash -Algorithm SHA256 -LiteralPath $Zip -ErrorAction Stop).Hash -ne $ExpectedSha256) {
       throw 'Evidence ZIP SHA-256 mismatch'
   }
   $Root = Join-Path 'D:\codex' ('openchamber-recheck-' + [guid]::NewGuid().ToString('N'))
   $Bundle = Join-Path $Root 'bundle'
   $Evidence = Join-Path $Root 'evidence'
   New-Item -ItemType Directory -Path $Root -ErrorAction Stop | Out-Null
   New-Item -ItemType Directory -Path $Evidence -ErrorAction Stop | Out-Null
   Expand-Archive -LiteralPath $Zip -DestinationPath $Bundle -ErrorAction Stop
   $Py = 'D:\code\python\ollama-windows-poc-local\tools\locked-evaluator\Scripts\python.exe'
   ```

2. 使用解壓根目錄的 runner 與同目錄的 `excel_python_mcp.py`。執行本案的一條命令。

   ```powershell
   # 正常
   & $Py -I -B -u (Join-Path $Bundle 'smoke-openchamber-generated.py') $Evidence
   # missing
   & $Py -I -B -u (Join-Path $Bundle 'smoke-openchamber-generated-errors.py') missing $Evidence
   # corrupt
   & $Py -I -B -u (Join-Path $Bundle 'smoke-openchamber-generated-errors.py') corrupt $Evidence
   ```

3. 依新收證目錄 `$Evidence` 下的 `ready.json` 找到 VS Code 視窗、模型和提示。若 VS Code 詢問 Workspace Trust，只信任該次暫存的合成資料工作區。從 OpenChamber 側欄建立新 session，貼上原樣提示並按一次 **Send**。記下畫面中的工具與最終回答。

4. 用 `$Evidence` 下的 `session-messages.json`、`analysis-01.py`、`python-attempt-01.json` 和 `verified-answer.json` 核對單筆送出、生成原始碼、實際執行及側欄回答。正常案比對 oracle，異常案核對原始路徑與實際例外。用 `preload.json` 與 `verified-answer.json` 確認 context，等 runner 收尾後檢查 `stops.jsonl` 再重跑下一案。

## 官方 OpenCode TUI 三案功能驗證（8192 context）

三案均在原生 Windows 以官方 OpenCode VS Code 擴充套件的 `Open opencode` 命令啟動 TUI，各送出一次。OpenCode 自行撰寫 `analysis-01.py` 並透過 `excelpython_execute` 執行，工具輸入與執行檔相符。三案不計入正式驗收。E010 的隔離、65,536 context 與正式案例判準照舊。[Draft PR #2 的驗證紀錄](https://github.com/dawning-data-app/ollama-windows-poc/pull/2#官方-tui-三案功能驗證總表) · [E010](../../../experiments/E010/README.md)

使用同一台原生 Windows 主機與既有 POC worktree。沿用 VS Code 1.137.0、`sst-dev.opencode@1.0.0`、OpenCode 1.19.5、Ollama 0.31.1、Node 24.19.0、CPython 3.12.12／openpyxl 3.1.5、Git for Windows，以及已準備的 `qwen3.5:9b-q4_K_M` model store。runner 使用專用 loopback Ollama，以 CPU 載入衍生文字模型，設定 `use_mmap=true`、`LLAMA_ARG_REPACK=0` 與 `num_batch=256`。預載與驗證答案時均以 `/api/ps` 核對實際 **8192 context** 與 manifest digest `2c0b40d01b97bad9eb56ff380478a61fbd80ed626229b223cb362b8ecf558e60`。

| 案例 | 預期結果 | 本機證據 |
| --- | --- | --- |
| 正常 | 實際讀取合成 `sales.xlsx`，Python exit 0，stdout 與 TUI 最終 JSON 均符合 oracle。 | `D:\codex\official-opencode-tui-1794537994488` 下的 `HANDOFF.md` 和各案收據。Session `ses_e2d2ea9fdffeIGQmHWRu2fdLGa`。 |
| missing | `os.scandir` 對 `銷售 資料` 取得 `FileNotFoundError`（WinError 3、errno 2），TUI 以繁中回報路徑與目錄不存在。 | 共用 ZIP 的 `missing/`。Session `ses_e2d1dff3dffemxzGClDsfBNK4U`。 |
| corrupt | `openpyxl.load_workbook` 嘗試開啟 `銷售 資料\sales.xlsx` 並取得 `BadZipFile`，TUI 以繁中回報路徑與檔案格式錯誤。 | 共用 ZIP 的 `corrupt/`。Session `ses_e2d155464ffe9qMlx3ebgBu2Xj`。 |

missing 與 corrupt 使用修正後的 UTF-8 MCP。共用證據 ZIP 位於 `D:\codex\official-opencode-tui-errors-1794538977939-evidence.zip`，SHA-256 為 `83e1f33d17ec3f6fb3f4aead94f2abeaaabff638bed529fda06c9a4b4d58f7e3`。前次失敗保存在 `D:\codex\official-opencode-tui-1794537290354`。行號引用只記錄 `@context-probe.txt#L2-4` 出現在 TUI 草稿。該引用未送給模型，附件與精確行範圍內容均未驗證。

1. 在原生 PowerShell 選一案並建立空白收證目錄。正常案使用原始證據目錄，異常案可用本機證據目錄或核對 ZIP 的 SHA-256 後解壓。使用 `$Bundle` 根目錄的 runner，並讓 `excel_python_mcp.py`、`observe-tui-session.cjs` 與 runner 留在同一目錄。

   ```powershell
   $Case = 'normal' # normal、missing 或 corrupt
   $Run = Join-Path 'D:\codex' ('official-tui-recheck-' + $Case + '-' + [guid]::NewGuid().ToString('N'))
   New-Item -ItemType Directory -Path $Run -ErrorAction Stop | Out-Null
   $Py = 'D:\code\python\ollama-windows-poc-local\tools\locked-evaluator\Scripts\python.exe'
   if ($Case -eq 'normal') {
       $Bundle = 'D:\codex\official-opencode-tui-1794537994488'
   } elseif ($Case -in 'missing', 'corrupt') {
       $Bundle = 'D:\codex\official-opencode-tui-errors-1794538977939'
   } else {
       throw 'Choose normal, missing, or corrupt'
   }
   ```

2. 執行本案對應的一條命令。每次只開一個測試視窗。

   ```powershell
   # 正常
   & $Py -I -B -u (Join-Path $Bundle 'smoke-official-opencode-tui.py') $Run
   # missing
   & $Py -I -B -u (Join-Path $Bundle 'smoke-official-opencode-tui-errors.py') missing $Run
   # corrupt
   & $Py -I -B -u (Join-Path $Bundle 'smoke-official-opencode-tui-errors.py') corrupt $Run
   ```

3. 依 `$Run` 下的 `ready.json` 找到指定 VS Code 視窗。若詢問 Workspace Trust，只信任當次合成資料工作區。在 Command Palette 執行 `Open opencode`，將該次 `prompt` 原樣貼到官方 TUI，按一次 Enter。

4. 等待正常案的 `answer_verified` 或異常案的 `answer_checked`，再等 runner 收尾。比對 `extension-activation.txt`、`session-messages.json`、`analysis-01.py`、`python-attempt-01.json` 與 `verified-answer.json`，核對單筆提交、原始碼、實際執行和同一 session 的回答。查看 `preload.json` 與 `verified-answer.json` 的 context，並核對 `stops.jsonl`。兩個異常案的 Python 預期 exit 1，runner 與停止收據應為 exit 0。

## 官方 OpenCode TUI 行號附件與快捷鍵（8192 context）

這次使用原生 Windows 上已安裝的 VS Code 1.141.0 和獨立 profile，搭配官方擴充套件 `sst-dev.opencode@1.0.0`、OpenCode 1.19.5、Ollama 0.31.1、Node 24.19.0 與 CPython 3.12.12。專用 loopback Ollama 以 CPU 載入既有的衍生文字模型，設定 `use_mmap=true`、`LLAMA_ARG_REPACK=0`、`num_batch=256`。預載及回答後均核對實際 **8192 context** 和模型 digest `2c0b40d01b97bad9eb56ff380478a61fbd80ed626229b223cb362b8ecf558e60`。本節是功能驗證，不計入正式驗收。E010 依原判準。[Draft PR #2](https://github.com/dawning-data-app/ollama-windows-poc/pull/2) · [E010](../../../experiments/E010/README.md)

| 操作 | 實測結果 |
| --- | --- |
| TUI 自動完成選取 `@context-probe.txt#2-4` | **附件與行範圍已驗證。** 按 Tab 選取候選，再送出一筆訊息。Session `ses_e2ccf98d4ffeg5Y3WOA6iQ8OZi` 有一個 `text/plain` 附件，URL 帶 `?start=2&end=4`，OpenCode 以 `offset=2`、`limit=3` 讀取。兩筆 HTTP 200 的實際 Ollama 請求都只有第 2–4 行標記，第 1、5 行標記均未出現。模型逐行照原文回覆。 |
| `Ctrl+Esc` | Windows 開啟開始功能表。回到 VS Code 後，可用命令面板的官方 `Open opencode` 啟動 TUI。 |
| `Ctrl+Shift+Esc` | Windows 將工作管理員帶到前景。回到 VS Code 後，可用命令面板的官方 `Open opencode in new tab` 另開 TUI。 |
| `Ctrl+Alt+K` | 在編輯器選取第 2–4 行後，TUI 插入 `@context-probe.txt#L2-4`。**本次只記錄草稿**，確認後清除。 |

成功證據 ZIP 為 `D:\codex\official-opencode-tui-autocomplete-1794544258537-evidence.zip`，SHA-256 為 `f8d0c8a1b894a97b8b6711858e13c3cb79fba7997b2af58b5bf4f490c69f99dd`。在 ZIP 的 `evidence/` 查看 `review.json`、`session-messages.json`、兩筆 `ollama-request-*.json`、三組快捷鍵收據及 `teardown-verified.json`。

首輪停在 Workspace Trust，當輪未送出。原始證據 ZIP 為 `D:\codex\official-opencode-tui-autocomplete-1794543511759-evidence.zip`，SHA-256 為 `322a6064176feace57b4b6275961869f161044b5fb93f90d887da8df8fe137e1`。先前直接送出 `#L2-4` 的測試及 HTTP API 對照仍可在 PR 查閱。[Draft PR #2 舊紀錄](https://github.com/dawning-data-app/ollama-windows-poc/pull/2#官方-tui-行號引用送出測試)

### 離線 ripgrep 重跑

離線環境第一次開啟 TUI 時，自動完成顯示 `No matching items`，OpenCode 日誌記錄嘗試下載 ripgrep。實測將既有 POC 的 VS Code 1.137.0 附帶的 ripgrep 15.0.0 放到本輪的 `cache/opencode/bin/rg.exe`，再用 `Open opencode in new tab` 另開 TUI，候選就出現了。下方的離線 runner 已做語法檢查，會在啟動前做同一份複製並核對 SHA-256 `8c121acc4d703ca62d394ab38a03771156370b7edeab0c379044482f07e133cf`。

1. 在同一台原生 Windows 核對成功 ZIP 的 SHA-256。使用原始證據目錄，或將 ZIP 解壓後把 `$Bundle` 指向解壓根目錄。讓 runner、`observe-tui-session.cjs` 和 `verify-tui-autocomplete.ps1` 留在同一目錄。在原生 PowerShell 啟動 runner，記下畫面顯示的收證目錄。

   ```powershell
   $Bundle = 'D:\codex\official-opencode-tui-autocomplete-1794544258537'
   $Run = Join-Path 'D:\codex' ('official-tui-autocomplete-recheck-' + [guid]::NewGuid().ToString('N'))
   New-Item -ItemType Directory -Path $Run -ErrorAction Stop | Out-Null
   $Py = 'D:\code\python\ollama-windows-poc-local\tools\locked-evaluator\Scripts\python.exe'
   $Code = Join-Path $env:LOCALAPPDATA 'Programs\Microsoft VS Code\Code.exe'
   $CodeVersion = (Get-Item -LiteralPath $Code -ErrorAction Stop).VersionInfo.ProductVersion
   Write-Host "收證目錄 $Run"
   & $Py -I -B -u (Join-Path $Bundle 'smoke-official-opencode-tui-autocomplete-offline.py') $Run $Code $CodeVersion
   ```

2. 依 `$Run` 下的 `ready.json` 找到視窗與提示。若詢問 Workspace Trust，只信任本輪的暫存合成工作區。在 VS Code 命令面板執行 `Open opencode`。依表實測快捷鍵。測 `Ctrl+Alt+K` 時，從 `context-probe.txt` 第 2 行開頭選到第 4 行末尾，確認出現 `#L2-4` 草稿，再清除草稿。

3. 在空白 TUI 輸入 `@context-probe.txt#2-4`，等候選出現，按 **Tab** 選取，再接上本輪 `ready.json` 的 `prompt`。確認草稿已有檔案引用後，按 **Enter** 一次。

4. 等 runner 輸出 `reference_measured`。在另一個 PowerShell 將 `$Bundle` 和 `$Run` 設為第一個視窗所用的路徑，執行下方命令。核對 `review.json` 的 `userMessages=1`、`fileParts=1`、`filePartExact=true`、`wireExact=true`、`finalExact=true` 和 `context=8192`，再等 runner 收尾並核對 `stops.jsonl`。

   ```powershell
   & (Join-Path $Bundle 'verify-tui-autocomplete.ps1') -Evidence $Run
   if (-not $?) { throw 'TUI attachment verification failed' }
   New-Item -ItemType File -Path (Join-Path $Run 'finish.request') -ErrorAction Stop | Out-Null
   ```

### 離線 runner 首次開啟實測

2026-11-13 依上方步驟在原生 Windows 實跑離線 runner。VS Code 啟動前已將 ripgrep 15.0.0 放入專用的 `cache/opencode/bin/rg.exe` 並核對 SHA-256。從命令面板執行官方 `Open opencode`，第一次開啟的 TUI 就顯示 `context-probe.txt#2-4` 候選。以 **Tab** 選取 `@context-probe.txt#2-4` 後按 **Enter** 一次送出。OpenCode 日誌記錄一次啟動，沒有 ripgrep 下載記錄。

Session `ses_e2cc11cccffe525k1wZ93IHS0z` 有一筆使用者訊息和一個 `text/plain` 附件，附件 URL 帶 `?start=2&end=4`。兩筆 HTTP 200 的 Ollama 請求都只包含第 2–4 行的標記，第 1、5 行均未出現，最終回答逐行符合原文。預載與回答後均確認 **8192 context**，沿用 `use_mmap=true`、`LLAMA_ARG_REPACK=0` 和 `num_batch=256`。

本機證據 ZIP 為 `D:\codex\official-tui-autocomplete-recheck-1794545220999-evidence.zip`，SHA-256 為 `55112add3eab83b65ff8345de40822e387f48cc3a0e91ca16ac049b94b8e0d4c`。ZIP 內的 `first-open-preflight.json`、`first-open-process.json` 和 `first-open-candidate.json` 記錄預置快取與首次開啟。`review.json`、`session-messages.json` 和兩筆 `ollama-request-*.json` 可核對附件與行範圍。

本次為功能驗證，不計入正式驗收。E010 依原判準。[Draft PR #2 的重跑紀錄](https://github.com/dawning-data-app/ollama-windows-poc/pull/2#離線-runner-首次開啟重跑) · [E010](../../../experiments/E010/README.md)

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
