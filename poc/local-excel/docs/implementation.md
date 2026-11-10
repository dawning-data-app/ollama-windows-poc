# python-implementation 工作契約

| 欄位 | 本 topic 邊界 |
|---|---|
| Goal | 透過官方 VS Code extension 的終端 TUI，以及現成 extension 的側邊欄聊天，給資料夾路徑，由本機 Qwen 自主寫／執行 Python 分析 Excel；保留 CLI/TUI 基準，Mac 完成才 Windows。 |
| Non-Goal | 不做報表產品、網站、MCP、雲端推論或模型評比；不自動升級 OpenCode、不更換模型契約、不自製 extension。 |
| In-Scope | 沿用 uv/openpyxl／資料／oracle；增加固定版官方 extension 與 OpenChamber 的最小可行性及各三輪正常、missing/corrupt；受控 launcher、專用 VS Code profile、使用者授權的 Mac 隔離 MVP、上下文／路由證據、教程與本機圖件。 |
| Out-Of-Scope | tinyllama 重構、公開 API 變更、Graphify 建圖、工具全域整合、發布與合併。Draft PR 由使用者另行明確授權。 |
| ReadOnly | 舊 CLI／Windows 腳本／測試／簡報、AGENTS、hooks、runtime、skills、GitHub 設定與 .gitignore。 |
| Written | 本目錄新資產、experiments/E001、E002、E003、E004、E005 與 E006；run/evidence 在 repo 外系統暫存目錄及本次持久 artifact；PR Lens 在 repo 外。oracle 不複製至 agent workspace。 |
| Modify | 本輪可修改此 POC 的 helper／測試／教程／實作與驗證紀錄／圖件；原 baseline poc.py、資料、oracle、uv.lock 保留；根 README 僅入口。 |
| Deleted | 無既有 tracked 刪除；只清理本次生成的程式或輸出，不刪資料、oracle 或歷史證據。 |
| TestCase | TC-01 固定 digest／65536／主輔本機路由；TC-02 官方快捷啟動／檔案引用／cwd／config／uv；TC-03 側邊欄最小可行性後真實送出與顯示工具／回答；TC-04 每介面三次 fresh sales、missing、corrupt 與 protected hashes；TC-05 額外上下文／回歸／圖件；TC-06 Mac 人審後 Windows；TC-07 隔離內讀寫／跨 session／oracle／symlink 拒絕與真實工具鏈；未成立須停止執行。 |

分支：`feat/andrew/local-excel-poc`。基點：`7dc9902a9a6b47fa0a1f1d9a79e1ce21fce2e561`。只在獨立 feature worktree 實作；dev worktree 不改動。

## 技能邊界

- Graphify：沒有既有 graph，採定點讀碼；不 extract。未來若有圖，固定 graphifyy 0.9.73，所有命令設 `GRAPHIFY_NO_AUTO_REFRESH=1`，重要關係回讀 source。
- Archify：`diagrams` 的 workflow 是理解工具，不是 E2E 成功證據；需 showcase 九項檢查、deliver 與四種 viewport visual-check，實際看截圖後才寫視覺判定。繁中內容的固定 Viewer UI／HTML lang 回退英文。
- PR Lens：固定 CLI 0.11.0，只針對真實 base/head diff 作本機 validate/render；規格與結果在 repo 外。不跑 canvas、upload、server 或工具內 PR 發布。缺可用 head 時 deferred；本次 commit／push／Draft PR 使用 Git／GitHub 能力，為使用者另外明確授權。

## 人工審查完成條件

測試者確認每次生成程式有實際讀取銷售 XLSX、計算與本機工具紀錄；核對數字、排名、protected-input hashes、模型身份／context／路由、答案污染限制。三次 CLI 之外要有 VS Code TUI 操作證據；負面案例須明確說明讀取失敗。記錄各項 pass/fail/unverified，不以程式 exit 0 或圖件通過替代。

## 本輪 extension 增量

來源與版本先查證，必要 runtime 問題先登錄 experiments 的事前判準再試。官方 sst-dev.opencode 固定 1.0.0，聊天仍是終端 TUI；OpenChamber 2.6.1 要求 backend 2.x，改評估現成 1.24.2，保留 OpenCode 1.19.5 與既有模型契約。若此版無法相容，停止依賴 E2E，提出證據與影響交使用者決策。使用者另行授權信任本次暫存 runs 根目錄；不關閉 workspace trust。

## 隔離增量決策

使用者已授權最小隔離實驗，成立後接入並重測。E003 在兩次修正上限內無法判定；只證實部分拒絕，未完成完整 Python／推論／工具鏈，故沒有取得接入前提。官方 missing 越界、正常第三輪鍵名失敗與全部舊證據保留。launch/server 與新生成 launcher 拒絕啟動；無 bypass 參數。既有 CLI/TUI、模型／資料／鎖檔與 oracle 仍為 ReadOnly，Windows、backend 升級、自製 extension、其他隔離技術另待決策。

E004 後續：使用者另行授權 15 分鐘／兩次修正，MVP 已成功，依原條件接入 Mac 隔離與重測。ReadOnly 契約不變。`isolation.py` 與其 OS 回歸屬 Written；新 run 必須具備匹配的 policy／manifest／receipt，舊無隔離 run 仍拒絕。E003 的暫停狀態為歷史，不覆寫實驗結論。兩種介面依原判準執行三輪正常與 missing/corrupt，實際結果及未驗證項見下表，Mac 尚未驗收。

## 2026-11-06 契約執行對照

九欄位範圍維持不變；本日只在 feature 更新教程／契約／驗證紀錄，未改 runtime、模型、資料或 oracle。驗證執行結束不表示採用條件成立。

| TestCase | 證據／狀態 |
|---|---|
| TC-01 | 最終 runtime 各案例的主／輔本機 streams、固定 digest／恰好 65536、config／uv／protected hashes 均相符。 |
| TC-02 | 官方快捷入口與 TUI／cwd／config／uv 已實測；引用實際附加全文，但選取行數未保留，屬已知限制。 |
| TC-03 | 側欄 MVP 成立；三個正常及 missing 的 GUI 工具／最後繁中回答已見。corrupt 曾遇 cgWindowNotFound，解鎖後已在同一側欄補看最後繁中錯誤報告及最後 Python 工具，沒有重送需求或重啟 backend；歷史缺口保留。 |
| TC-04 | 各三輪正常、missing、corrupt 已執行並保留，兩介面正常 JSON 都是 2/3 符合；分組／額外數字／敘述仍有錯誤，完整 E2E 未通過。負面案例無銷售答案，但保留路徑／敘述限制；GUI 補驗已完成。 |
| TC-05 | 原始 user context／模型／hashes／生成程式留證；11/06 POC 20/20；舊 CLI 10/10 為 11/05 結果。Archify 凍結圖再驗 9/9、保留原視覺檢視；Graphify 無既有可用圖、不建圖。PR Lens 按本輪真實 increment base/head 在 repo 外交付，見 render manifest。 |
| TC-06 | Mac 交 human review／needs-rework，Windows 未執行；不合併。 |
| TC-07 | E004 最小驗證及真實 OS 回歸成立；新 run 套同一 policy，無 unsandboxed fallback。不外推成通用惡意程式防禦。 |

本輪人審需要處理分析不穩定與路徑／敘述限制；corrupt 最後 GUI 證據已補齊。不得以 errors=[]／exit 0／圖件通過取代驗收；不得為追求成功率刪除失敗、換成功樣本，或直接重用本輪生成程式。若決策需要升級 backend、改模型契約或自製 extension，須先取得使用者決策。

## 2026-11-10 修正候選契約

九欄位範圍不變；Written 增加 workflow.py、tests/test_workflow.py、E005 與本輪驗證紀錄。新提示／嚴格 evaluator 僅以 `--evidence-workflow` opt-in；MVP 未成立，不取代原 IDE 預設或原 CLI/TUI。

ReadOnly 保留 poc.py、sales.xlsx、oracle.json、uv.lock、isolation.py、固定外部 runtime、舊 tinyllama CLI／腳本／測試／簡報。Modify 僅 IDE opt-in／capture 及新模組、測試、教程／紀錄；Deleted 無既有 tracked 刪除。

TC-01／TC-07：兩 MVP 的本機模型、context、原 config、hashes 與 E004 邊界一致。TC-03：兩個 MVP 的真實側欄工具／中止已核對，但沒有完整分析回答。TC-04：正式兩介面三正常＋missing/corrupt 全未執行，前提未成立。TC-05：31/31 POC 回歸，保留舊失敗、凍結 Archify 與本機 PR Lens。TC-06：Mac 未通過、Windows 未開始，Draft／人審。詳細證據及下個待決策見 [修正候選驗證](repair-verification.md)。

## 2026-11-10 E006 追加契約

Goal／Non-Goal／In-Scope／Out-Of-Scope／ReadOnly／Written／Modify／Deleted／TestCase 九欄位保留。Written 增加 shortflow.py、tests/test_shortflow.py、E006／短式批次紀錄；Modify 僅 ide.py 的互斥 opt-in 與 capture dispatch、教程／紀錄。ReadOnly 基準及固定模型／隔離不變；Deleted 無 tracked 刪除。

使用者明確追加 30 分鐘，不是正式十例重驗授權：一版 `--short-workflow`、三種 fresh MVP，期限後停止。TC-01／07：兩個已送出案例 route/model/context 與三個 workspace hashes/policy 一致；missing 嘗試擴大搜尋但未取得其他資料，不代表遵守指定路徑。TC-03：兩例 GUI 送出／工具可見，無完整最後回答；corrupt 未送出。TC-04：正式十例未執行。TC-05：36/36 POC 測試、保留失敗與既有 Archify、Graphify 不建圖、本機 PR Lens。TC-06：Mac 未通過、Windows 未開始、Draft 交人審。詳見 [E006 驗證](short-verification.md)。

## E007／限定指令修訂決策

Goal、Non-Goal、In-Scope、Out-Of-Scope、ReadOnly、Written、Modify、Deleted、TestCase 九欄位保留。Written 增加 E007／基線與提案紀錄；Modify 本批只有教程／契約／驗證／續作文件，Deleted 無。TC-01／07 三例 hashes／模型／本機路由／原隔離相符；TC-03 三例實際側欄送出／工具可見，正常與 corrupt 最後回答已見，missing 無最後回答；TC-04 未通過、不進正式十例；TC-05 文件變更不重跑既有36測試；TC-06 Mac 未驗收、不進 Windows。使用者另同意新 opt-in agent.excel.prompt 修改與輸出型別／位置澄清，將另記新 config hash；model/digest/context/sampler／權限／隔離不變，本 E007 未套用。見 [基線紀錄](baseline-verification.md)。

## E008 指令契約執行對照

Goal、Non-Goal、In-Scope、Out-Of-Scope、ReadOnly、Written、Modify、Deleted、TestCase 九欄位保留。使用者明確批准的例外僅 opt-in config agent.excel.prompt；Written 增加 aligned.py、tests/test_aligned.py、E008及紀錄，Modify 僅ide旗標／prepare／capture與教程。原poc.py／isolation.py／資料／oracle／鎖檔與tinyllama資產仍ReadOnly，Deleted無。原config hash保留，另記新34b0dce9…，不得稱原config未變；實際其餘JSON語義均不變。

TC-01正常身份／65536／主輔本機stream／hashes相符，missing僅setup無session；TC-02官方新版未測；TC-03正常真實GUI工具與最後訊息可見，但未分析，missing GUI不可得、corrupt未送；TC-04正式十例未執行；TC-05 40/40 POC、原圖維護與本機PR Lens，不代表E2E；TC-06 Mac未驗收、Windows未開始；TC-07原E004邊界與權限保留，無fallback／放寬。詳見 [E008](aligned-verification.md)。

## E008 後續契約對照

九欄位保留；Written增加E008補驗／thinking提案與紀錄，Modify本批僅文件，ReadOnly不變，Deleted無。TC-01／07補驗兩例hashes／同一34b0dce9…／模型／65536／本機路由／邊界相符；TC-03兩例真正側欄送出、工具與最後回答已見；TC-04三例候選仍失敗，不進正式十例；TC-05沿用既有40項、維護本機圖件；TC-06 Mac未通過、Windows未開始。使用者另批准E009的唯一推理模式變因與50分鐘上限，未套入或重判E008，見 [補驗](../../../experiments/E008/followup-20261110.md)。

## E009 thinking 契約對照

Goal、Non-Goal、In-Scope、Out-Of-Scope、ReadOnly、Written、Modify、Deleted、TestCase 九欄位保留。使用者例外僅新增thinking opt-in的reasoningEffort none→medium，無具名level保證。Written增加thinking.py、test_thinking.py、E009與驗證紀錄；Modify限ide.py互斥prepare／capture、教程／紀錄；ReadOnly保留poc.py、isolation.py、aligned.py、shortflow.py、workflow.py、fixture／oracle／uv.lock與tinyllama資產，Deleted無。

TC-01／07：所有首次樣本核對固定主輔本機route／digest／65536與hash／原policy，config新802cb27b…並保留original／aligned hash，不冒稱config沒改。TC-02：官方TUI本候選未驗。TC-03：probe與三例真實側欄送出，GUI工具／最後或中止狀態按實際列E009，未完成者不補成pass。TC-04：正常未完成，負面依raw判失敗／缺口，正式十例未執行。TC-05：46/46 helper回歸、原Archify再驗9/9與原視覺檢查、Graphify不建圖、本機bounded diff PR Lens；均不等於E2E。TC-06：Mac未驗收、Windows未開始，Draft交human review／needs-rework，不合併。見 [thinking紀錄](thinking-verification.md)。
