# E004：隔離 runtime 的第二輪有限驗證

## 驗證什麼
- 日期 2026-11-05；使用者明確授權 E003 後另加一輪，15 分鐘、兩次修正。
- 沿用 E003 假設與成功／失敗判準，不改模型、資料、lock 或 oracle。

## 為什麼
- E003 部分檔案拒絕成立，完整工具鏈證據不足；最後 numeric IPv4 profile 因作者語法錯誤無法載入。
- 此輪以已可載入的 round-1 profile 為比較基準，查本機 Apple policy 後修復 runtime，不推論 sandbox-exec 必然可行。

## 成功與失敗判準
- 成功：同一 profile 能在 workspace 讀合成 XLSX／寫 canary，直接與 symlink 讀其他 session／真 oracle 均拒絕，ls/find 無法列出其他 session；本機 Ollama 可用，固定 digest／65536；OpenCode 真實呼叫 Python 工具並完整回覆。
- 失敗：禁止路徑讀取成功，或有限修正後有充分證據顯示必要操作不相容。
- 無法判定：必要工具鏈／推論證據仍缺。到 15 分鐘或兩次修正上限即停，不改判準。

## 環境與前置條件
- 同 E003 Mac、OpenCode 1.19.5、Ollama 0.31.1、uv Python 3.12.12 與固定 Qwen digest／65536。
- evaluator-only harness 不交給 LLM；oracle 只測拒絕，絕不讀回內容或複製入 workspace。

## 重現步驟
- 保留 E003 所有結果；此輪使用新 evidence 根目錄與同一無分析答案的 MVP workspace。
- 先查 Apple profiles，再測 OS/Python/loopback/backend；成功後才送無分析解法的環境探測。

## 是否成功
- 狀態：成功。
- 本輪任務完成：是；09:26 UTC 開始，約 09:29 完成核對，兩次修正內、未到 15 分鐘。
- 此為隔離最小工具鏈成功，不是官方／側欄的 GUI E2E 通過。

## 結果與證據
- [evidence](evidence/) 保留兩次 policy、runtime、ls/find、實際 backend JSONL、完整最終回覆、identity/hashes 與主輔 stream；launch-env 含 host 環境，未提交。
- 修正 1：以 E003 合法 round-1 加精確 MIME 檔，openpyxl 可讀 Sales、workspace 可寫；禁止路徑／symlink／父層 list 仍遭拒。localhost 僅回 ::1，但 127.0.0.1 可連 Ollama。
- 修正 2：依本機 Apple application.sb／AssetCacheLocatorService.sb，加入精確 DNSConfiguration、dnssd.service 與 mDNSResponder Unix endpoint；localhost 解析恢復 IPv4，原 config 的 localhost:11434 可用。未改 /etc/hosts 或模型 endpoint。
- ls／find session 父層都 exit 1、stdout 空白。相同 profile 的 OpenCode session `ses_e54f713f6ffedek1PpKQVr6K21` 實際跑 pwd、uv Python 印 interpreter／cwd、讀 benign context，71.747 秒後以 stop 完成繁中回覆，未分析 Excel。
- 主／輔 stream 皆 ollama/qwen3.5:9b。同 profile 內 API /ps 確認 digest `5eb3a683cbfed5baef1d1f24e2f54afd93e8a9ba344ca71eb8bb37129cf545fe`／context 65536；fixture、uv.lock、opencode.json hashes 與既有基準相同。
- 正式 isolation.py 對該 run 產生的 policy 與 MVP profile byte-equivalent。OS 回歸對真 oracle 僅唯讀開啟並核對前後 hash；寫入拒絕只用可丟棄 canary。舊 E003／CLI/TUI／正常三輪／missing 歷史不覆寫。

## 結論與限制
- 依使用者條件授權接入 ide.py launcher 與本機 server，兩者整個 OpenCode 及子程序皆套同一 policy；舊無 isolation manifest 的 run 仍拒絕啟動，無無隔離 fallback。
- 下一步分別重做每介面三輪 sales 與 missing/corrupt；OpenChamber 仍須先通過 E002 真實側欄最小驗證。
- 這是有限輸入的 Mac 實驗，sandbox-exec 已棄用，不外推 Windows 或全面惡意程序防禦。
