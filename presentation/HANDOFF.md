# Windows Agent 接續事項

目前簡報為三頁可編輯 PPTX。第 2 頁的 Windows 畫面是刻意保留的空位；`mac-cli-output-capture.png` 是 2026-10-08 14:39 CST 真實 CLI 執行輸出的截圖呈現，回覆只顯示節錄，並非 macOS Terminal 視窗直拍。補齊 Windows 畫面並核對主機對應前，不要當作已完成的客戶展示證據。

1. 在 Windows 原生 PowerShell 取得真實畫面：`hostname`、`ollama list`、`Invoke-RestMethod -Uri http://127.0.0.1:11434/api/tags`。確認模型清單有 `tinyllama:latest`。
2. 核對 Mac 的未追蹤 `.env` 目標確實是這台 Windows 的私網位址。Mac 圖已呈現 `python3 -B client.py --timeout 120`、`GENERATED HTTP 200`、非空回覆節錄與 exit code 0；若客戶需要 macOS Terminal 視窗直拍，再由 Mac 操作者補拍。歷史跨機紀錄見 `docs/verification.md`。
3. 在圖片**副本**中永久遮蔽私人 IP、憑證及其他敏感資訊；兩端的同一 Windows 位址統一標為 `<WINDOWS_IP>`。只將遮蔽後的圖片放入 PPTX，不能用投影片圖形覆蓋原圖。
4. 替換第 2 頁的證據區，保留真實日期；檢查投影片可讀性，以及 PPTX 內嵌媒體、備註、文字和中繼資料沒有原始敏感資訊。再排練一次現場跨機呼叫。

Windows 原生 `.\scripts\windows-local.ps1 -Action All` 的 human check 仍待完成，與本次跨機展示分開記錄。
