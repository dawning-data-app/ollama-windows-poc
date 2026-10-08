# 驗證紀錄

請記錄日期、Ollama 版本、模型、命令範本、分類、HTTP 狀態及簡短回應或錯誤。將實際私人 IP 改成 `<WINDOWS_IP>`，並移除敏感提示與完整日誌。

## Mac 本機

2026-10-08 11:32 CST；Ollama `0.31.1`，模型 `tinyllama:latest`。

```sh
python3 client.py
```

結果：`GENERATED HTTP 200`，取得非空文字回應（開頭為 `Hi!`）。Mac 本機 API 請求成功。

離線測試：`python3 -m unittest discover -s tests -v`，7 個測試通過。

## Mac → Windows

待 Windows 主機安裝與網路設定完成後執行。尚未證明跨機連通。

## Human check

檢查 Windows 實測結果、重現步驟及預計公開的 Git diff，之後才發布 GitHub Public repo。

## Windows 本機自身驗證

日期：2026-10-08。Checkout：`main`，commit `86f515b7f90712dcb434a8eccd88238d87cf99ae`。

- Ollama `0.40.0`；官方安裝檔 SHA-256 與 winget manifest 一致，Authenticode 簽章有效。
- 模型：`tinyllama:latest`，大小 637700138 bytes，digest `2644915ede352ea7bdfaff0bfac0be74c719d5d5202acb63a6fb095b52f394a4`。
- Python `3.12.3`（WSL）；`python3 -m unittest discover -s tests -v`：7 個測試通過。
- `python3 client.py --help` 與 `python3 -m compileall -q client.py tests`：通過。
- Windows 本機 `GET /api/tags`：HTTP 200，包含目標模型。
- Windows 本機 `POST /api/generate`：HTTP 200；`model=tinyllama:latest`、`prompt=Reply with one short greeting.`、`stream=false`。收到非空回覆 `Hi there!`，`done=true`。
- 安裝前 WSL CLI `python3 client.py --timeout 5`：`TRANSPORT_ERROR`，exit code 3，不能視為連通。
- WSL 為 NAT 模式；Windows 本機 API 推論成功不代表 WSL CLI 或 Mac 跨機連通成功。WSL CLI 直連驗證需另行允許暫時監聽 WSL 虛擬網路介面。
- 未變更程式碼、持久環境變數或防火牆規則。Mac → Windows 仍待 human check 與網路設定。

### Windows 本機 Human check

在 PowerShell 執行（若目前終端尚未取得新的 PATH，可使用下列絕對路徑）：

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" --version
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" list
Invoke-RestMethod -Uri http://127.0.0.1:11434/api/tags
$body = @{ model = 'tinyllama:latest'; prompt = 'Reply with one short greeting.'; stream = $false } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:11434/api/generate -ContentType 'application/json' -Body $body -TimeoutSec 180
```

預期：模型清單包含 `tinyllama:latest`，生成結果的 `response` 為非空文字且 `done=true`；實際文字可能不同。這些步驟僅驗證 Windows 本機 API。
