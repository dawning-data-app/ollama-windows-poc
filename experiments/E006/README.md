# E006：一版短式流程，三個 fresh MVP

## 驗證什麼
2026-11-10 設計，E006 原未占用。減少 E005 指令長度與探索 metadata 格式負擔，保留先探索欄名／型別、按欄名分析、實際輸出回答，能否在同一模型契約下完成正常／missing／corrupt 三例？單一候選，不重試，不替換舊失敗。

## 為什麼
E005 長流程出現語法、猜錯路徑、tuple/Cell API 混用，尚未成立。本輪只縮短文字、提示通用 iter_rows(values_only=True) API，不提供迴圈／計算程式或答案。文件／原始碼只能說明 API，不能判定這個代理行為；需真實 GUI MVP。結果影響是否進入正式十例，未改已鎖定的模型／路由／隔離。

## 成功與失敗判準
使用者明確追加 30 分鐘：02:45:12–03:15:12 UTC。一版 excel-short-v1，正常／missing／corrupt 各一個 fresh 側欄 MVP，每例最多 600 秒且總限優先。全部真實 GUI 送出與看到工具／最後繁中回答；正常 Python 實讀欄名／型別並自主分析，JSON／月份／數值／分組／排名及敘述正確；負面對精確路徑回報實際例外，不建 answer.json。固定 hashes、模型/context/本機路由／隔離一致。可觀察行為違反契約為失敗；環境或時間造成證據不足為無法判定；尚未送出為未執行。三例成立才交回決策，MVP 不冒充正式樣本。越界或保護改變即停止依賴執行。

## 環境與前置條件
開始前 feature／branch／Draft PR head 確認 e93deecb112304381d715e70a913f2ad18833ac1，dev main clean，未在 dev 實作。沿用 VS Code 1.137.0、OpenChamber 1.24.2、官方 1.0.0、OpenCode 1.19.5、Ollama 0.31.1、uv 0.9.2、Python 3.12.12、openpyxl 3.1.5。Qwen3.5:9b digest／65536、config／參數、Excel／uv.lock／獨立 oracle／E004 隔離不變；只用合成資料。新增 shortflow.py 通用文字及 evaluator，不放入代理 workspace，沒有供應分析器。三個 workspace 均事前準備，只有兩個實際送出；沒有重用既有對話。

## 重現步驟
在 feature 的 poc/local-excel 用 ide.py prepare --short-workflow --interface chamber，分別 --case sales/missing/corrupt，根目錄 /private/tmp/local-excel-extensions/runs/short-20261110。啟動受限 server／專用 profile，從真正側欄 textarea 送完整 prompt.txt；只用唯讀 API/CLI 收證，不由 API 送需求。短流程要求自主寫 check_excel.py 實讀表頭／型別，成功後才寫 analysis.py，最後繁中句＋實際 JSON，不要求 inspection.json。固定提示 hash；本輪沒有第二版。evaluator 的 guard.py 只 GET 狀態並在期限核對本次 server PID／命令／cwd 後停止，不發提示、不動全域 Ollama，不是產品 runtime orchestration。

## 是否成功
**無法判定／INCOMPLETE，不成立為可採用修正。** 正常在期限內未完成，missing 有已觀察到的錯誤型別／路徑契約失敗，corrupt 未執行；資源與 GUI 不可得使完整三例假設無法驗完。證據紀錄與停點已完成，使用者要求的三例完整驗證任務未完成；原定 Mac 完整驗收目標未達成，不進正式十例或 Windows。

## 結果與證據
| case | run／session | 事實與分類 |
|---|---|---|
| sales | 20261110T024709-2cff1b79／ses_e3ca28b31ffe5YW4liEu17sQ9J | 真實側欄送出，看到寫程式及展開首個 uv Python 錯誤；四次 Python exit 1：generator 索引、漏 import json、datetime 序列化、把 datetime 模組當 isinstance 型別。沒有成功探索、analysis.py、answer.json 或完整最後回答。600 秒 guard receipt 600.219 秒；用 session.created 到停止 UTC 計算為 600.572 秒，原 receipt 不改。期限內未完成，不能推論無限時間也不可能。 |
| missing | 20261110T024721-24c8d316／ses_e3c946a5bffeQAPf1L3PY1RpVn | 真實側欄送出並看到寫 check_excel.py。raw Python exit 1 印 directory_not_found／<class 'OSError'>，不是實際 FileNotFoundError；之後查 workspace 根目錄及 /private/tmp 的 find，沒有按指定路徑停止。跨工作區搜尋輸出為空，未見其他資料或 oracle 內容。沒有 answer.json／完整最後回答。為保留 corrupt 時間提早中止，03:11:02.752 UTC（session 建立後約 292.538 秒）；該次 generic stop receipt 的 reason 是固定字串，不代表 case complete。這些已觀察違規為失敗，最後回答仍未驗證。 |
| corrupt | 20261110T024726-36217ee0／無 session | 受限 server 與 VS Code 視窗已啟動；native GUI 逾時／reset，截止前 OpenChamber 仍無可操作輸入。沒有送出需求，SQLite 唯讀核對 session count=0，**未執行**；不把安裝／啟動當成功。 |

總限 03:15:12 UTC 到點不再送需求。corrupt guard 停止 receipt 為 03:15:12.641 UTC（輪詢延遲約 0.641 秒）；missing 已提前停止，03:15 的 guard identity-check-failed 是 PID 已不存在，不是 sandbox 失效。三個 server 埠事後均確認關閉。未停止全域 Ollama，沒有下一個候選／重試。

資源觀察：執行中 memory_pressure -Q 的 system-wide memory free 約 6%，session API GET 多次 10 秒 timeout、native GUI 逾時／reset；停止後再量為 25%。missing UI/server 在正常案例進行中預暖但沒有同時送第二個模型需求；多個 VS Code 視窗亦為環境干擾。這些證據支持延遲／GUI 可用性受干擾，不能單獨斷言程式錯誤由記憶體造成。中途 /api/ps 仍為同一 digest／65536／size_vram 7674223656。

兩個已送出 session 的主／輔 stream 均為本機 Qwen，text user part 與 prepared prompt 去尾空白後相同，沒有附檔／選取內容。三個 workspace 的資料、lock/config/prompt/context-probe/policy hashes 均相符，missing 指定資料夾仍不存在。沒有成功分析，故月份／數值／分組／排名／最終額外敘述均無可驗結果；不能填 pass。36/36 POC 單元／OS 回歸只驗 helper，舊 CLI 測試未改未重跑。

完整 run、control／guard／audit／raw export／程式／輸出在 /private/tmp/local-excel-short-20261110；持久交付 /Users/andrew/.codex/artifacts/local-excel-short-20261110，ZIP＋SHA-256。gui-observations.json 明確區分 GUI 目見與只由 export 核對。歷史 E005 與 11/05–06 artifacts 不覆蓋，不提供受測代理。

## 結論與限制
不進正式兩介面十例；官方本輪未送出，不能由側欄推定 TUI 結果。本輪不足以分離短提示效果與資源／GUI 干擾，也不能否定所有 Qwen 或提示；已排除模型/config/hash 漂移、額外附檔及 sandbox 放寬作為本輪差異，未排除資源壓力與工具延遲。Python 錯誤和 missing 擴大搜尋是獨立、具體的失敗證據。

下一個待決策：是否先投入受控的環境基線實驗（只保留一個測試視窗、事前記錄記憶體／API 延遲與 GUI 可用性，再固定候選測 fresh MVP），或維持 needs-rework。不能保證此舉改善模型正確性；未經決策不追加時間、不改 context／模型／backend／隔離。維持 Draft PR／human review，不合併、不進 Windows。既有 Archify 圖無拓樸變更而沿用，Graphify 無可用既有圖且未建圖，PR Lens 針對 E006 真實 bounded diff 本機交付。
