# VS Code extension 入口（Mac）

沿用 [CLI/TUI 教程](../README.md) 的 OpenCode 1.19.5、Qwen 9b 固定 digest／65536 context、合成 Excel、uv.lock 與獨立 oracle。本頁增加兩種介面；[驗證紀錄](extension-verification.md) 才是各案例的實際結果。安裝或啟動成功不表示 E2E 通過。

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

在本次環境，使用者另行授權將 `/private/tmp/local-excel-extensions/runs` 加入 VS Code 信任。其他機器若跳出信任提示，由操作者只信任本次合成測試目錄；不關閉 workspace trust。獨立 user-data 程序曾無法由 GUI 控制定位，本輪採同一 VS Code 程序內的專用 profile；這不等於 OS 程序／檔案系統沙箱。

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

在 OpenChamber 側邊欄確認本次資料夾、`excel` agent 與本機 9b，從該輸入區送出完整需求。不得用 helper 的 HTTP prompt API 或 CLI run 代替 GUI 送出。實際相容性與工具／最終回答呈現以驗證紀錄為準。每次測完只關閉本次視窗／server，不能終止使用者其他程序。

## 各介面的證據與驗收

正常案例各做三次 `prepare`；missing／corrupt 各一次，使用 `--case missing`／`--case corrupt`。每個案例最多 900 秒，記錄失敗或未完整完成，不挑選成功案例替換失敗。`--probe` 的環境探測不能算正常分析案例。

```sh
uv run --locked python ide.py capture "$Run" # 列出該次 session
uv run --locked python ide.py capture "$Run" --session-id <實際ID>
```

capture 保存原始 session JSON、所有 user parts（含檔案與 synthetic context）、推論日誌及 loaded model。自動核對完整回覆、真實成功 Python 工具、數值／排名、protected hashes、主／輔模型身份與 65536 context；仍是 `needs-human-review`，不自動宣稱 E2E 通過。

執行者另外看實際 GUI 的工具與最後繁中回覆，逐份讀生成程式確認真的計算 XLSX，檢查額外上下文是否含未授權資料、主輔推論與有效 endpoint。錯誤案例需讀敘述是否清楚且無編造數字。原始證據留 repo 外，repo 只存可公開摘要。Python 工具不受 OS 沙箱隔離，僅用合成資料。

CLI/TUI 基準保持不變；新介面的結果不能回頭修改既有基準紀錄。Mac 人工驗收後才處理 Windows。

兩種入口與共用本機 backend 的 [Archify 架構圖](../diagrams/extensions.html)／[receipt](../diagrams/extensions.receipt.json) 用於理解流程，不能代替各介面 E2E 證據。
