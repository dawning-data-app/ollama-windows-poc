# 跨機展示交接

最新簡報為 [ollama-cross-machine-demo-v4.pptx](ollama-cross-machine-demo-v4.pptx)，共三頁，保留可編輯文字與流程圖；兩端證據以圖片呈現。v3 保留為原始版本。

## 已取得的證據

- Mac：`mac-cli-output-capture.png` 是 2026-10-08 14:39 CST 真實 CLI 輸出呈現，回覆節錄，非 macOS Terminal 視窗直拍。圖中記錄 `GENERATED HTTP 200`、非空回覆與 exit code 0；歷史跨機紀錄見 [verification.md](../docs/verification.md)。
- Windows：`windows-cli-output-capture.png` 是 2026-10-08 15:04:57 +08:00 原生 PowerShell 真實輸出節錄，非視窗直拍。執行日期、`hostname`、私網 IPv4 查詢、`ollama list` 與本機 `http://127.0.0.1:11434/api/tags` 已取得；模型清單與 API 均包含 `tinyllama:latest`。
- 主機對應：由使用者確認 Mac 目標與此 Windows 主機相同；本次未直接讀取 Mac 的 `.env`。
- 圖片已永久遮蔽主機名稱與私人 IP，同一 Windows 位址統一標示為 `<WINDOWS_IP>`。原始輸出只存於私有暫存區，未加入 repo 或 PPTX。

## 驗證與 human review

已渲染並逐頁檢查三頁的文字、比例與可讀性。PPTX 結構、版面與重新匯入驗證通過；另檢查文字、備註、中繼資料與內嵌媒體，未發現原始私人 IP 或主機名稱、憑證或完整日誌。內嵌媒體只有原始 Mac 圖與遮蔽後 Windows 圖，Mac 圖的位元組保持一致。

依使用者確認，Mac 圖所記錄的操作直接呼叫此 Windows Ollama，屬於已完成的跨機實際操作。客戶展示前建議再排練一次；這是展示準備建議，不代表缺少跨機實跑證據。Windows 原生 `.\scripts\windows-local.ps1 -Action All` 的 human check 也仍待完成，與此次展示證據分開記錄。

1. 用 PowerPoint 開啟 v4，確認三頁顯示正常、文字可編輯、兩張證據圖可讀。
2. 由 Mac 操作者核對目標後執行 `python3 -B client.py --timeout 120`，確認 `GENERATED HTTP 200`、非空回覆及 exit code 0。
3. 再次排練並確認現場環境後再決定客戶展示；若需視窗直拍，由操作者另行擷取並永久遮蔽敏感資訊。
