# Mac 修正候選驗證：2026-11-10

**Mac 完整驗收目標未達成。** 本輪兩版 MVP 均未成立，已達事前的兩版嘗試上限；不是 210 分鐘總時間耗盡。新正式十例未執行，不能宣稱修正後三輪穩定重現。

## 狀態與範圍

續作前唯讀核對 feature worktree／branch／Draft PR head 均為 b121801，feature／dev clean。只在 feature 實作。沿用 OpenCode 1.19.5、官方 extension 1.0.0、OpenChamber 1.24.2、Qwen 固定 digest／65536、原 config／資料／uv.lock／oracle／E004 隔離；沒有升級或改模型契約。

[原始結果](extension-verification.md) 保留；[E005](../../../experiments/E005/README.md) 記錄原因、事前判準、投入上限與結果。新證據只在 evaluator 的 `/private/tmp/local-excel-repair-20261110`，最終另存 `/Users/andrew/.codex/artifacts/local-excel-repair-20261110`，不提供受測模型。

## 原因及增量

| 類別 | 原始證據支持的原因 | 本輪候選 |
|---|---|---|
| 資料理解 | 兩介面都曾把 product 當 region，未先實讀欄名；日期型別錯判導致空月額。 | 代理先自主寫探索 Python，印欄名／型別與兩種分組集合，再依欄名自主寫分析。沒有提供分析器。 |
| 執行流程 | 已略過表頭又扣一筆；missing 改查 workspace；exit 0 隱藏錯誤。 | 要求精確指定路徑、實際例外、分組集合／合計／排名核對；綁定 prompt hash、驗證實際探索在分析之前。 |
| 回答依據 | JSON 正確後仍額外編造月額／幣別／推測原因。 | 最後繁中句＋實際 stdout JSON，拒絕額外敘述或與 answer.json 不同的結果。 |

新流程只在 `ide.py prepare --evidence-workflow` 明確 opt-in；未成立，不採為預設。原 CLI/TUI 的 `poc.py`、原 IDE 預設需求、原 model/config、isolation.py 及受保護資產未修改。核對器 `workflow.py` 只包含指令文字與 evaluator 邏輯，不放入 agent workspace，沒有替代理執行分析。

## 新批次結果

| 樣本 | run／session | 結果 |
|---|---|---|
| MVP v1 | 20261110T020733-33eeb2c8／ses_e3cc63ff1ffeDhX0CwvhOTs0VM | 真實側欄送出並看到 Python traceback；作者選 inspect.py 遮蔽 stdlib inspect，113.485 秒中止。流程命名缺陷，無完整分析。 |
| MVP v2 | 20261110T021411-e4d0a53d／ses_e3cc0c108fferWwDK4MQxoVk9J | 改 explore_excel.py 後仍有 SyntaxError、猜錯路徑、tuple/Cell API 錯用及空探索。600 秒門檻後 GUI 實際中止完成於 617.802 秒；無 inspection.json、analysis.py、answer.json 或完整最後回答。 |
| 官方正常 1／2／3 | 未建立 | **未執行**：MVP 前提未成立。 |
| 官方 missing／corrupt | 未建立 | **未執行**，不能沿用舊案例當成本輪結果。 |
| 側欄正常 1／2／3 | 未建立 | **未執行**，MVP 不計入正式三輪。 |
| 側欄 missing／corrupt | 未建立 | **未執行**。 |

兩 MVP 的 raw user parts 只有原文字，與 prompt.txt 差一個尾端換行；無額外 file／synthetic context。主輔本機 stream、digest、恰好 65536、config 與 protected hashes 均相符。錯誤輸出與停止畫面在真實側欄核對；沒有完整分析回答，不標 E2E 通過。

## 核對與限制

- 31/31 POC 回歸通過；原 tinyllama CLI 測試沒有修改，也沒有在本輪重跑。
- evaluator 在代理停止後，以相同 sandbox／uv 成功讀出固定 fixture 的五欄及型別；不能把這個 evaluator probe 當成代理成功，也沒有交給模型。
- 既有 Archify 架構圖再驗 showcase 9/9，spec／HTML hash 與 receipt 相同，沿用原四張已目視截圖；本輪元件、路由與隔離沒有變。新通用流程與核對差異由 E005／PR Lens 描述。Graphify 無既有可用圖，未建圖／更新 skill。
- PR Lens 以本輪真實 b121801 到最終 HEAD 的 bounded diff 在 repo 外 validate/render；不是整支 PR 相對 main 的圖，也不代表正確性通過。
- 維持 Draft PR／human review／needs-rework，不合併；Windows 未開始。

下一個待決策是 E005 的 30 分鐘短式流程 MVP 建議。此次沒有自動增加第三版、擴大模型或權限。失敗只適用本輪長式提示及有限投入，不能宣稱所有 Qwen 或提示都不可行。
