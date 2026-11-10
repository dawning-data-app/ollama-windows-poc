# 下班斷點：2026-11-05

歷史狀態：2026-11-05 使用者明確要求暫停。下列停止證據保留。

2026-11-06 使用者要求從斷點續作；唯讀確認 feature／dev clean、PR head 為 `4626391` 且仍為 Draft。已重新核對固定 runtime／模型、通過 20 項 POC 測試，並另建五個 fresh 側欄案例。最新結果以 [extension-verification.md](extension-verification.md) 為準；Mac 尚未完整驗收，Windows 未開始，不合併。

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

## 11/05 原續作清單（歷史）

1. 唯讀確認此 feature branch、worktree、PR 與 checkpoint commit。不得改 dev worktree。
2. 確認 /tmp 的 pinned OpenCode 1.19.5 是否仍存在；若已清空，按教程固定來源重建並核對版本。已安裝 VS Code profiles、Ollama 模型與 repo 鎖檔仍須核對。
3. 側邊欄重新建三個 fresh sales，再各一個 missing／corrupt；由 OpenChamber 真正送出，不能以 CLI／HTTP prompt 代替。保留中止案例，不續接舊對話，不拷貝 archive 中的舊答案或分析程式至 agent workspace。
4. 每次核對 Python／繁中回答／全部數值排名／hashes／主輔身份／恰好 65536／路由／額外上下文。TUI 先前三輪多一個尾端空白，側欄中止輪逐字相符、無額外附檔／system override。
5. 更新教程、九欄位契約、驗證紀錄；依最終 diff 更新本機 PR Lens validate/render 與 Draft PR。現有圖優先，不自行建 Graphify 圖。
6. commit by topic → push → Draft PR → human review。不得把數值／敘述失敗當完成，不自改模型契約、升級 backend 或自製 extension；有此需要須交決策。Mac 驗收後才 Windows。

原始 evidence 與 archive 僅供 evaluator／human review，絕不提供受測代理。2026-11-05 暫停期間沒有啟動新測試；2026-11-06 明確續作後另建 fresh sessions。

## 2026-11-06 本輪交接

已按上列清單另建五個 fresh 側欄案例並完成 backend 執行；三輪正常 JSON 2/3 符合，第 1 輪分組錯誤、第 2 輪額外月額錯誤，第 3 輪要求欄位正確但有敘述限制。missing 無答案但查錯目錄；corrupt 真實 Python 損毀錯誤已見，最後繁中回答僅能從 backend 匯出，GUI cgWindowNotFound 的缺口待人工補驗。所有 run／session ID 與結果見 extension-verification.md，昨天中止案例不計入新三輪。

07:50 UTC GUI 補驗：使用者解鎖後，在同一 corrupt 側欄看到最後完整繁中錯誤報告，展開最後 uv Python ZIP 錯誤並目視 screenshot；沒有重送需求、重啟 backend 或替換案例。上述 GUI 未驗證為先前交接狀態，現已補齊；分析不穩定與敘述錯誤仍交 human review，Mac 未通過。

本輪第一次交付證據與 PR Lens：`/Users/andrew/.codex/artifacts/local-excel-extensions/review-20261106`。歷史 checkpoint archive 不覆蓋。既有 Draft PR 保持 human review／needs-rework；不重跑以替換失敗，不進 Windows、不合併。若只補看 corrupt 既有最後回答，應查看上述同一 session，不另送需求，也不把匯出文字冒充已在 GUI 驗證。

GUI 補驗後最終證據與 PR Lens：`/Users/andrew/.codex/artifacts/local-excel-extensions/review-20261106-gui-followup`。第一版 review-20261106 原樣保留。

## 2026-11-10 修正續作停點

新 E005 兩版 MVP 已到事前嘗試上限，沒有成熟修正可凍結，因此正式十例未執行。原始失敗、新 MVP 與錯誤／時間戳見 repair-verification.md；原 b121801 交付不覆蓋。新流程僅實驗 opt-in，原預設及受保護資產不動。

Mac 目標未達成；下一個待決策為一版更短流程、正常／missing／corrupt 各一個 600 秒 fresh MVP，合計 30 分鐘的 E005 建議。尚未授權追加，沒有第三版／模型升級／權限擴張。完成本輪 commit／push／Draft PR 更新後交 human review，不合併、不進 Windows。持久證據：`/Users/andrew/.codex/artifacts/local-excel-repair-20261110`。

## E006 後續狀態（上述待授權為歷史）

使用者已明確授權追加 30 分鐘，E006 一版短流程已執行至期限。正常四次 Python 錯誤、600 秒內未完成；missing 錯誤字串／擴大搜尋違反契約且無最後回答；corrupt 因 GUI 逾時／reset 未送出。兩個已送出 session，沒有重試；不替換歷史失敗。完整三例驗證仍未完成，原定 Mac 目標未達成，正式十例／Windows 均未執行。詳見 [短式驗證紀錄](short-verification.md) 及 [E006](../../../experiments/E006/README.md)。

本輪受限 server 三個埠均已關閉，沒有停止全域 Ollama。保護資產／模型／65536／路由／隔離保留，另存 `/Users/andrew/.codex/artifacts/local-excel-short-20261110`，不覆蓋 E005。下一個待決策為受控環境基線實驗（降低同時視窗負擔，先量 API／GUI／記憶體）或保留 needs-rework；不得自行加時或變更模型／權限。續作前仍須唯讀核對 feature branch／worktree／Draft PR head，不在 dev 實作。

## E007 後續停點

三個新 fresh MVP 已送出與收證，環境 GUI／API 可觀察，正常數值正確但格式不符、missing 無最後回答、corrupt 真實錯誤正確但流程／格式不符。三個 server 均已停止，原失敗不覆蓋；見 [基線紀錄](baseline-verification.md)。持久證據 `/Users/andrew/.codex/artifacts/local-excel-baseline-20261110`。使用者已明確採用限定指令修訂提案，下一批另計最多40分鐘／一候選三例 fresh MVP；不直接正式十例、不改模型／權限／隔離、不在 dev 實作、不合併。

## E008 GUI不可得斷點

候選 source commit d01d474，protocol excel-aligned-v1，新 config hash 34b0dce9…，僅已批准的 agent.excel.prompt改變；40/40 POC通過。正常91.871秒後只給後續計畫，無analysis／answer；missing已準備但session=0，04:25:37 UTC因cgWindowNotFound清理本次server／guard，corrupt未準備。詳見 [E008](aligned-verification.md)。原截止04:49:15 UTC保留，未用盡40分鐘，不重置；使用者解鎖／顯示視窗仍待回覆。續作先唯讀核對feature／branch／Draft PR，未超時可重新prepare零受測session的missing再首次送出，保留舊setup；不重跑失敗正常／補追問。超時則新投入另決策。持久證據 `/Users/andrew/.codex/artifacts/local-excel-aligned-20261110`。正式十例／Windows未開始，不合併。

## E008 負面補驗完成／下一決策已授權

使用者05:30 UTC再次續作，另列05:31–06:01的30分鐘補兩個未送出案例；本次不是舊期限重置。missing／corrupt首次受測與GUI收證已完成，仍有路徑／停止／格式錯誤，詳見 [補驗](../../../experiments/E008/followup-20261110.md)。兩個backend已停止，候選與ReadOnly資產不變，原正常失敗／GUI setup／archive保留。使用者已明確批准新thinking候選：reasoningEffort none→medium相容值，先最多10分鐘工具鏈、成立後40分鐘三例，總50；其他模型／context／sampler／output／路由／指令／權限／隔離不改。下一批E009另列，不進正式十例，不在dev實作，不合併。

## E009 thinking 實驗停點

在既有feature／branch完成已批准的唯一reasoningEffort變因實驗，source754f9fb／probe-review修正63ba9db。probe真實執行在10分鐘內完成；人工核對晚39秒已揭露，未重送，總截止06:49不補時。正常／missing／corrupt各一個fresh側欄樣本保留，候選未成立，不正式重驗。所有本次backend已停止，全域Ollama保留；詳見 [E009](thinking-verification.md)。持久證據 `local-excel-thinking-20261110`；原archive不覆蓋。原預設／CLI/TUI／模型digest／context／sampler／output／隔離與九欄位契約保持，不在dev實作。續作先唯讀核對feature／branch／Draft PR與交付head，下一步為human review／needs-rework決策，不自動加時／改模型或runtime契約、不合併、不進Windows。
