# 短式流程 MVP：2026-11-10 E006

**Mac 完整驗收未達成，不進正式重驗。** 使用者授權的額外 30 分鐘已用完；一個短提示候選，正常與 missing 各真正從側欄送出一次，corrupt 未能送出。沒有重試或更換樣本。完整判準／run／session／實際錯誤／時間戳在 [E006](../../../experiments/E006/README.md)。

| 案例 | 可得證據 | 尚缺或失敗 |
|---|---|---|
| 正常 | 自主寫探索 Python，四次真實 uv 執行；GUI 見首個錯誤 | generator 索引、漏 import、datetime JSON／型別錯用；600 秒內沒有成功探索、分析與最後回答。月份鍵、金額、區域、排名與敘述無可驗結果。 |
| missing | 真實指定資料夾檢查及 exit 1，沒有 answer.json | 錯誤字串是 OSError 類別本身；接著查父目錄與 /private/tmp。沒有取得其他資料，但未遵守精確路徑及停止契約；最後回答未完成。 |
| corrupt | server／視窗準備，session count=0，deadline 後埠關閉 | GUI 逾時／reset，未送出，**未執行**。不能沿用舊 corrupt 通過結果。 |

本輪 `--short-workflow` 僅 opt-in，原 IDE 預設、CLI/TUI、E005 長流程都保留。shortflow.py 只有通用需求文字與 evaluator，沒有預寫分析器；不放入代理工作區。短流程減去 inspection.json 格式負擔，仍要求代理自行探索／計算並引用實際 stdout。核對器不是完整安全證明或 E2E 自動通過器，仍須人審 source／GUI／所有額外敘述。

三例 protected-input／policy hashes 相符；兩個已送出案例的主輔本機模型、固定 digest／65536、config、uv Python 均核對，沒有附檔／選取內容。兩次收證 errors 只有未完成／分析／回答缺失，不能據此補為成功。原始 oracle 僅 evaluator 使用。受測代理未取得舊答案、預寫分析器或 oracle；隔離未放寬。

執行中可用記憶體約 6%，API 與 GUI 逾時；停止後 25%。有環境干擾，不能把本輪歸因成單一模型／提示瓶頸；也不能因此忽略已實際觀察的 Python 和路徑違規。先前 E005 同 sandbox/uv 的 evaluator 讀檔 probe 成功，只排除該固定檔案缺套件／讀權限，沒有代替代理成功。

36/36 POC 測試通過，無改動或重跑舊 tinyllama 測試。三個受測 server 均停止；全域 Ollama 保留。持久證據為 `/Users/andrew/.codex/artifacts/local-excel-short-20261110`，歷史交付原樣保留。

沿用凍結的 [Archify 架構圖](../diagrams/extensions-isolated.html)／[receipt](../diagrams/extensions-isolated.receipt.json)，本輪再驗 showcase 9/9、errors=0、warnings=0；spec/HTML hashes 不變，視覺檢視沿用原紀錄，未聲稱新目視。繁中內容的固定 Viewer UI／html lang 回退英文。Graphify 沒有可用既有圖，不建圖。PR Lens 為 e93deec 到本輪最終 HEAD 的 bounded diff，在 repo 外 validate/render，不是整支 PR 的圖或驗收證據。

正式官方三正常＋missing/corrupt、側欄三正常＋missing/corrupt 全部**未執行**；不能把本輪 MVP 算入正式三次。下一個待決策為受控環境基線實驗或保留 needs-rework；未自動加時、升級 OpenCode、改模型、放寬隔離或自製 extension。Draft PR 交 human review，不合併；Windows 未開始。
