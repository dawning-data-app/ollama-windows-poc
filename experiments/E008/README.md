# E008：已授權的條件式探索／錯誤停止指令

## 驗證什麼
2026-11-10 設計，E008 未占用。主要問題：在同一 Qwen／65536／參數／權限／隔離下，僅對齊 agent system 指令與短需求的探索順序／錯誤停止，並補回既有排名型別與輸出位置，能否完成正常／missing／corrupt 各一個 fresh 側欄 MVP？一個候選 excel-aligned-v1，不重試。

## 為什麼
E007 的正常實算數字與區域順序正確，但短提示漏列排名名稱陣列；missing 擴大搜尋／Python 錯誤／第20步無最後文字，corrupt 探索失敗後仍寫分析。原 system 指令直接要求 analysis.py 與 Do not stop after listing files，和 user 先探索／失敗停止存在語意張力，尚未證明因果。來源為固定 poc.py:config/prompt、ide.py、shortflow.py 及 E007 原始 session。只能透過執行判斷行為，不由文件／單元測試推定成功。

## 成功與失敗判準
使用者明確選擇採用限定修訂、另測三例，最多40分鐘含setup：04:09:15–04:49:15 UTC。一個候選，每例600秒且總限優先；每種一個 fresh session，不以重試替換。只改 opt-in config 的 agent.excel.prompt，JSON語義差異必須只這一欄；其餘固定模型／參數／provider／權限、E004邊界與基準完全保持。新 config hash 另記，不能冒稱原 hash。

三例真正側欄送出，見工具與最後繁中回答；正常自主寫／執行探索與分析，原 schema、月份鍵、數值、region 分組、排名與所有額外敘述正確，stdout／answer／final一致。負面為精確指定路徑之真實原始例外，停止、不建立 answer.json，不改查其他目錄或 substitute inputs。hashes/model/context/route/user額外上下文核對。可觀察違規為失敗；環境／限時造成不足為無法判定，未送出為未執行。三例成立才交正式十例決策，MVP 不計入正式三輪。越界取得內容、保護漂移或需要額外權限立即停止依賴，不放寬或換模型。

## 環境與前置條件
feature branch/worktree clean、head 10a9743961e630a4b8667f58b2f1142d801b9438，Draft open/unmerged；E007 backend 全停止／關閉測試視窗。沿用已驗版本、Qwen digest 5eb3a683…、65536、Excel／uv.lock／獨立 oracle／E004 隔離，ReadOnly 基準不改。使用者決策已另存 E007 instruction-decision.json／提案。新模組只是通用指令與 evaluator，沒有分析器／答案，不放入 agent workspace。

## 重現步驟
新增互斥 --aligned-workflow opt-in；prepare 後對本次 config 僅改 agent.excel.prompt，重記 hash；其餘差異拒絕。原預設／CLI／長短流程保留。新根 /private/tmp/local-excel-extensions/runs/aligned-20261110，依序 sales/missing/corrupt，先前例收證／停止／關窗才啟動下一個，不預暖。ready API及可見草稿後從側欄送 prompt.txt，唯讀GET/CLI export收證，不用API送需求。模型自行寫程式；不交 oracle／舊答案／預寫分析器。

## 是否成功
執行日期 2026-11-10。**無法判定完整三例假設／INCOMPLETE；已觀察正常完整性失敗。** 三例任務未完成，Mac 原定驗收未達成。不是40分鐘耗盡：04:25:37 UTC 因 GUI 前置不可得而停止依賴測試並清理未送出 backend；原截止 04:49:15 UTC 保留，不自動重置。一般文件／程式／證據交付可繼續，不能把未執行負面案例記為模型失敗。

## 結果與證據
實際 JSON 語義差異只有 /agent/excel/prompt；原 config hash 7dac6527308a16d50dc84c9c1edcbc10025aa0e0d35a29cf14036e5981abc688，新 hash 34b0dce93dbcb02a78caa4007d71f21413ba3362419052981111c763bd732789。新 effective agent 指令已核對；主輔模型、digest／65536／sampler／provider／permissions 與 E004 隔離不變。來源 commit d01d474，40/40 POC 回歸通過；這只驗 helper／契約，不代替 E2E。

| case | run／session | 實際結果 |
|---|---|---|
| 正常 | 20261110T041101-bef38e77／ses_e3c5681e0ffePEieLmXD33V8lz | 真正從側欄送出，先自主寫 check_excel.py、uv 執行 exit 0，實讀五欄與首筆型別；GUI 工具／最後繁中訊息已見。91.871 秒、3 assistant steps／2 tools 後 finish=stop，最後只給「現在寫 analysis.py，需要」的後續計畫，沒有 analysis.py／answer.json／分析執行或數值答案。不是600秒／20step門檻造成，**完整性失敗**；不追加「請繼續」。 |
| missing | 20261110T041725-da79679a／無 session | config／Python／隔離與 server ready 均已準備；GUI 先 control ID 失效，繼而多次 cgWindowNotFound，重新綁定仍失敗，原生 launch_app 亦不可用。未貼需求／送出，SQLite與GET session count=0，**未執行**。已請使用者解鎖並顯示確切視窗，等待環境回覆；04:25:37 核對本次 PID／port／cwd 後停止 backend 及其 guard。 |
| corrupt | 未準備／無 session | 為保持一次一個案例而未預暖，GUI 尚不可得，**未執行**，不沿用 E007 或舊 corrupt 結果。 |

正常 raw user part 只有本輪文字，去尾空白後與 prepared prompt 相同，無額外附檔／選取；主輔本機 streams、digest／65536、cwd／uv、protected hashes 核對。兩個 prepared workspace 的 fixture／缺失狀態、lock/config/prompt/context-probe/policy hashes 與僅指令差異均相符。missing 的 setup qualification 不能冒充受測主輔 stream／工具／回答，因沒有 session。兩個本輪 backend 均已停止，全域 Ollama 未停止。

ready 後正常／missing API GET 均可回應，推論中 free 約7–8%、swap逾22GB；不能排除資源干擾，但正常是模型自己結束回合，不是計時器中止。GUI normal setup 曾回報 user-changed app，重新讀取後核對正確視窗／草稿才送；後續 missing 是獨立的 GUI 不可得。完整 raw export／agent source／工具、GUI 觀察／中斷、config差異、tests／hash／控制與停止 receipt 在 /private/tmp/local-excel-aligned-20261110；持久交付 /Users/andrew/.codex/artifacts/local-excel-aligned-20261110，不覆蓋 E007／E006／E005。

## 結論與限制
本候選沒有成立為可採用修正，仍保留為 opt-in，原 IDE預設／CLI/TUI／長短流程不變。正常欄名／型別成功不等於完成自主分析；月份／總額／分組／排名／最終額外數字沒有可核對的分析結果。不能推論對齊指令必然改善或惡化模型，也不能由單次失敗宣稱所有 Qwen 不可行。

下一步先恢復 Mac 可見視窗；若仍在原截止內，可為尚未送出的 missing 重新準備新 workspace（保留這次零 session 的 setup／GUI 失敗證據），再首次送出 missing／corrupt，不重跑已失敗正常或補追問。若超出原40分鐘，新的投入需另決策，不自行追加。即使剩餘負面成功也不能把本輪正常改為通過。正式兩介面十例／Windows 全未開始；不改模型／推理模式／backend或權限，不自製 extension，不合併，Draft／needs-rework／human review。
