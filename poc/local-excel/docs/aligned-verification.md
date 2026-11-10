# E008：已授權指令修訂，驗證未完成

**Mac 完整驗收仍未通過。** 新候選正常案例提前結束，missing／corrupt 因 GUI 不可得未送出。不是40分鐘耗盡；[完整 E008](../../../experiments/E008/README.md) 保存事前判準、原始時間／session／config差異與缺口。

| case | 結果 |
|---|---|
| 正常 | 真實側欄送出，探索 Python exit0，五欄／首筆型別正確；91.871秒、3個assistant step後只給後續計畫，未寫／執行分析、無 answer.json。GUI最後訊息已見，沒有補追問。 |
| missing | 已準備同一新 config 與受限 backend，GUI多次 cgWindowNotFound，重綁失敗；session count=0，未執行，已停止自己的server／guard。 |
| corrupt | 未準備／未送出，未執行；不挪用 E007 結果。 |

使用者已同意的新 `--aligned-workflow` 僅修改 session config 的 `/agent/excel/prompt`，將先探索／讀取失敗停止與分析順序對齊；補回原排名名稱陣列型別、workspace輸出位置並明訂錯誤JSON stdout。config hash 從 `7dac6527…` 變為 `34b0dce9…`；實際 JSON diff 只有該指令欄位，effective config亦核對。模型、65536、sampler、主輔本機路由、權限與隔離不變，原 baseline 與預設保持。

40/40 POC回歸只驗契約與 helper；舊 tinyllama／腳本／測試／簡報與 ReadOnly基準不改。正常主輔stream／固定身份／context／hashes相符、原始user只有本輪文字；missing只有setup資格，不代表受測代理路由／工具通過。raw／source／GUI／audit／tests／停止紀錄持久存於 `/Users/andrew/.codex/artifacts/local-excel-aligned-20261110`，不提供受測代理。

04:25:37 UTC 因 GUI 不可得清理未送出的 backend；原截止04:49:15 UTC不重置。使用者解鎖／顯示視窗的問題仍待回覆。視窗恢復且仍在原期限才續作尚未送出的兩例；若超時，新投入另決策。正常失敗保留，不以追問、重試或其他批次補成通過。正式十例／Windows未開始，Draft交human review，不合併。

## 後續更新：兩個負面首次受測已完成

[補驗](../../../experiments/E008/followup-20261110.md) 在使用者新續作授權下另列30分鐘，沒有重置舊40分鐘。missing 514.838秒：真實FileNotFoundError後仍擴查／變更路徑，最後自稱完成但缺JSON、類型非原class。corrupt 389.716秒：真實BadZipFile、卻回報資料夾而非失敗檔案、多次重跑，最後格式仍錯。GUI工具與兩個最後回答均已見、無answer.json；正常91.871秒失敗保留。兩例固定hash／config34b0dce9…／模型／65536／路由／隔離相符，server均停止。至此E008三例受測已補齊，候選失敗，不進正式十例／Windows。持久補驗證據 `local-excel-aligned-followup-20261110`，舊GUI斷點保留。使用者已另批准最多50分鐘thinking實驗（先10分鐘工具鏈、成立後40分鐘三例），尚未套入本輪。
