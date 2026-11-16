# E003：Mac 工具執行的檔案隔離

## 驗證什麼
- 設計日期：2026-11-05；使用者已明確授權隔離 MVP，成立後接入並重測兩種介面。
- 主要問題：能否在不改模型／資料／uv 契約的情況下，對 OpenCode 及子程序施加有效的檔案執行邊界？
- 假設：macOS sandbox-exec 可阻止跨 session／oracle 的讀取，同時讓本次 workspace、鎖定 Python 與本機推論正常運作。

## 為什麼
- 官方 missing session 已完成 `find /private/tmp` 並列出其他 session，還對另一個 case 的 Excel 目錄執行 ls，故原先分離資料夾與 OpenCode permission 不足以防止污染。
- 已停止該測試子程序，保留 raw export；停止前沒有看到讀取舊答案檔，不把「發現路徑」說成「已讀答案」。
- 文件依據：本機 Apple `man sandbox-exec` 明示可用 profile 限制程序，且已標示 DEPRECATED；可執行檔確實存在。文件不證明本次 backend／Python 相容，必須實驗。
- 成立則接入既有 extension launcher 與本機 server；不成立則停止依賴 E2E，回交決策，不換模型或默默退回無隔離。

## 成功與失敗判準
- 執行前固定：同一受限 Python 能讀合成輸入、在 workspace 寫入無答案 canary；直接與透過 workspace symlink 讀其他 session canary／真正 oracle 路徑均遭拒，ls/find 不得列出其他 session；本機 Ollama 可回應，實際 digest／65536 context 不變；同一 profile 下的 OpenCode 能完成真實 Python 工具環境探測並回覆。
- 失敗：任何禁止路徑讀取成功，或受限 backend 無法完成所需操作，且有限修正無法恢復。
- 無法判定：OS 權限／工具／時間限制導致缺少必要執行證據。
- 上限：20 分鐘、最多兩次針對 policy/runtime 的修正。不得改判準來配合結果；不宣稱全面對抗惡意程序的安全證明。

## 環境與前置條件
- Mac M3 Pro 18 GB／macOS 26.5.2；Apple sandbox-exec；既有 OpenCode 1.19.5、uv Python 3.12.12、Qwen 9b 固定 digest／65536 context。
- 真實 OS 限制與本機服務；資料為合成 fixture，其他 session canary 不含舊答案。
- oracle 路徑僅由 evaluator 的獨立 harness 測試，不交給 LLM，也不將 oracle 內容放進 agent workspace。

## 重現步驟
- fresh run 以既有 ide.py prepare --probe 建立；profile 與 evaluator harness／證據在 repo 外，不交給受測代理。
- 先測 OS 層內外讀寫與 symlink，再測 loopback 推論與受限 OpenCode 的非分析型環境工具呼叫。
- 具體 policy、命令、版本、退出碼與證據位置於實際執行後記錄。

## 是否成功
- 執行日期：2026-11-05，約 09:14–09:23 UTC；在 20 分鐘內已達兩次修正上限。
- 實驗狀態：無法判定。
- 本輪驗證任務完成：是（有限實驗的紀錄與停點）；必要 runtime／推論／真實代理工具證據不足，隔離假設尚未成立，不能推進依賴 E2E。這不表示 macOS 隔離不可行。

## 結果與證據
- 原因證據：official missing run `20261105T085950-276bdd12`／session `ses_e550e141bffeu6FFMZBKixnn0L`，停止標記與原始 export 留本機。
- 隔離 run `20261105T091434-ecdfbe5e`，在 `runs/isolated` 下；完整工作路徑與實際 evaluator-only 命令保留於 [evidence](evidence/README.md)，不交給 LLM。
- 初始 profile：uv 在 SystemConfiguration NULL store 處中止。修正 1 僅加入 configd mach lookup；之後 uv／Python stdlib 與 OpenCode `debug config` 可執行，但 openpyxl import 因系統 `/etc/apache2/mime.types` 讀取遭拒而中止。
- 修正 1 下：直接 canary、真正 oracle、workspace symlink 均 PermissionError；列舉 session 父層亦遭拒；workspace canary 可讀寫。這是受限路徑的部分證據，不是完整執行邊界驗收。
- 受限 Python HTTP 請求 localhost:11434 回報 connection refused。獨立 host 檢查確認 localhost／127.0.0.1 的 Ollama 0.31.1 可回應，::1 拒絕，服務僅監聽 IPv4；不能把 host 成功當成受限程序成功。
- 修正 2 加入精確系統 MIME 檔與 IPv4 remote rule；Apple parser 拒絕數字 host，exit 65：`host must be * or localhost in network address`。這次 profile 尚未載入，沒有在其下完成 Python 或推論。
- 已用完兩次 policy/runtime 修正，未再修 profile、未送受限 LLM 探測。合成 XLSX 讀取、實際本機推論、受限 OpenCode 自主 Python 工具與完整回覆仍缺證據。

## 結論與限制
- 決策：不接入此未成立 profile，不退回無隔離 E2E。`ide.py launch/server` 與新生成 launcher 明確拒絕啟動；prepare／唯讀 capture 保留以供檢視，舊 CLI/TUI 基準不改。
- 如要繼續，需另行決定有限投入或隔離技術；下一輪必須重新事前登錄並保留本輪結果。既有暫存 launcher 為歷史資產，勿手動重用。
- 未改模型 digest、65536 context、資料、uv.lock 或 oracle；因沒有受限推論，本輪不宣稱實際 loaded identity/context 已在隔離內證實。
- 不能沿用「非 OS sandbox」的成功標記來宣稱新隔離成立。
- 此為 Mac 範圍；Windows 的工具執行邊界尚未驗證。已棄用的 OS API 不提供長期可用保證。
