# E010 原生 Windows 工具鏈與 OS 隔離 MVP

## 2026-11-13 功能驗證結案

**Windows 端到端功能驗證通過，本次結案無需 IT 介入。** AppContainer 診斷依使用者指示停止。受限檔案、Python 與 named pipe 對照已有部分探測通過，完整 AppContainer 官方 TUI 流程、E010 正式隔離與 65,536 context 均未驗收。功能案例不計入正式驗收。

下方保留 2026-11-12 的前置判準與當時狀態。

| AppContainer 探測 | 實測結果 |
| --- | --- |
| 官方入口 | 官方擴充套件送出裸 `opencode`。修正 launcher 後，無埠入口已驗證能抵達 AppContainer 政策檢查。 |
| 檔案與子程序 | 專用 profile 與 run ACL 已實測。工作區映射到 `Y:\` 後，受限 OpenCode 能讀寫工作區並啟動鎖定 Python。已核對子程序的 SID 與 Job，外部 canary 的直接讀取與 junction 穿越均遭拒絕。 |
| 完整官方 TUI | 明確傳入 `Y:\` 和 `PWD` 後，仍在對 D 槽根目錄做 `lstat` 時回 `EPERM`、exit 1，未建立 Excel session。修正版診斷執行檔在 `CreateProcessW` 回 Win32 4551，Code Integrity 3077 記錄企業政策阻擋。獨立 VHD 掛載回 Win32 1314。 |
| 本機推論對照 | 桌面控制端前後均可連 `127.0.0.1:21434`，AppContainer 直連回 Winsock 10060。受限 Bun 經獨立 named pipe 完成一次 Qwen 推論，收到 HTTP 200 和預期答案 `42`。OpenCode provider 的 named pipe 整合未驗證。WFP 和 loopback 豁免均未修改。 |

完整診斷與原始證據索引位於 `D:/code/python/ollama-windows-poc-local/evidence/windows-opencode-qwen-handoff-20261113.md`。

功能案例及證據檔名見 [Windows 教程的結案紀錄](../../poc/local-excel/docs/windows.md#2026-11-13-功能驗證結案)。

## 驗證什麼

設計日期 2026-11-12（台北）。基準 `e41369371053702483b964a6cac575e4f176bd04`。問題是固定的 Windows OpenCode 能否在同一原生 OS 邊界內讀寫本次 workspace、執行鎖定 Python 並只連到 POC Ollama，同時讓兩個 VS Code 入口保有真實互動。

## 為什麼

`ide.py` 的 E004 launcher、環境與隔離規則由 macOS sandbox-exec 實作。Windows 候選使用 AppContainer 限制檔案與子程序的 token，使用 Windows 網路政策限定 TCP 路由，使用 Job Object 管理本次程序生命週期。原生程序測試只能回答 Job 與引號等局部行為。已安裝的官方 VSIX 以裸 `opencode` 啟動 TUI 的程序內 API。網路測試須查驗實際入口使用的路由，以及 OpenChamber 的外部 API。

## 成功與失敗判準

- 成功須具備原生鎖定 Python、已生效的檔案及網路邊界、真正 backend／子程序探測、三個入口、固定模型身分與停止收據。workspace 讀寫及指定 Ollama 是正對照。其他 run／evaluator／控制 checkout 的讀取、列舉、reparse 路徑與未授權網路目的地須拒絕。
- 對照證實可繞過或程序／身份／設定不符即失敗。缺少權限、固定工具、對照、資料或觀測時依情形標為未執行／無法判定。
- 台北時間 10:39:07 開始，前置截止 11:39:07，總截止 14:39:07。前置最多兩次有證據的修正。資源與每案上限見 Windows 教程。只有前置成立才開三案側欄 MVP。

## 環境與前置條件

Windows 11 Pro x64 build 26200。基準來源與 PR #1 已重查。既有 Ollama 0.40.14 使用 11434。本次使用單獨的 0.31.1、21434 與 model store。Ollama 版本、模型 digests 與 65536 context 必須分別核對。系統網路政策須先有公司授權及可驗證的 provisioning 收據。

## 重現步驟

1. 在獨立 worktree 核對 workbook、lockfile 及 oracle 雜湊。
2. 驗證固定工具與原生鎖定 Python，確認 UTF-8、含空格／中文的 cwd、Job 整棵程序樹清理。
3. 由公司批准的原生政策準備專用 AppContainer、路徑 ACL、網路 allowlist，核對權限及還原範圍。
4. 使用無答案 canaries 與正／負網路對照，從同一 token 與子程序做隔離探測。只對符合條件的候選進行模型載入、工具鏈、GUI 和案例驗證。

## 是否成功

**E010 整體無法判定。** 已完成固定工具、Windows 啟動拒絕、Job 程序樹與資源前置驗證。公司機未提供本次 AppContainer、ACL 與 WFP 政策。真實 OS 邊界、模型載入、GUI 提交、三案側欄 MVP 和 15 個正式案例均未執行。

| TestCase | 狀態 | 實測結果 |
|---|---|---|
| 固定工具與 repo 資產 | 成功 | 核對官方工具檔 SHA-256／簽章與實際版本。兩個固定擴充套件已裝於各自專用的 VS Code user-data 及 extensions 目錄。Workbook、uv.lock、oracle 前後 hashes 相符。 |
| Windows 原生 Python／shell | 成功 | 原生 uv 0.9.2 依鎖檔安裝 CPython 3.12.12、openpyxl 3.1.5。固定版 Git Bash login 參數在 `銷售 資料` 內用離線 uv 執行，cwd、interpreter 和版本均相符。OpenCode 1.19.5 無模型 config 探測確認本機 21434。 |
| 無政策時的三入口 | 成功 | CLI、官方 TUI 和 OpenChamber 分別用獨立的合成準備案，均於程序啟動及推論前拒絕。 |
| Job／watchdog／reparse | 成功 | 原生測試驗證含中文空格路徑、父子程序一併停止、硬截止、GUI finish 停止擁有的 Job、loopback PID 核對與 evaluator junction 拒絕。 |
| 資源門檻 | 成功 | 初測 commit 餘裕 11.05 GiB，低於 12 GiB。主機資源回升後，7 次採樣最低 RAM 15.18 GiB、commit 15.32 GiB，持續 30 秒符合門檻。 |
| 公司檔案／網路邊界 | 未執行 | 目前帳號為一般 Windows token。未找到已核准的 POC AppContainer、ACL 或 WFP 規則，待 IT 提供。 |
| 模型資產 | 成功 | 官方 Q4_K_M manifest 與六個 blobs 的大小及 SHA-256 均相符。首次傳輸逾時後以 HTTP 206 續傳。 |
| Windows 參數化 tag | 成功 | 受控的 21434 上重建 Modelfile，digest 與 Mac 相同。/api/ps 前後皆無載入模型。專用 Job 與 listener 已停止。首輪 listener 在 GPU discovery 時尚未 ready，修正 readiness 後重驗成功。 |
| 模型實際 context／主輔路由 | 未執行 | 須先實測 Windows OS 邊界、當次資源門檻與模型工具鏈。 |
| 真實 VS Code GUI／Excel MVP | 未執行 | 官方快捷鍵／引用與 OpenChamber 真實送出待測，三案均未送出。 |
| Windows 正式案例 | 未執行 | CLI、官方 TUI、側欄各五案，全部未啟動。 |
| 現有程式回歸 | 成功 | local-excel 50 通過、4 跳過（3 個 Mac 邊界測試及 1 個舊 `.venv` 探測）。tinyllama 原有 Python 10 通過、PowerShell 20 通過。 |
| Archify | 成功 | Showcase 9/9，4 個 viewport 無溢出，明暗四張截圖均已目視。 |
| PR Lens／Graphify | 未執行 | 兩個固定版本缺 Windows runtime，repo 無可用 Graphify 圖。 |
| 人工審查 | 未執行 | Windows 增量交獨立 Draft PR。 |

## 結果與證據

- 初次回歸揭露 Windows 預設編碼、POSIX 字串與 junction 呼叫差異。修正以 UTF-8、平台路徑及原生 junction 呼叫重驗。Mac 歷史實驗及固定資產保留。
- Windows launcher 為官方 TUI 設定 `OPENCODE_GIT_BASH_PATH` 與 `SHELL`。OpenCode 1.19.5 的 `Shell.acceptable` 在未另設 shell 時採用 `SHELL`，其 Bash tool 以 login 方式執行。 [固定版原始碼](https://github.com/anomalyco/opencode/blob/v1.19.5/packages/core/src/shell.ts)
- 六套技能及引用檔已同步到 evaluator 專用控制目錄。原始證據位於 repo 外的 `evidence/20261112T023907Z`，包含工具 SHA-256、資源、準備案 IDs、18 個未執行案例、Archify HTML 與 receipt。準備案未產生模型 session。
- 11434 屬既有 Ollama 0.40.14。21434／21435 屬本輪專用候選。Windows GUI、實際推論 backend 與前次關機原因仍無實證。

## 結論與限制

下一步由公司管理方提供僅限 POC 的 AppContainer profile、目錄 ACL、WFP 規則與可用的 TCP 正對照。確認規則存續、重測資源並以無答案 sentinel 實測後，才進 65536 context 與三案側欄 MVP。驗收待結果及人工審查。
