# Extension 增量驗證（2026-11-05）

這是既有 Mac CLI/TUI [基準紀錄](verification.md) 的增量，不改寫基準。**目前隔離後重測中：E004 與 OpenChamber 最小驗證已成立，尚不能宣稱完整 Mac 驗收。** 停止點是 Draft PR 與 human review；Windows 尚未執行。未完成的案例明確保留，不把安裝或啟動當成 E2E。

## 固定條件

OpenCode 1.19.5、Ollama 0.31.1、Python 3.12.12、VS Code 1.137.0、uv 0.9.2；主／輔模型皆為本機 Qwen 9b。digest `5eb3a683cbfed5baef1d1f24e2f54afd93e8a9ba344ca71eb8bb37129cf545fe`，context 65536。資料、uv.lock、oracle 與基準一致；有效 opencode.json hash 為 `7dac6527308a16d50dc84c9c1edcbc10025aa0e0d35a29cf14036e5981abc688`。不提供 oracle、舊答案或分析程式給代理。

版本與公開來源見 [教程](extensions.md)。官方 extension 固定 1.0.0；OpenChamber 固定 1.24.2，沒有升級 backend。較新的 2.6.1 拒絕 OpenCode 1.x，屬文件／source 已可回答的相容性限制；1.24.2 是否可用仍需實測。

## 最小可行性

| 實驗 | 狀態與證據 |
|---|---|
| [E001](../../../experiments/E001/README.md) 官方入口 | 成功：Cmd+Esc／Cmd+Shift+Esc 建立 TUI，receipt 的 cwd/config/uv 正確；真實 pwd／uv Python 與繁中回答可見。檔案引用可附加全文，但本輪未保留選取行數。 |
| [E002](../../../experiments/E002/README.md) 側邊欄 | 成功：真實側欄送出、工具輸出與最終繁中回覆可見，主輔本機 route、cwd/config/uv 與 hashes 相符。 |

| [E003](../../../experiments/E003/README.md) 執行隔離 | 無法判定：部分路徑拒絕成立，但 Python／推論／真實工具鏈未完整通過；兩次修正額度已用完，禁止接入。 |

| [E004](../../../experiments/E004/README.md) 額外有限隔離 | 成功：兩次修正內完成 OS 路徑拒絕、openpyxl、localhost 與真正 OpenCode Python 工具／最終回覆；新 helper 接入同一 policy。 |

官方環境 probe：run `20261105T082000-af34bc76`、session `ses_e55305e63fferG85lGQWc8CxCo`。第一個獨立 user-data 程序不能由 GUI 控制定位，該嘗試為無法判定；改為同一程序的專用 profile 才完成。使用者明確允許信任本次 `runs` 根目錄，未關閉 workspace trust。

引用專用新 TUI session `ses_e552c9355ffewJ4wGP4R1yL0uE` 的匯出顯示 `file` part、synthetic Read 與 context-probe.txt 全文。它不是正常 Excel 案例，確認附檔後中止。直接把中文貼在 `#L1` 後的另一份輸入只有 text，不能宣稱已附檔；檔案建議解析後也未保留行數 URL。正式分析從空白編輯器起始，逐輪檢查 user parts，不隱瞞 extension 的額外上下文。

## 官方 extension 的終端 TUI（隔離前，原始結果保留）

| 案例 | run／session | 執行者核對 |
|---|---|---|
| sales 1 | `20261105T082628-5b7a001f`／`ses_e5528d57cffevlY81ktkEP1l8v` | 315.716 秒；工具與最終繁中回答可見，數值／排名正確、protected hashes 未變，主輔 stream 皆本機 Qwen，digest/context 相符。 |
| sales 2 | `20261105T083907-61caf674`／`ses_e5520b78dffeDLB3J68yVLU9N4` | 185.832 秒；數值／排名、真實計算程式、GUI 最終回答與主輔本機路由核對相符；無附檔，原始需求逐字相符。 |
| sales 3 | `20261105T084817-c0d3182d`／`ses_e551872a1ffeYfKOAOkvAXRZ0O` | 462.270 秒；未通過：monthly_sales 為 YYYY-MM-DD 鍵名，與要求的 YYYY-MM 不符；對話誤稱已完成月額。其他數值／排名、hashes、主輔本機路由可核對。 |
| missing | `20261105T085950-276bdd12`／`ses_e550e141bffeu6FFMZBKixnn0L` | 未通過並中止：find /private/tmp 發現其他 session，並 ls 另一 case 的 Excel 目錄；沒有看到讀取舊答案檔，不把路徑發現說成已讀答案。 |
| corrupt | 尚未建立 | 因隔離缺口停止，未執行。 |

sales 1 的 user parts 僅完整原始需求，與 prompt.txt 逐字相符，沒有附檔／選取 context。生成腳本真正以 openpyxl 讀 Sales 並依資料列計算，測試者未提供修正答案；代理自行修正欄位讀取。一般資料型別或髒資料處理不屬本情境保證。

## OpenChamber 側邊欄

最小驗證已成立：run `20261105T093414-cc98abb6`／session `ses_e54e9f081ffenJYHMmbs4UXU2L`。實際點側欄送出、展開 pwd 與 Python tool card，看到最終繁中回答；user parts 僅原始 probe，無選取／附檔。此 probe 不計入正常分析三輪。

## 隔離後 fresh E2E（持續更新）

| 介面／案例 | run／session | 狀態 |
|---|---|---|
| 官方 missing | `20261105T093158-f28c197f`／`ses_e54f15127ffek3vEs8uzAJG6Qm` | 約 179 秒；完整繁中說明找不到輸入、無 answer.json、無跨 session 探索，hashes／路由／隔離 receipt 相符，GUI 工具與結論已見。回覆將資料夾叫作檔案並多加 /xls/xlsx，記為敘述限制。 |
| 官方初版隔離 sales | `20261105T094225-116d9cef`／`ses_e54e527d3ffebRy7X38AD4soGk` | 未通過：900 秒達限後 UI 中止；錯誤輸出路徑、Python SyntaxError 與 zsh here-doc tmp EPERM，沒有完整分析結果。原始失敗保留。 |
| 官方 sales 2／3／corrupt | 尚未執行 | 不宣稱通過。 |
| 側欄 sales 1／2／3／missing／corrupt | 尚未執行 | 不宣稱通過。 |

## 回歸、圖件與人審

本輪 POC unittest 20/20，新增測試防止部分回覆、錯誤 route 或改寫鎖檔被當成通過。既有根目錄 10 項在基準已通過，本輪已重跑通過。tinyllama CLI／腳本／測試／簡報未改動。

Archify [隔離後增量架構圖](../diagrams/extensions-isolated.html) 已通過 showcase 9/9、0 errors／0 warnings，來源 revision d2399f0；四種 desktop viewport 無 overflow，四張明暗截圖已實際檢視並記錄 visual review passed，詳見 [receipt](../diagrams/extensions-isolated.receipt.json)。繁中內容的固定 Viewer UI／html lang 回退英文。原基準圖保留。Graphify 無既有可用 graph，採定點讀碼，未建圖。PR Lens 將依最終真實 base/head 在 repo 外更新、validate/render，不上傳圖件；GitHub Draft PR 由使用者另行授權更新。

原始 session/export、user context、模型／程序／工具證據留在本機暫存 `local-excel-extensions`，repo 只提交可公開摘要。核對器固定 `e2e_passed: false`，還需獨立人工驗收。原 extension helper 並非 OS sandbox；missing 已證明僅分離資料夾無法阻止跨 session 探索。本輪僅使用合成資料，E004 後新 run 套用 OS profile，舊無隔離 run 仍拒絕啟動，沒有無隔離 fallback。UI 最終回覆及程式品質的已知限制會依觀察補記，不以 exit 0 冒充完整成功。

已知敘述限制：第二輪模型自行使用 NT$，但合成資料未定義幣別；只核對數值與分組／排名，不把模型補充的幣別當作來源資料。兩輪生成程式對其他日期格式或髒資料的處理亦非本 POC 保證。

官方正常三輪結果為 2/3 符合完整機器契約。第三輪原始失敗保留，不手改生成程式／答案，也不換成功樣本。固定資料的日期皆為每月首日，按日鍵分組會碰巧得到相同金額，必須連鍵名一起核對；對話看似正確不能取代獨立 oracle。Mac 尚不可宣稱完整驗收通過。

E003 部分證據不能取代完整工具鏈；E004 已補齊最小驗證，仍不能以此取代兩介面完整 E2E。原 normal 2/3 不構成隔離後重現；新增結果逐輪記錄。原始 missing 工具包含 `find /private/tmp`、列出既有 runs 及 `ls` 其他案例輸入，已以 verified pid 停止；本機 stopped.json 與原始 session export 保留。

初版隔離 E2E 找到 zsh here-doc 暫存缺口：本機 zshparam 手冊說明 TMPPREFIX 預設 /tmp/zsh，並不隨 TMPDIR 改變。相同 policy 的最小對照，未設前 exit 1／EPERM，設為本次 run/tmp/zsh 後 exit 0。helper 已補該環境變數，未放寬 profile、未改模型／資料／提示。為驗證最終 runtime，另列修正後三輪 fresh 正常；不刪除或用成功覆蓋上述失敗。
