# E007：單一測試視窗基線

**三例均已真正從側欄送出並收證，原定 Mac 完整驗收仍未通過。** [完整實驗紀錄](../../../experiments/E007/README.md) 保留事前判準、UUID／session、工具／時間與失敗，不替換 E006 樣本。

| case | 結果 |
|---|---|
| 正常 | 367.304 秒。自主實讀欄名／型別、實算數字／月份／region／排名順序及最後回答正確；名稱陣列型別因短提示漏列而不符原契約，stdout 有額外文字。第一次 /answer.json 寫入被隔離拒絕，代理自行修正。 |
| missing | 515.194 秒。擴大搜尋、兩次 print_json NameError，第20 assistant step 結束而無最後文字；無 answer.json。不能追加追問或只拿最後 edit 宣稱成功。 |
| corrupt | 556.506 秒。真實 BadZipFile 與 GUI 最後繁中錯誤路徑／類型／訊息正確，無 answer.json；探索失敗後仍繼續寫／執行分析，最後格式不符。 |

六個舊 POC 視窗已關閉，其他工作視窗保留。ready 後 API GET 低於 30 ms，GUI 沒有本輪定位失敗；仍有 free 7–10%、高 swap 的資源干擾，不能只看 GET 延遲排除推論負擔。corrupt 的 server 啟動競態造成首批 connection refused，原紀錄保留。

三例固定 hashes／同一模型 digest／65536／主輔本機路由／cwd／uv 均核對；user parts 僅文字，無額外附檔／選取。三個 server 均已停止，未停止全域 Ollama。持久證據 `/Users/andrew/.codex/artifacts/local-excel-baseline-20261110`。原 CLI/TUI／隔離及受保護資產保留；36項 POC 是 E006 既有結果，本輪文件變更未重跑。

使用者已同意只修 opt-in system 指令及輸出型別／路徑，再做最多40分鐘三例 MVP；這是另個批次，沒有套用或重判 E007。原指令的順序／停止語意有張力，但尚未證明是因果。原正式十例／Windows 未執行，PR 維持 Draft／needs-rework／human review，不合併。
