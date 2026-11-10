# E007：單一測試視窗的環境基線與固定短流程

## 驗證什麼
2026-11-10 設計，E007 未占用。使用者「可以繼續了」授權接續 E006 所提環境基線。主要問題：只保留一個測試 VS Code 視窗、一次一個受限 backend，是否能取得可觀察的 API／GUI 基線，並完成同一 excel-short-v1 的三種 fresh MVP？分開記錄環境可用性與代理正確性，不因環境好轉就宣稱模型修正。

## 為什麼
E006 執行中記憶體 free 約 6%、API GET／GUI timeout，且有多個歷史 POC 視窗；同時有真實 Python 與 missing 擴大搜尋錯誤。ide.py／shortflow.py 及固定版 extension 原始碼只能說明啟動／API 契約，不能判斷目標 Mac 可用性。這個實驗影響是否值得進入後續正式重驗；沒有改模型、提示、context 或 sandbox 的決策。

## 成功與失敗判準
執行前固定：03:31–04:16 UTC 共 45 分鐘，由 agent 依前輪 30 分鐘不足及三例各 600 秒提出，並非使用者指定的新時間。環境階段最多 15 分鐘：已停止舊 POC 視窗關閉，只保留一個本次測試視窗；其他使用者視窗／應用不關閉。新受限 backend 健康、三次 GET health/session 成功且每次 <=2 秒；GUI 能見可輸入側欄並能確認草稿，可用記憶體只觀察不設任意性能合格線。API/GUI 不可得標無法判定，停止依賴推論，不放寬隔離。

環境可用才以相同短提示正常／missing／corrupt 各一個 fresh session，每例 600 秒，總限優先；一次一個 server／測試視窗，不預暖其他案例，不重試或換成功樣本。正常需自主探索型別／欄名、實際 Python 分析、月份／數值／區域／排名／最後繁中回答均正確；負面須指定路徑的真實原始例外，停止且不建 answer.json。完整 GUI 工具與最後回答、hashes／digest／65536／本機主輔路由一致。單一案例失敗仍保留並繼續其餘預定 negative（若環境／時間允許），不能當成正式三輪。越界取得內容、保護改變、權限或相容性重大變更即停止依賴。不得重啟全域 Ollama 或關閉其他使用者程式。

## 環境與前置條件
feature branch/worktree／Draft PR head 3d616b0997341b4ff5c9db0ae11503b8555b873f，clean；dev main 6a78267 不實作。沿用既有固定版本、Qwen digest／65536、opencode.json、uv.lock、Excel／獨立 oracle／E004 隔離。ReadOnly 資產不改。開始觀察 free 26%、swap used 17458.44M；不能只看 free 排除壓力。只用原合成資料、同一短提示，不提供舊 code／oracle／答案。

## 重現步驟
先記舊視窗清單及已停止 server 證據；用原生 GUI 關閉可核對為本 POC 的舊視窗，不刪資料。不關閉其他使用者視窗；如未存檔／未知視窗則保留並記限制。序列 prepare --short-workflow --interface chamber，每次新根 /private/tmp/local-excel-extensions/runs/baseline-20261110；啟動／量 GET 延遲、記 memory/swap，再由真實側欄送 prompt.txt。只用 GET／CLI export 收證，不用 API 送分析需求。候選 prompt 只替換 session 路徑，不變文字。記 raw user context、tool stdout、agent source／最後回答、hash/model/route 與 GUI 觀察。三例後停止本輪 backend，再做文件／commit／push／Draft PR 人審。

## 是否成功
執行日期 2026-11-10。**失敗：環境基線可觀察，但固定短流程未滿足三例契約。** 本輪三個預定 fresh MVP 都真正從側欄送出並收證，有限實驗任務完成；missing 最後沒有回答是已觀察到的失敗，非未送出。原定 Mac 完整驗收仍未完成。沒有用完 45 分鐘才停止：三例皆已結束，不新增樣本或重試。

## 結果與證據
關閉六個已停止／空白 POC 視窗，其他使用者工作視窗保留；一次一個測試 backend／視窗。開始 free 26%、swap used 17458.44M，固定模型載入後 free 約 7–10%、swap 增至約 26185.31M。三例 GUI 均可操作、沒有 cgWindowNotFound／控制端 reset；health/session ready 後 GET 約 0.5–26 ms，沒有 2 秒 timeout。corrupt 第一批 GET 早於 server listen 而 connection refused，保留後再確認就緒，沒有換樣本。不能用低 free 數值單獨判定模型不可用，也不能由 API 快推論模型生成快或沒有資源壓力。

| case | run／session | 實際結果 |
|---|---|---|
| sales | 20261110T033229-c586da57／ses_e3c7a178bffefvy38Of9oky5wc | 367.304 秒、11 assistant steps。探索先失敗後自行修正 exit 0，analysis 路徑先誤寫 /answer.json 被隔離拒絕，再自行修正成功。GUI 工具與最後繁中 JSON 已見，總額 12000、2026-01=3300／02=8700、北2800／中4000／南5200、遞減南中北及額外 rank 數字均正確。排名為物件陣列而非原名稱陣列，stdout 非單一 JSON，仍不通過。 |
| missing | 20261110T034216-b14de70b／ses_e3c71cbe3ffe8Fth6cf3CWc9be | 515.194 秒、20 assistant steps／19 tools。先查缺失子目錄，再改查 workspace／run 父目錄及 /private/tmp，未取得其他資料。兩次 Python print_json NameError，最後 edit 後未再執行；最後 step finish=stop、output token=1、沒有 text。GUI 已確認沒有最後回答，無 answer.json；不追加追問。 |
| corrupt | 20261110T035319-7d1a6d6c／ses_e3c674a24ffeMhlmz9w1PmLTrR | 556.506 秒、14 assistant steps／13 tools。mkdir／file 命令被既有 allowlist 拒絕；先 SyntaxError、自行重寫後實得正確路徑 BadZipFile: File is not a zip file；卻繼續調查並寫／執行 analysis.py 再次失敗。GUI 最後繁中錯誤 JSON 與實際例外一致，沒有 answer.json；未遵守探索失敗停止及最後固定格式。 |

三個 workspace 的 fixture／缺失狀態、lock/config/prompt/context-probe/policy hashes 均相符；三個 server 埠事後確認關閉。兩種主輔 stream、同一 digest／65536／本機路由、session cwd／uv Python 皆核對。三個 user parts 只有本輪文字，去尾空白後與 prompt 相同，沒有附檔／選取內容。原始 export、工具、程式、GUI 觀察、資源／延遲、audit、決策與來源在 /private/tmp/local-excel-baseline-20261110；持久交付 /Users/andrew/.codex/artifacts/local-excel-baseline-20261110，ZIP／SHA-256。不覆蓋 E005／E006 或原始失敗。

作者缺口與模型行為分開：短提示漏列原 region_ranking 名稱陣列型別，不能把本輪物件陣列解讀成 region/product 混淆。short reviewer 要求整段 negative stdout 都可 parse JSON，但原文字只明定 analysis.py 的 stdout-only JSON，check_excel 的進度前綴有歧義；本輪 corrupt 因最後格式先被拒，不能據此稱其例外內容不實。正常的進度 stdout、missing 擴大搜尋／程式錯誤、corrupt 讀取失敗後繼續分析則有明確證據。

原 system agent 指令要求先寫 analysis.py／Do not stop after listing files，與短提示先探索及錯誤停止有語意張力；這是候選原因，尚未因果證明。使用者已同意 [限定指令修訂](instruction-proposal.md)：只改 opt-in agent.excel.prompt 與補回輸出型別／位置，另開最多 40 分鐘、一候選三例 fresh MVP；本 E007 未套用，仍是原 config hash 7dac6527…。

## 結論與限制
本輪支持目標 Mac 在已觀察時段能操作側欄及低延遲 GET，不支持單視窗是唯一原因，也不代表推論性能或完整分析驗收成功。正常實算與 corrupt 錯誤內容有進展，仍有格式、流程與程式錯誤，missing 不可靠。正式兩介面十例、Windows 全未執行；官方本輪未測，不能由側欄推定其結果。原 CLI/TUI、tinyllama／腳本／測試／簡報、poc.py／isolation.py／fixture／oracle／lock 不改。本輪只有文件變更，未重跑回歸；36/36 是 E006 的既有 POC 結果，不冒充本輪新測試。E008 按使用者新決策另行開始，未自動改模型／context／sampler／權限或隔離，不合併。
