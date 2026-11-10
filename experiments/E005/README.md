# E005：以資料探索與輸出證據約束自主 Excel 分析

## 驗證什麼
- 設計日期：2026-11-10；編號 E005 未占用，E001–E004 歷史保留。
- 問題：不換模型／backend、不提供分析器，只增加 IDE 使用者需求的探索、核對與回答規則，能否修正欄位理解及無依據敘述，達到原定 Mac 完整驗收？
- 假設：代理先自主產生並執行 inspect.py，根據實際欄名／型別／區域與商品集合寫 analysis.py，以實際輸出核對分組、合計，再只引用計算結果回答，可在固定資產下完成驗收。

## 為什麼
- 來源：b121801 的 ide.py／poc.py／驗證紀錄及 review-20261106-gui-followup/review-evidence.zip 的原始 session、腳本、工具與回答。
- 資料理解：官方 sales 2 用 row[2] 當 region；側欄 sales 1 用第 3 欄，均未先檢查欄名。型別探索缺少時，側欄 sales 2 的日期先轉字串再按不相符格式解析，月額為空後才自行診斷。
- 流程：官方 sales 3 已跳表頭，row_count 又減一；missing 改查 workspace 根目錄。僅 exit 0 不保證分組／路徑正確。
- 回答依據：側欄 sales 2 的 answer.json 正確，但最後多加未計算的南區月額；corrupt 工具已回報 ZIP 錯誤，回答另加錯誤根路徑、位元單位與猜測。
- 既有指令及 capture 不強制先探索欄位，最終正常回答只自動檢查總額是否出現；手動核對才發現額外數字。原始證據已能定位上述原因，但能否靠通用流程修正仍必須實測。
- 成立才採用新 IDE 流程並重驗；不成立則停止自動擴展，交證據及下一個決策。原 CLI/TUI 基準不修改。

## 成功與失敗判準
- 事前設定：2026-11-10，執行新代理需求前固定。
- MVP 成功：真實側欄送出；代理自主寫／執行探索與分析 Python，探索欄名／型別／兩種分組集合；正常 JSON 與 oracle 相符；最終繁中回答僅引用實際計算輸出，GUI 工具與回答可見；所有保護／路由不變。
- 最終成功：凍結流程後兩介面各三個 fresh 正常及 missing／corrupt；每例真正 GUI 送出及看工具／最後回答，全部數值／月份鍵／分組／排名／額外敘述／精確錯誤路徑通過，無答案污染、hash 改變或模型／隔離差異。
- 失敗：在有效環境下出現任一數值／分組／敘述／指定路徑錯誤或未完成；不以成功樣本替換。
- 無法判定：GUI／runtime／權限等前置條件不可得，無足夠執行證據。
- 上限：總計 210 分鐘，02:01:50–05:31:50 UTC；最多兩版通用提示，各一個 fresh MVP、最多 600 秒。MVP 皆不成立即不接入正式批次；成立後凍結版本，正式十例各最多 900 秒，批次中不修提示或換案例。總限到即停並逐項標示未完成。
- 越界、protected hash 改變、隔離／模型不符即停止依賴執行；需 backend 升級、模型契約、自製 extension 或重大權限變更則交使用者決策。

## 環境與前置條件
- Mac；VS Code 1.137.0、官方 extension 1.0.0、OpenChamber 1.24.2、OpenCode 1.19.5、uv 0.9.2、Ollama 0.31.1。
- Qwen digest 5eb3a683cbfed5baef1d1f24e2f54afd93e8a9ba344ca71eb8bb37129cf545fe，65536 context、主輔本機；11/10 preflight 已重新 qualified。
- 合成 Excel／uv.lock／oracle／poc.py／isolation.py 不改；保持 E004 Mac 邊界與原 opencode.json／模型參數。
- feature worktree 與 Draft PR 均確認 b121801，乾淨；dev main 6a78267 乾淨，只唯讀。GUI 可見。
- 只測合成資料；不推論其他檔案格式、髒資料或真實客戶環境。

## 重現步驟
- 新增 IDE 專用通用需求流程（沒有 Python 解法或答案），由 ide.prepare 寫入新 workspace 的 prompt.txt；原 config／資產保留。綁定 prompt hash，capture 核對探索工具、實際 stdout 與最後回答。
- workspace 僅放原固定準備資產。不得複製 evaluator、oracle、舊答案／腳本給代理。
- 每個新 run 用新 state；MVP 通過後凍結，正式批次用新的 run，不計入 MVP。
- 原始新證據在 /private/tmp/local-excel-repair-20261110，最終另存持久 artifact。GUI 用原固定兩種介面；CLI／HTTP prompt 不可替代。
- 實際執行位置／指令／結果：待執行後逐項補記。

## 是否成功
- 執行日期：2026-11-10。
- 實驗狀態：失敗。
- 本輪有限假設的驗證任務完成：是；已按事前上限取得實際反例並記錄限制。使用者的 Mac 完整驗收目標未達成，不能把紀錄完成當成目標完成。

## 結果與證據
- 唯讀原因分析及版本核對如上；兩個 MVP 均無完整成功證據，正式十例未執行。
- 新正式批次不得混入 11/05–06 的舊樣本，舊失敗與使用者中止案例保留。

## 結論與限制
- 此長式結構化流程在兩版 MVP 的有限投入內未成立，不能宣稱改善或 Mac 通過。新流程只保留為 `--evidence-workflow` 明確 opt-in，原 IDE 預設與原 CLI/TUI 基準保留，不將未成立候選作為預設採用。
- 後續依事前條件判讀，保留失敗及停止原因；Mac 通過且人審後才 Windows，不合併。

### 第一版 MVP（保留）

run `20261110T020733-33eeb2c8`，session `ses_e3cc63ff1ffeDhX0CwvhOTs0VM`，真實側欄送出。流程作者選用 inspect.py，實際 Python traceback 證明遮蔽 stdlib inspect，openpyxl.compat 的 import inspect 回到本地腳本而循環匯入；代理試圖 rm 被原權限拒絕，未放寬。已由 GUI 停止，無完整分析，不算成功／不算正式正常樣本。這是流程命名缺陷，不能據此判斷 Qwen 資料理解假設。第二版將探索腳本改為 explore_excel.py，其他流程及 config 不變；用最後一個允許的 fresh MVP，不續接舊對話。

### 第二版 MVP（最後一次允許嘗試）

run `20261110T021411-e4d0a53d`，session `ses_e3cc0c108fferWwDK4MQxoVk9J`。02:17:44.451 UTC 從真實側欄送出，同樣只含原文字需求，前端刪除一個尾端換行，無額外選取／檔案 context。v2 唯一提示變更是探索腳本改名，模型/config/資料/隔離不變。

實際自主過程：SyntaxError → 猜成「銷售 資料.xlsx」的錯路徑 → 自行 ls 找到正確 sales.xlsx → tuple.values AttributeError 被 catch 且 exit 0 → 錯誤探索只得 headers=[date]、錯誤型別與空 region/product 集合 → 後續 Python -c 仍錯用 Cell API／有語法錯誤。從 GUI 展開工具看到了真實失敗輸出。

按 600 秒門檻停止；GUI cancel 實際於 02:28:02.105 生效，MessageAborted completed 為 617.802 秒，晚約 18 秒的操作／UI 延遲如實保留，不算門檻內完成。未產生 inspection.json、analysis.py、answer.json，無最終完整繁中分析回答。事前最多兩版的嘗試上限已用完，並非 210 分鐘總時間耗盡；不另開隱藏重試。

### 已排除的原因與不能排除的限制

- 兩次 capture 均確認 protected hashes、原 config hash、主輔本機 stream、固定 digest 與恰好 65536 context；沒有資料被改寫或 oracle／跨 session 讀取成功的證據。
- 停止代理後，evaluator 用相同 sandbox／uv 做唯讀欄位探測：正常讀出五欄及 datetime/str/str/int/int，exit 0。此 probe 僅排除該 fixture 缺套件／讀權限問題，不是代理自主成功，未提供給模型。
- 第一版命名衝突是流程作者錯誤，不能歸責為模型資料理解失敗。第二版真實生成程式錯用 openpyxl API，且此長式、多欄位流程在時間內不能完成；不能外推為所有提示或 Qwen 一律不可行。
- 31 項 POC unittest 通過，包含錯分組、額外數字、錯誤路徑、未知型別與執行順序的拒絕檢查。這只支持 evaluator 防誤判，不支持 GUI E2E 成功。
- 新正式批次：官方三正常＋missing/corrupt、側欄三正常＋missing/corrupt，全部**未執行**，因 MVP 接入前提未成立。原 11/05–06 的結果保持原樣，不拿舊樣本補齊。

### 下一個待決策事項

建議若要繼續，另授權一個更短的單訊息流程候選：只要求先實際列舉指定目錄、以自主 Python 印欄名／型別，再按欄名分析；不要求七欄位 inspection.json。以正常／missing／corrupt 各一個 fresh MVP、每例 600 秒、總計 30 分鐘區分「提示複雜度」是否主因；三例成立後才再凍結並重跑正式十例。仍不得提供預寫分析器或答案，不換模型／隔離。這是待決策建議，未授權執行，也不保證成功。若要改推理模式／模型契約，需另提出具體影響取得決策，沒有自動升級 fallback。
