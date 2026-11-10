# VS Code extension 入口（Mac）

沿用 [CLI/TUI 教程](../README.md) 的 OpenCode 1.19.5、Qwen 9b 固定 digest／65536 context、合成 Excel、uv.lock 與獨立 oracle。本頁增加兩種介面；[驗證紀錄](extension-verification.md) 才是各案例的實際結果。安裝或啟動成功不表示 E2E 通過。

**隔離後驗證已紀錄，Mac 尚未通過完整驗收**：[E003](../../../experiments/E003/README.md) 在有限修正內無法判定；取得使用者額外授權後，[E004](../../../experiments/E004/README.md) 以同一模型／資料完成 OS 與真實工具鏈探測。新 prepare 會產生 Mac policy 並綁定 hash，官方 launcher 與 API server 都限制整個 backend／子程序；舊的無隔離 run 不允許 launch/server，勿手動重用其 launcher。OpenChamber 的 [E002](../../../experiments/E002/README.md) 側欄 probe 已成立；完整 Excel 結果見驗證紀錄。

## 固定來源與版本

| 介面 | 受測套件 | 來源／邊界 |
|---|---|---|
| 官方入口 | `sst-dev.opencode@1.0.0` | [Marketplace](https://marketplace.visualstudio.com/items?itemName=sst-dev.opencode) 的已發佈版本；聊天仍是終端 TUI。CLI 1.19.5 與 extension 版本獨立，不用 CLI tag 冒充已發佈 extension。 |
| 側邊欄聊天 | `fedaykindev.openchamber@1.24.2` | [官方固定版 VSIX](https://github.com/openchamber/openchamber/releases/tag/v1.24.2)，[manifest](https://github.com/openchamber/openchamber/blob/v1.24.2/packages/vscode/package.json) 使用 1.x SDK。先通過最小驗證才做 Excel E2E。 |

官方 1.0.0 VSIX SHA-256：`ddec815ab9a4a481b351e1ea297996688a443d9ac02cb21b7d9b423ce315e0c4`。OpenChamber 1.24.2：`bc101557f23edb353cca57cb5c05061c434c5911def741fc00434030b15aa632`。Marketplace 的 HTTP 回應可能外層 gzip，前一個 hash 是解壓 HTTP content-encoding 後的 VSIX bytes。

查證時最新版 OpenChamber 2.6.1 的 [版本檢查](https://github.com/openchamber/openchamber/blob/v2.6.1/packages/vscode/src/opencodeVersion.ts) 明確拒絕 OpenCode 1.x；本輪沒有升級 backend，選用既成的 1.24.2 驗證。SDK 版本相近不等於相容，見 [E002](../../../experiments/E002/README.md)。若此版不相容，先提出證據與影響交使用者決策；不自行升級、自製 extension 或換模型。

## 專用 profile 與 fresh workspace

只在 feature worktree 的 `poc/local-excel` 執行。`ide.py` 不提供 Excel 解法；它複製原基準的準備資產，檢查 backend 版本／模型 digest，預備 uv，建立專用 launcher 與 workspace 設定。VS Code 的專用 profile 只安裝本介面的 extension；一般 profile 不改設定。

先用 VS Code 的 Profiles UI 建立空白 `Excel POC Official`、`Excel POC OpenChamber` profile，或用 `code --new-window --profile "<名稱>"` 開啟並建立，再從官方來源安裝固定版。例：

```sh
code --profile 'Excel POC Official' --install-extension sst-dev.opencode@1.0.0
# OpenChamber 使用上述官方 v1.24.2 release 的 VSIX，先核對 hash
code --profile 'Excel POC OpenChamber' --install-extension <openchamber-1.24.2.vsix>
```

每次 launch 都以 `code --profile ... --list-extensions --show-versions` 核對受測版本。不把此類使用者層的更新設定寫到 workspace；不更動一般 profile 的更新政策。

在本次環境，使用者另行授權將 `/private/tmp/local-excel-extensions/runs` 加入 VS Code 信任。其他機器若跳出信任提示，由操作者只信任本次合成測試目錄；不關閉 workspace trust。獨立 user-data 程序曾無法由 GUI 控制定位，本輪採同一 VS Code 程序內的專用 profile；VS Code profile 本身不提供 OS 隔離；新 helper 另套 E004 的 Mac sandbox-exec policy。

## 1. 官方 extension：仍在終端對話

```sh
uv run --locked python ide.py prepare --interface official \
  --runs-root /private/tmp/local-excel-extensions/runs \
  --opencode /private/tmp/local-excel-poc/opencode/node_modules/.bin/opencode
Run='<輸出的新 run 目錄>'
cat "$Run/workspace/prompt.txt" # 先複製完整需求
uv run --locked python ide.py launch "$Run"
```

確認視窗標題的 interface／case／run ID。關閉 VS Code 內建的聊天欄，避免把需求送到其他服務。在官方入口按 **Cmd+Esc** 啟動，或 **Cmd+Shift+Esc** 新增 TUI；Windows 快捷鍵另為 Ctrl+Esc／Ctrl+Shift+Esc，尚未實測。確認顯示 `Excel · qwen3.5:9b Local Ollama` 與本次 workspace，再點終端輸入區，貼上需求，等貼上顯示後按 Enter。模型須自主寫、執行與修正程式，測試者不回餵標準答案。

實際 1.0.0 bundle 呼叫 createTerminal 並送出 `opencode`，沒有指定 cwd，也沒有自動附加目前分頁。專用 terminal profile 使用 zsh `-f`、明確 cwd/env；`run/bin/opencode` 拒絕不符的 cwd，記錄 receipt，再以既有鎖定 uv 啟動真正 CLI。`evidence/extension-launch.jsonl`、`python-runtime.stdout` 與 `effective-config.stdout` 用於核對，不只看畫面名稱。

**檔案引用**：在編輯器選取文字後按 Cmd+Option+K。固定版會把 `@檔案#L起迄` 作為文字插到 TUI。這不等於已附檔：實測直接接中文貼文時只有 text part；完成檔案建議選取後才在 session 出現 file part 與 synthetic Read 全文，而且這輪沒有保留行數範圍。先輸入完整需求，再處理引用並確認內容，避免只送出檔名就觸發模型開始工作。只用不含解法的 `context-probe.txt` 測試引用，不引用 oracle、舊答案或分析腳本。正式三輪先從空白編輯器開始，逐輪記錄額外上下文。

## 2. OpenChamber：真正的側邊欄聊天

先做 `prepare --interface chamber --probe` 的最小環境探測。成立條件是從側邊欄送出，看到真實 pwd／uv Python 工具及繁中回覆，並核對 route、digest、context；不是只看到側邊欄。實驗設計與停止條件見 [E002](../../../experiments/E002/README.md)。

採該版既有的 `openchamber.apiUrl` 外部 API 模式，由 helper 在該次 workspace 與受控 env 啟動同一 backend；不採自動下載／升級功能。

```sh
uv run --locked python ide.py prepare --interface chamber \
  --runs-root /private/tmp/local-excel-extensions/runs \
  --opencode /private/tmp/local-excel-poc/opencode/node_modules/.bin/opencode
Run='<輸出的新 run 目錄>'
uv run --locked python ide.py server "$Run" # 只綁 127.0.0.1；記錄 pid/url/cwd
cat "$Run/workspace/prompt.txt"
uv run --locked python ide.py launch "$Run"
```

在 OpenChamber 側邊欄確認本次資料夾、`excel` agent 與本機 9b，從該輸入區送出完整需求。若初始會話清單顯示「正在載入工作階段…」，本輪點該 workspace 的「新增會話」即可進入空白聊天；不把 reload 視為必要步驟。模型圖示本身不足以證明選用的 agent／模型，還須核對 session metadata 與 runtime streams。不得用 helper 的 HTTP prompt API 或 CLI run 代替 GUI 送出。實際相容性與工具／最終回答呈現以驗證紀錄為準。每次測完只關閉本次視窗／server，不能終止使用者其他程序。

## 各介面的證據與驗收

正常案例各做三次 `prepare`；missing／corrupt 各一次，使用 `--case missing`／`--case corrupt`。每個案例最多 900 秒，記錄失敗或未完整完成，不挑選成功案例替換失敗。`--probe` 的環境探測不能算正常分析案例。

```sh
uv run --locked python ide.py capture "$Run" # 列出該次 session
uv run --locked python ide.py capture "$Run" --session-id <實際ID>
```

capture 保存原始 session JSON、所有 user parts（含檔案與 synthetic context）、推論日誌及 loaded model。自動核對完整回覆、真實成功 Python 工具、數值／排名、protected hashes、主／輔模型身份與 65536 context；仍是 `needs-human-review`，不自動宣稱 E2E 通過。

執行者另外看實際 GUI 的工具與最後繁中回覆，逐份讀生成程式確認真的計算 XLSX，檢查額外上下文是否含未授權資料、主輔推論與有效 endpoint。錯誤案例需讀敘述是否清楚且無編造數字。原始證據留 repo 外，repo 只存可公開摘要。新工具邊界套用 E004 的 Mac sandbox-exec，允許本次 workspace/tmp/config/cache/state 與唯讀系統／已鎖定工具，阻止其他 session 與 oracle 內容讀取。只允許 Ollama 11434 的 loopback 出站、受測 IDE 所需本機監聽及系統 resolver。這是有限案例驗證，sandbox-exec 已棄用、system.sb 為 Apple 私有介面；並非通用惡意程式防禦保證，仍只使用合成資料。

CLI/TUI 基準保持不變；新介面的結果不能回頭修改既有基準紀錄。Mac 人工驗收後才處理 Windows。

兩種入口與共用本機 backend 的 [Archify 隔離架構圖](../diagrams/extensions-isolated.html)／[receipt](../diagrams/extensions-isolated.receipt.json) 用於理解流程，不能代替各介面 E2E 證據。

隔離驗證的 runtime 限制：OpenCode 1.19.5 曾嘗試背景 npm dependency install，被網路規則阻擋並記 warning；目前已實測的工具鏈仍可完成。這不代表有雲端模型推論。API server 不設定 password，只綁 loopback，測試後停止該次 PID；不提供遠端存取。

本機 zsh 的 here-doc 使用 TMPPREFIX（預設 /tmp/zsh）。helper 將 TMPDIR/TMP/TEMP 與 TMPPREFIX 一起綁到本次已允許的 tmp；launch 會在尚未使用的 prepared run 更新 runtime 環境，舊已執行案例的證據不修改。

本輪正常三次的要求 JSON，官方 TUI 與 OpenChamber 皆為 2/3 符合，仍有錯誤分組與額外敘述。側欄 corrupt 曾遇 GUI 定位失敗，解鎖後已在同一 session 補看最後繁中錯誤報告及 Python 工具，未重送需求；詳見驗證紀錄。此環境只支持有限合成資料 POC，不能把目前生成程式直接當作可重用分析器。

## 2026-11-10：未成立的修正候選

[修正候選驗證](repair-verification.md)／[E005](../../../experiments/E005/README.md) 已保留兩個 fresh MVP 的失敗。新增的通用探索／回答規則只透過 `prepare --evidence-workflow` opt-in，沒有預寫分析器；目前**不採為預設、不建議當作已通過方案**。未加旗標的原 IDE 準備與 CLI/TUI 基準不變。兩版嘗試上限後沒有啟動正式十例；下一輪需先處理 E005 的待決策投入範圍，不能以重試或單元測試宣稱達標。

## E006 短式流程：未成立的實驗選項

2026-11-10 使用者追加 30 分鐘，只測一版正常／missing／corrupt fresh MVP。結果見 [短式批次](short-verification.md)；兩例送出、corrupt 未執行，不進正式重驗。原教學預設與 E005 `--evidence-workflow` 不變。只有另獲後續實驗授權時，才用下列 opt-in 準備全新 workspace：

```sh
uv run --locked python ide.py prepare --short-workflow --interface chamber \
  --case sales --runs-root /private/tmp/local-excel-extensions/runs \
  --opencode /private/tmp/local-excel-poc/opencode/node_modules/.bin/opencode
```

missing/corrupt 分別用新 prepare，不續接 session，不複製舊生成程式。短流程不要求 inspection.json，仍須自主寫 check_excel.py 探索欄名／型別，成功後自主寫 analysis.py，實際執行並只引用輸出。失敗需原始例外與精確指定路徑；不得改查父目錄或其他 session。

本輪遇系統可用記憶體約 6%、本機 API／GUI 逾時，須列環境干擾；請勿為改善效能減少 65536 context、換模型或取消隔離。正常 Python 錯誤、missing 搜尋錯路徑仍屬具體失敗證據。安裝、啟動、36 項測試或沒有 answer.json 都不能替代 GUI 最後正確回答的驗收。

## 單一測試視窗的可觀察基線

[E007](baseline-verification.md) 保留六個舊 POC 視窗關閉後的一次一 server／視窗結果。先確認 server 真正 listen、三組 health/session GET 成功及側欄草稿，再送需求；啟動時 connection refused 與後續成功要分開保留。不要關閉其他使用者程式、重啟全域 Ollama，或以 free 百分比／API 快判定推論與分析通過。每例結束先收證、停止並核對自己的 backend，再關閉該測試視窗；不要預暖下一案例。

## E008：已授權指令對齊 opt-in

使用者已同意僅改agent.excel.prompt，另記新config hash；模型、context、sampler／權限／隔離不變。`ide.py prepare --aligned-workflow --interface chamber ...` 與其他實驗旗標互斥；原預設保留。不要將此選項視為通過：[E008](aligned-verification.md) 正常只探索就結束，負面尚未送出。GUI不可得時保存零session／停止receipt，不用CLI／HTTP代送，不追加「請繼續」修補正常。恢復後先核對原期限與branch／PR，重新prepare尚未送出的fresh案例；保留被中止setup，不重跑失敗正常。
