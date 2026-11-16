# E001：官方 extension 的 session 邊界與檔案引用

## 驗證什麼
- 設計日期：2026-11-05。
- 主要問題：官方 sst-dev.opencode 1.0.0 能否透過快捷鍵在乾淨 session 的 cwd／config／uv Python 啟動，且檔案引用可觀察？
- 假設：隔離 VS Code profile 與 terminal env 可保持既有 OpenCode 1.19.5 和模型契約；聊天仍是終端 TUI。

## 為什麼
- 官方 Marketplace 的 1.0.0 VSIX；實際 bundle createTerminal/sendText(opencode)，檔案快捷鍵 sendText(@path#L...)。原始碼標籤 1.19.5 與 Marketplace 的 extension 版本不同，不混用。
- 文件可說明啟動方式，無法證明 extension host 實際繼承的 cwd／env 或 UI/SDK 與本機工具相容，故需最小實驗。結論決定是否沿用此介面進 E2E。

## 成功與失敗判準
- 執行前固定：GUI 入口實際送出環境探測；工具輸出確認指定 workspace 與 .venv Python，最終繁中回覆可見；session 匯出、有效 config、模型 digest／65536 context 與本機 route 一致。另外觀察快捷鍵檔案引用與選取行數，不提供解法。
- 失敗：可觀察到錯誤 cwd/env、API 不相容、錯誤模型／路由，或完成回覆卻沒有要求的真實工具執行。
- 無法判定：GUI 不可控制、權限／必要前置條件缺失、或時限內沒有完整證據。
- 最小實驗每個介面最多 15 分鐘互動，最多兩次針對設定／環境的修正；不換 backend、模型契約或自製 extension。達界線則停依賴 E2E，保留部分證據。E2E 每案例 900 秒操作上限沿用基準，不作效能合格線。

## 環境與前置條件
- Mac M3 Pro 18 GB；VS Code 1.137.0；OpenCode 1.19.5；Ollama 0.31.1；uv 0.9.2；Python 3.12.12。
- 固定 Qwen 9b digest 與 65536 context、既有 uv.lock；只用合成資料。最小探測不做銷售分析，不提供分析程式或 oracle。
- 隔離 VS Code user-data／extensions；若 GUI 要求新的信任授權，先取得使用者授權，不關閉 workspace trust。

## 重現步驟
- feature 的 `poc/local-excel/ide.py prepare/launch/capture`；所有 runtime/evidence 在 repo 外 `local-excel-extensions`。
- 最小輸入：請以 bash 的 pwd 與 uv Python 工具確認目前目錄及 Python interpreter，讀 context-probe.txt 並以繁中回覆環境狀態；不要進行 Excel 分析或新增依賴。
- 觀察 GUI、extension 啟動 receipt／backend cwd、有效 config、實際工具與 session-export；無工具紀錄的純文字宣稱不算。
- 實際執行位置與結果於下節補記；未將安裝成功當作假設成立。

## 是否成功
- 執行日期：2026-11-05。
- 實驗狀態：成功。
- 本輪驗證任務完成：是；實際快捷啟動、檔案行數引用、pwd／uv Python 工具與繁中回覆均觀察到，符合事前成功判準。

## 結果與證據
- 官方來源與固定版下載、manifest 檢視保留於本機 sources；最小 run `20261105T082000-af34bc76`、session `ses_e55305e63fferG85lGQWc8CxCo`：GUI 以 Cmd+Esc 啟動，Cmd+Option+K 插入 `@context-probe.txt#L1`；真實 pwd 與 uv Python 輸出均指向本次 workspace／.venv，最終繁中回覆可見。有效 config、模型與 65536 context 核對相符。
- 來源： https://marketplace.visualstudio.com/items?itemName=sst-dev.opencode ；https://github.com/openchamber/openchamber/tree/v1.24.2/packages/vscode 。

## 結論與限制
- 此為原入口的最小環境驗證，不能取代銷售分析正確性；後續 missing 發現跨 session 探索，現依 E003 結果停止新 E2E，不能沿用此成功標記宣稱檔案隔離。
- 本實驗不核准 backend 升級、模型契約變更或自製 extension；Windows 未執行。

第一次以獨立 user-data 程序啟動時，GUI 控制只能定位原程序，該次為無法判定且未送需求；改用同一程序的專用 profile 與 workspace env 後完成。使用者明確授權信任本次 runs 根目錄。原本錯放 workspace 的使用者層更新設定已移除，沒有關閉 workspace trust。

引用解析的實際限制：最初與中文貼文相連的 `@...#L1` 只留在 text part，不能宣稱已附檔。另一個新 TUI session `ses_e552c9355ffewJ4wGP4R1yL0uE` 完成檔案建議選取後，匯出含真實 file part 與 synthetic Read 全文。其 URL 沒有行數範圍；因此僅確認快捷鍵插入 `#L1`，不能宣稱模型只收到選取行。引用專用 session 在確認附檔後中止，不計入任何 Excel 正常案例；其模型曾自發探索 Excel，不能當成使用者已送出完整分析需求。正式三次 fresh 分析從沒有開啟編輯器檔案的 workspace 起始，額外上下文須逐輪檢查。
