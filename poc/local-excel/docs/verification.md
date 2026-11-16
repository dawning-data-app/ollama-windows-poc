# Mac 實測紀錄（2026-11-05）

狀態：Mac CLI 與 VS Code TUI 的執行者證據核對完成，最終 human review 待完成。Windows **未執行**；本紀錄不宣稱 Windows 相容性或整體 E2E 已獲人工驗收。

## 環境與選型

- Apple M3 Pro、18 GB；macOS 26.5.2 arm64。
- VS Code 1.137.0、OpenCode 1.19.5、Ollama 0.31.1、Node 24.19.0、uv 0.9.2。
- Python 3.12.12、openpyxl 3.1.5、et-xmlfile 2.0.0；專用 uv 鎖檔。
- 最終模型 `qwen3.5:9b`、Q4_K_M；實際 context **65536**，載入大小／VRAM 為 7,674,223,656 bytes。
- 原始 registry digest：`56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90`。
- 本機加入 context／coding 參數後 digest：`5eb3a683cbfed5baef1d1f24e2f54afd93e8a9ba344ca71eb8bb37129cf545fe`。
- Ollama 參數：num_ctx 65536、temperature 0.6、top_p 0.95、top_k 20、min_p 0、presence_penalty 0、repeat_penalty 1；OpenCode reasoningEffort none，主／輔模型皆為同一本機模型。

最小工具呼叫通過；也以 OpenAI-compatible 路由實際載入後查 `/api/ps`，確認 context，沒有只依賴 OpenCode 宣告。此機選型依 4b → 9b 的次序完成：4b 曾完成數值計算，但該輪缺最終文字回覆；其他診斷輪混有準備環境、權限與 profile 調整，**不當成公平模型評比**。最終 9b 配置才計入下列三次連續重現。

## CLI 正常案例

每輪 fresh session，只放合成資料、提示及鎖定環境。代理自行找檔、寫程式、執行與修錯，測試者沒有提供分析解法或把 oracle 回餵。三輪均核對到總額 12000、2026-01 為 3300、2026-02 為 8700；北 2800、中 4000、南 5200；排名南／中／北。

| run ID | 分析秒數 | 核對結果 |
|---|---:|---|
| 20261105T073428-3cfa70ad | 286.852 | 數值、工具執行、最終繁中回覆相符；代理自主修正初稿。 |
| 20261105T073918-64151a6c | 230.567 | 數值、工具執行、最終繁中回覆相符；代理自主修正欄位。 |
| 20261105T074314-37b89c2b | 96.126 | 數值、工具執行、最終繁中回覆相符。 |

執行者另外逐份檢視生成的 `analysis.py`：均由 openpyxl 實際讀取 XLSX 並以資料列計算分組，未見讀 oracle／舊答案或寫死核對總額。檢視 effective config、模型串流身份與載入紀錄：主／輔路由皆為 `ollama/qwen3.5:9b`，loopback endpoint，run 後 digest／context 相符。這是執行者證據檢查，仍需使用者獨立 human review。

三次的共同 hash：

| 資產 | SHA-256 |
|---|---|
| sales.xlsx | `9d88b6da7175a8e86188b359cf663b16610cdadeca485a9b773f71bb74858fc4` |
| uv.lock | `02428609b416acb248ddbf9cde9ca2b9365c8237aff057ad0a9c9e3554d20926` |
| session opencode.json | `7dac6527308a16d50dc84c9c1edcbc10025aa0e0d35a29cf14036e5981abc688` |

以上是同一 Mac 上的重現證據，不是效能門檻或跨硬體推論。`check` 仍回傳 `needs-review` 與 `e2e_passed: false`，不會替代獨立驗收。

## CLI 異常案例

| 案例／run ID | 秒數 | 實際觀察 |
|---|---:|---|
| missing／20261105T074456-60e51d08 | 42.937 | glob／ls 找不到 Excel，對話說明沒有資料可分析；沒有建立缺失資料夾或 answer.json。 |
| corrupt／20261105T074545-28dc45bc | 492.911 | openpyxl 實際讀取並報 File is not a zip file；代理檢查 28-byte 偽 XLSX，說明無法分析，未產生 answer.json，原始輸入未改。 |

兩個案例的自動邊界檢查無錯誤，但敘述品質並非完全通過：corrupt 回覆聲稱「正常 Excel 檔案至少數 MB」，此常識敘述錯誤，Excel 可以很小；本測試的重點「不可讀取時不編造銷售數字」達成，該句仍是 human review 已知問題。missing 回覆以工作區沒有 Excel 說明情況，未精確區分指定子資料夾不存在。部分不在 allowlist 的探索命令被拒，代理仍完成失敗說明。

## 圖件與回歸

- 新 POC unittest 10/10；包含真實 uv sync 後離線 interpreter／openpyxl 回歸。
- 既有根目錄 unittest 10/10，舊 CLI／腳本／測試／簡報未改。
- Archify showcase 9/9、0 errors／0 warnings，delivery 完成；1440×900、1600×1000、1920×1080、2048×1320 四 viewport 無 overflow。實際檢視四張明暗主題截圖後記錄 manual visual review passed；詳見 [receipt](../diagrams/receipt.json)。自動 visual-check 的人工欄位仍為 pending，不偽裝自動完成。
- Archify runtime 採 MIT；附 [LICENSE](../diagrams/LICENSE)。
- Graphify 無可用既有 graph，採定點讀碼；未建圖、未自動 refresh。
- PR Lens 固定 0.11.0，最終 commit 後依實際 base/head 在 repo 外 validate/render；只供本機審查，不上傳圖件。

原始 session、生成程式、提示、工具軌跡、模型／環境證據保留在本機暫存 `local-excel-poc` 目錄，未納入 Git。分離工作區可降低答案污染，但不是 OS sandbox 或封包層的離線／資料外洩驗證；本次只使用合成資料。

## VS Code 與交接

VS Code GUI 曾因鎖定／視窗不可見而回報 cgWindowNotFound；使用者解鎖後已恢復。僅依授權信任本次 feature 的 local-excel 資料夾。TUI run `20261105T075356-d71348d9` 已在整合終端完成同一 9b profile 的對話；session ID：`ses_e554ac47effeqMDrJRAYhW5Fg5`。由 GUI 貼上資料夾需求，代理自主找檔、寫程式、執行與修錯，最終畫面及匯出的 stop 回覆均包含正確總額、各月／區域金額及排名。對話自送出至完成約 410 秒，不含啟動準備。

執行者核對 `answer.json` 與 oracle 無差異、protected hashes 未變；匯出 session 的 provider/model 為 `ollama/qwen3.5:9b`，本機 loaded-after 的 digest／65536 context 相符。檢視生成程式與工具輸出可確認真正讀檔計算；最後分析命令 exit 0。原始 `script` 終端錄製、session JSON、GUI review 摘要留本機，最終畫面已直接觀察，TUI 保留供人工查看。

這輪亦揭露限制：初稿曾把輸出寫往 `/answer.json`，因 root 唯讀而失敗，代理自行修成工作區路徑；日期處理也經自行修正。生成程式透過轉型錯誤略過表頭，字串日期分支不適合一般資料，不能把本次固定合成資料通過當作可直接處理任意 Excel。Python 工具本身不是檔案系統沙箱，`external_directory: deny` 無法隔離任意 Python 存取。

停止點為 Draft PR 與 human review，不合併。Mac human review 完成後才移到 Windows，Windows 必須重跑同模型 digest、鎖檔、資料、三次正常案例與異常案例。
