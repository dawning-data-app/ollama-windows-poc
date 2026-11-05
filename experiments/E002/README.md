# E002：現成側邊欄前端與既有 backend 相容性

## 驗證什麼
- 設計日期：2026-11-05。
- 主要問題：OpenChamber 1.24.2 的側邊欄能否連接受控本機 OpenCode 1.19.5，送出需求並顯示真實 Python 工具結果與回答？
- 假設：採現成 extension 的 external apiUrl 設定，可保留 1.19.5、相同 opencode.json、主輔本機模型及 uv Python，不需自製 extension。

## 為什麼
- OpenChamber v2.6.1 明確拒絕 OpenCode 1.x；v1.24.2 manifest 使用 @opencode-ai/sdk 1.18.31，支援 external apiUrl，但這不足以證明實際相容。
- 文件可說明啟動方式，無法證明 extension host 實際繼承的 cwd／env 或 UI/SDK 與本機工具相容，故需最小實驗。結論決定是否沿用此介面進 E2E。

## 成功與失敗判準
- 執行前固定：GUI 入口實際送出環境探測；工具輸出確認指定 workspace 與 .venv Python，最終繁中回覆可見；session 匯出、有效 config、模型 digest／65536 context 與本機 route 一致。必須從側邊欄送出，終端啟動不算成立。
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
- 執行日期：尚未執行。
- 實驗狀態：未執行。
- 本輪驗證任務完成：否；尚待最小 GUI 操作。

## 結果與證據
- 官方來源與固定版下載、manifest 檢視保留於本機 sources；尚無 runtime 假設成立證據。
- 來源： https://marketplace.visualstudio.com/items?itemName=sst-dev.opencode ；https://github.com/openchamber/openchamber/tree/v1.24.2/packages/vscode 。

## 結論與限制
- 尚不可推進本介面 E2E；E003 執行隔離尚未成立，先停止本最小 GUI 驗證。完成隔離並依原判準操作後才可判讀此介面。
- 本實驗不核准 backend 升級、模型契約變更或自製 extension；Windows 未執行。
