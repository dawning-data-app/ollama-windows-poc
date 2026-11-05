# python-implementation 工作契約

| 欄位 | 本 topic 邊界 |
|---|---|
| Goal | 給資料夾路徑，本機 Qwen 自主使用 Python 工具分析 Excel，結果可核對且有教程；Mac 完成才 Windows。 |
| Non-Goal | 不做報表產品、網站、MCP、雲端推論或模型評比。 |
| In-Scope | 獨立 uv/openpyxl 專案、合成資料、session 準備、本機設定、獨立核對、教程與本機圖件。 |
| Out-Of-Scope | tinyllama 重構、公開 API 變更、Graphify 建圖、工具全域整合、發布與合併。Draft PR 由使用者另行明確授權。 |
| ReadOnly | 舊 CLI／Windows 腳本／測試／簡報、AGENTS、hooks、runtime、skills、GitHub 設定與 .gitignore。 |
| Written | 本目錄新資產；run/evidence 在 repo 外系統暫存目錄；PR Lens 在 repo 外。oracle 不複製至 agent workspace。 |
| Modify | 既有 tracked 檔只有根 README 增加入口。 |
| Deleted | 無既有 tracked 刪除；只清理本次生成的程式或輸出，不刪資料、oracle 或歷史證據。 |
| TestCase | TC-01 模型／context／路由；TC-02 固定 Excel 正確性；TC-03 三次 fresh sessions 與 missing/corrupt；TC-04 Mac 通過後 Windows；TC-05 圖件來源與驗證。 |

分支：`feat/andrew/local-excel-poc`。基點：`7dc9902a9a6b47fa0a1f1d9a79e1ce21fce2e561`。只在獨立 feature worktree 實作；dev worktree 不改動。

## 技能邊界

- Graphify：沒有既有 graph，採定點讀碼；不 extract。未來若有圖，固定 graphifyy 0.9.73，所有命令設 `GRAPHIFY_NO_AUTO_REFRESH=1`，重要關係回讀 source。
- Archify：`diagrams` 的 workflow 是理解工具，不是 E2E 成功證據；需 showcase 九項檢查、deliver 與四種 viewport visual-check，實際看截圖後才寫視覺判定。繁中內容的固定 Viewer UI／HTML lang 回退英文。
- PR Lens：固定 CLI 0.11.0，只針對真實 base/head diff 作本機 validate/render；規格與結果在 repo 外。不跑 canvas、upload、server 或工具內 PR 發布。缺可用 head 時 deferred；本次 commit／push／Draft PR 使用 Git／GitHub 能力，為使用者另外明確授權。

## 人工審查完成條件

測試者確認每次生成程式有實際讀取銷售 XLSX、計算與本機工具紀錄；核對數字、排名、protected-input hashes、模型身份／context／路由、答案污染限制。三次 CLI 之外要有 VS Code TUI 操作證據；負面案例須明確說明讀取失敗。記錄各項 pass/fail/unverified，不以程式 exit 0 或圖件通過替代。
