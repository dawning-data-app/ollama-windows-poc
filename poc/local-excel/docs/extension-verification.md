# Extension 增量驗證（2026-11-05）

這是既有 Mac CLI/TUI [基準紀錄](verification.md) 的增量，不改寫基準。停止點是 Draft PR 與 human review；Windows 尚未執行。未完成的案例明確保留，不把安裝或啟動當成 E2E。

## 固定條件

OpenCode 1.19.5、Ollama 0.31.1、Python 3.12.12、VS Code 1.137.0、uv 0.9.2；主／輔模型皆為本機 Qwen 9b。digest `5eb3a683cbfed5baef1d1f24e2f54afd93e8a9ba344ca71eb8bb37129cf545fe`，context 65536。資料、uv.lock、oracle 與基準一致；有效 opencode.json hash 為 `7dac6527308a16d50dc84c9c1edcbc10025aa0e0d35a29cf14036e5981abc688`。不提供 oracle、舊答案或分析程式給代理。

版本與公開來源見 [教程](extensions.md)。官方 extension 固定 1.0.0；OpenChamber 固定 1.24.2，沒有升級 backend。較新的 2.6.1 拒絕 OpenCode 1.x，屬文件／source 已可回答的相容性限制；1.24.2 是否可用仍需實測。

## 最小可行性

| 實驗 | 狀態與證據 |
|---|---|
| [E001](../../../experiments/E001/README.md) 官方入口 | 成功：Cmd+Esc／Cmd+Shift+Esc 建立 TUI，receipt 的 cwd/config/uv 正確；真實 pwd／uv Python 與繁中回答可見。檔案引用可附加全文，但本輪未保留選取行數。 |
| [E002](../../../experiments/E002/README.md) 側邊欄 | 未執行。已檢查版本與 source、安裝隔離套件，尚未送出側邊欄需求。 |

官方環境 probe：run `20261105T082000-af34bc76`、session `ses_e55305e63fferG85lGQWc8CxCo`。第一個獨立 user-data 程序不能由 GUI 控制定位，該嘗試為無法判定；改為同一程序的專用 profile 才完成。使用者明確允許信任本次 `runs` 根目錄，未關閉 workspace trust。

引用專用新 TUI session `ses_e552c9355ffewJ4wGP4R1yL0uE` 的匯出顯示 `file` part、synthetic Read 與 context-probe.txt 全文。它不是正常 Excel 案例，確認附檔後中止。直接把中文貼在 `#L1` 後的另一份輸入只有 text，不能宣稱已附檔；檔案建議解析後也未保留行數 URL。正式分析從空白編輯器起始，逐輪檢查 user parts，不隱瞞 extension 的額外上下文。

## 官方 extension 的終端 TUI

| 案例 | run／session | 執行者核對 |
|---|---|---|
| sales 1 | `20261105T082628-5b7a001f`／`ses_e5528d57cffevlY81ktkEP1l8v` | 315.716 秒；工具與最終繁中回答可見，數值／排名正確、protected hashes 未變，主輔 stream 皆本機 Qwen，digest/context 相符。 |
| sales 2 | `20261105T083907-61caf674`／`ses_e5520b78dffeDLB3J68yVLU9N4` | 185.832 秒；數值／排名、真實計算程式、GUI 最終回答與主輔本機路由核對相符；無附檔，原始需求逐字相符。 |
| sales 3 | `20261105T084817-c0d3182d` | 執行中，尚未判定。 |
| missing | 尚未建立 | 未執行。 |
| corrupt | 尚未建立 | 未執行。 |

sales 1 的 user parts 僅完整原始需求，與 prompt.txt 逐字相符，沒有附檔／選取 context。生成腳本真正以 openpyxl 讀 Sales 並依資料列計算，測試者未提供修正答案；代理自行修正欄位讀取。一般資料型別或髒資料處理不屬本情境保證。

## OpenChamber 側邊欄

最小驗證尚未完成；三個 sales、missing、corrupt 全部未執行，不宣稱相容或 E2E 通過。

## 回歸、圖件與人審

本輪 POC unittest 13/13，新增測試防止部分回覆、錯誤 route 或改寫鎖檔被當成通過。既有根目錄 10 項在基準已通過，本輪尚未重跑。tinyllama CLI／腳本／測試／簡報未改動。

Archify [增量架構圖](../diagrams/extensions.html) 已通過 showcase 9/9、0 errors／0 warnings，來源 revision 709dd44；四種 desktop viewport 無 overflow，四張明暗截圖已實際檢視並記錄 visual review passed，詳見 [receipt](../diagrams/extensions.receipt.json)。繁中內容的固定 Viewer UI／html lang 回退英文。原基準圖保留。Graphify 無既有可用 graph，採定點讀碼，未建圖。PR Lens 將依最終真實 base/head 在 repo 外更新、validate/render，不上傳圖件；GitHub Draft PR 由使用者另行授權更新。

原始 session/export、user context、模型／程序／工具證據留在本機暫存 `local-excel-extensions`，repo 只提交可公開摘要。核對器固定 `e2e_passed: false`，還需獨立人工驗收。Python 並非 OS sandbox；本輪僅使用合成資料。UI 最終回覆及程式品質的已知限制會依觀察補記，不以 exit 0 冒充完整成功。

已知敘述限制：第二輪模型自行使用 NT$，但合成資料未定義幣別；只核對數值與分組／排名，不把模型補充的幣別當作來源資料。兩輪生成程式對其他日期格式或髒資料的處理亦非本 POC 保證。
