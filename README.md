# Ollama Windows Request POC

先在 Mac 本機確認可以送出 request 並取得 Ollama API 回應，再由 Mac 對私人網路上的 Windows Ollama 發送相同請求。CLI 只使用 Python 標準函式庫。

## 驗收

- `GENERATED`：收到非空的模型回覆，請求成功。
- `OLLAMA_API_ERROR`：收到 Ollama 的 JSON `error` 與 HTTP 狀態碼，證明請求到達 Ollama，但生成失敗。
- `TRANSPORT_ERROR`、`INVALID_RESPONSE`：連線、逾時或非 Ollama 回應，**不算**跨機連通。

## Windows 本機快速開始

Windows 從 Git / clone、安裝、測試到本機推論，請依 [Windows 本機教程](docs/windows-local-guide.md)。取得 repo 後執行：

~~~powershell
.\scripts\windows-local.ps1 -Action All
$LASTEXITCODE
~~~

Setup 會安裝缺少的軟體並下載模型；已有安裝沿用。All 依序執行建置、測試與推論，任何階段失敗立即停止。也可用 `-Action Setup`、`Test`、`Verify` 分階段執行。腳本固定驗證 Windows 本機，會覆蓋 `.env` 的遠端端點。

## 1. Mac 本機

安裝並啟動 [Ollama for macOS](https://ollama.com/download/mac)；已安裝者直接啟動應用程式。接著在 Terminal 執行：

```sh
ollama pull tinyllama:latest
python3 client.py --base-url http://127.0.0.1:11434
```

尚未建立 `.env` 時，預設端點是 `http://127.0.0.1:11434`。模型第一次載入可能較慢；必要時使用 `--timeout 180`。將實測結果填入 [驗證紀錄](docs/verification.md)。

## 2. Windows 主機

1. 依 [Windows 安裝文件](https://docs.ollama.com/windows) 安裝 Ollama，啟動後在 PowerShell 執行 `ollama pull tinyllama:latest`。
2. 在 Windows 本機確認服務與模型：

   ```powershell
   ollama list
   Invoke-RestMethod -Uri http://127.0.0.1:11434/api/tags
   ```

3. 在 PowerShell 設定使用者環境變數，然後從系統匣**完全結束** Ollama，再從開始功能表啟動，讓新設定生效。以 `ipconfig` 找出 Windows 在私人網路的 IPv4 位址。[Ollama 網路設定](https://docs.ollama.com/faq#how-can-i-expose-ollama-on-my-network)

   ```powershell
   [Environment]::SetEnvironmentVariable('OLLAMA_HOST', '0.0.0.0:11434', 'User')
   ipconfig
   ```

4. 先找出 Mac 的私人 IPv4 位址，再以**系統管理員 PowerShell** 在 Windows 防火牆新增輸入規則。把 `<MAC_IP>` 換成 Mac 的實際位址；此規則僅套用 Private 網路設定檔。

   ```powershell
   New-NetFirewallRule -DisplayName 'Ollama POC from Mac' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 11434 -RemoteAddress <MAC_IP> -Profile Private
   ```

   不要把此埠轉送到網際網路；[Ollama 本機 API 不要求驗證](https://docs.ollama.com/api/authentication)。
5. 在 Mac 的 repo 根目錄建立**不追蹤的** `.env`，填入 Windows 的實際私人 IP：

   ```sh
   OLLAMA_BASE_URL=http://<WINDOWS_IP>:11434
   ```

   然後執行：

   ```sh
   python3 client.py
   ```

記錄終端顯示的分類、HTTP 狀態與經遮蔽的回應到 [驗證紀錄](docs/verification.md)。若跨機連線失敗，先檢查 Windows 本機 `/api/tags`、`OLLAMA_HOST` 是否生效、兩台電腦是否互通，以及防火牆規則；不要把失敗寫成已驗證連通。

## CLI 與測試

```sh
python3 client.py --help
python3 -m unittest discover -s tests -v
```

可用 `--base-url` 暫時覆蓋 `.env`，或用 `--model`、`--prompt`、`--timeout` 修改測試。CLI 結束碼：`0` 為 `GENERATED`，`2` 為 `OLLAMA_API_ERROR`，`3` 為連線或回應格式錯誤。API 錯誤雖可證明 Ollama 有回應，仍以非零碼表示生成未成功。

公開 repo 只保留遮蔽過的驗證摘要；`.env` 已列入 `.gitignore`，不要提交原始日誌、私人 IP、帳密或 token。
