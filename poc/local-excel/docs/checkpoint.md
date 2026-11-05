# 下班斷點：2026-11-05

狀態：使用者明確要求暫停。停止 E2E，保留 Draft PR／human review；Mac 尚未完整驗收，Windows 未開始，不合併。

## 工作位置

- feature worktree：`/Users/andrew/.codex/worktrees/7e4a/ollama-windows-poc`
- branch：`feat/andrew/local-excel-poc`
- PR： https://github.com/dawning-data-app/ollama-windows-poc/pull/1 （Draft）
- dev worktree：`/Users/andrew/code/python/ollama-windows-poc`，未在此實作。
- 最新程式 revision：`1dbba0d`；本 checkpoint 是其後的紀錄提交，續作先唯讀檢查 git／PR 狀態，避免覆蓋他人變更。
- 持久證據：`/Users/andrew/.codex/artifacts/local-excel-extensions/checkpoint-20261105T105309Z`，包含 review-evidence.zip／SHA-256 與續作輔助資料；不依賴 /tmp 長期保留。

## 已完成與限制

- 官方 sst-dev.opencode 1.0.0、OpenChamber 1.24.2 固定，OpenCode 1.19.5 未升級；官方聊天仍為終端 TUI。
- Qwen digest／65536 context、合成資料、uv.lock、獨立 oracle 保留；主／輔模型本機 Ollama。
- E003 部分證據無法判定；使用者額外授權的 E004 已成功，Mac OS 邊界接入兩種入口。已修正 zsh TMPPREFIX，未放寬 policy。
- 20 項 POC／10 項原 CLI 測試通過；原 CLI/TUI 基準與 tinyllama 資產未改。
- 官方最終 runtime 三輪 JSON 數值契約 2/3 符合：第 2 輪錯將商品當區域；第 3 輪最後摘要誤稱 11 筆交易，實際 12。missing／corrupt 不編造銷售答案，但有資料夾名稱與檔案大小門檻的敘述錯誤。完整紀錄見 extension-verification.md。
- 側欄 E002 最小驗證已真正從 GUI 送出、看到 Python 工具／繁中回覆。完整 Excel 第一輪在本次暫停時中止，不算模型失敗、不算正常三輪之一。
- Archify 隔離圖已交付／showcase 9/9／四種 viewport 與四張明暗截圖已檢視。Graphify 無可用既有圖，未建圖。

## 本次停止的位置

- 中止側欄 run：`20261105T094918-9e035cd7`
- session：`ses_e54adebeeffeu3i1aFFChTTWgw`
- 點 GUI 停止生成，保存 export／user context／hashes／model log；核對命令後停止本次 server PID 78852（127.0.0.1:64156）。全域 Ollama 未停止。
- 尚未完成真實 Python 分析或最後回答，應標為 user-interrupted-incomplete。
- 其餘 prepared runs 未送需求；campaign.json 列明各 UUID。這些可以作線索，但續作建議重新 prepare，以免混淆未使用狀態。

## 下次接續

1. 唯讀確認此 feature branch、worktree、PR 與 checkpoint commit。不得改 dev worktree。
2. 確認 /tmp 的 pinned OpenCode 1.19.5 是否仍存在；若已清空，按教程固定來源重建並核對版本。已安裝 VS Code profiles、Ollama 模型與 repo 鎖檔仍須核對。
3. 側邊欄重新建三個 fresh sales，再各一個 missing／corrupt；由 OpenChamber 真正送出，不能以 CLI／HTTP prompt 代替。保留中止案例，不續接舊對話，不拷貝 archive 中的舊答案或分析程式至 agent workspace。
4. 每次核對 Python／繁中回答／全部數值排名／hashes／主輔身份／恰好 65536／路由／額外上下文。TUI 先前三輪多一個尾端空白，側欄中止輪逐字相符、無額外附檔／system override。
5. 更新教程、九欄位契約、驗證紀錄；依最終 diff 更新本機 PR Lens validate/render 與 Draft PR。現有圖優先，不自行建 Graphify 圖。
6. commit by topic → push → Draft PR → human review。不得把數值／敘述失敗當完成，不自改模型契約、升級 backend 或自製 extension；有此需要須交決策。Mac 驗收後才 Windows。

原始 evidence 與 archive 僅供 evaluator／human review，絕不提供受測代理。使用者下班暫停後，不再啟動新測試。
