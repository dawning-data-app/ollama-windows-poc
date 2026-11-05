# python-implementation 工作契約

| 欄位 | 本 topic 邊界 |
|---|---|
| Goal | 透過官方 VS Code extension 的終端 TUI，以及現成 extension 的側邊欄聊天，給資料夾路徑，由本機 Qwen 自主寫／執行 Python 分析 Excel；保留 CLI/TUI 基準，Mac 完成才 Windows。 |
| Non-Goal | 不做報表產品、網站、MCP、雲端推論或模型評比；不自動升級 OpenCode、不更換模型契約、不自製 extension。 |
| In-Scope | 沿用 uv/openpyxl／資料／oracle；增加固定版官方 extension 與 OpenChamber 的最小可行性及各三輪正常、missing/corrupt；受控 launcher、專用 VS Code profile、使用者授權的 Mac 隔離 MVP、上下文／路由證據、教程與本機圖件。 |
| Out-Of-Scope | tinyllama 重構、公開 API 變更、Graphify 建圖、工具全域整合、發布與合併。Draft PR 由使用者另行明確授權。 |
| ReadOnly | 舊 CLI／Windows 腳本／測試／簡報、AGENTS、hooks、runtime、skills、GitHub 設定與 .gitignore。 |
| Written | 本目錄新資產、experiments/E001、E002、E003 與 E004；run/evidence 在 repo 外系統暫存目錄；PR Lens 在 repo 外。oracle 不複製至 agent workspace。 |
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

E004 後續：使用者另行授權 15 分鐘／兩次修正，MVP 已成功，依原條件接入 Mac 隔離與重測。ReadOnly 契約不變。`isolation.py` 與其 OS 回歸屬 Written；新 run 必須具備匹配的 policy／manifest／receipt，舊無隔離 run 仍拒絕。E003 的暫停狀態為歷史，不覆寫實驗結論。兩種介面仍要各完成三輪正常與 missing/corrupt，Mac 尚未驗收。
