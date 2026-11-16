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

2026-10-08 13:27 CST，Mac 以未追蹤的 `.env` 指向 Windows 私人網路端點，執行 `python3 -B client.py`。`GET /api/tags` 逾時，CLI 回報 `TRANSPORT_ERROR`、exit code 3；以 5 秒逾時重試 `/api/tags` 仍逾時。此結果**未證明 Mac → Windows 連通**。Windows 本機 API 的成功紀錄見下節；跨機監聽與防火牆設定仍需確認。

2026-10-08 13:35 CST，Windows 開放此 Mac 的連線後，Mac 再次執行：

```sh
python3 -B client.py --timeout 120
```

CLI 先收到 `/api/tags` 的模型清單，再由 `/api/generate` 收到 `GENERATED HTTP 200`，exit code 0；模型 `tinyllama:latest`，回覆為非空文字（開頭 `Hi!`）。**Mac → Windows Ollama 跨機 Request 已通過。**實際 Windows 位址僅存於未追蹤的 `.env`，未寫入本紀錄。

## Mac → Windows Qwen 內網 POC

2026-11-16（台北時間）。Windows 原生 Ollama `0.40.16`，本機模型 `qwen3.5:9b`，digest `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90`。`<WINDOWS_IP>` 與 `<MAC_IP>` 分別代表 Windows Wi-Fi 與指定 Mac 的內網 IPv4。

### Windows 本機與暫時開放

1. 結束既有 Ollama 應用程式與服務程序。在原生 Windows PowerShell 設定使用者與當前程序的 `OLLAMA_HOST` 為 `127.0.0.1:11434`，設定 `$env:OLLAMA_NO_CLOUD = '1'`，執行 `ollama serve`。用 `netstat -ano -p tcp` 確認 `11434` 只監聽 `127.0.0.1`。另開原生 PowerShell，將 `$env:OLLAMA_HOST` 設為同一回送位址，執行 `ollama pull qwen3.5:9b`，並對本機測試 `/api/tags` 和 `/api/chat`。模型清單含 Qwen，聊天回 HTTP 200 和「四十二」。
2. 確認兩台裝置的內網 IPv4 在測試期間維持固定。以系統管理員 PowerShell 用 `Get-NetConnectionProfile -InterfaceAlias 'Wi-Fi'` 與 `Get-NetFirewallProfile -PolicyStore ActiveStore` 核對生效的設定檔和預設入站封鎖。用 `Get-NetFirewallRule -PolicyStore ActiveStore -Direction Inbound -Enabled True` 搭配埠、程式、位址與介面篩選器，檢查可能放行 Ollama 或 TCP `11434` 的規則，包含適用所有 TCP 埠的規則。本次 Wi-Fi 使用 `Public` 設定檔，既有 Ollama 放行規則限定另一個目的 IPv4。若有較寬規則會涵蓋本次端點，先記錄並暫停。無法限縮來源時，維持本機綁定。
3. 在管理員 PowerShell 新增下列臨時規則，並確認規則已出現在 `ActiveStore`，來源只有 `<MAC_IP>`。命令中的 `Public` 是本次實測的設定檔。

   ```powershell
   $rule = 'Ollama-Qwen-LAN-POC'
   $ollama = (Get-Command ollama.exe).Source
   New-NetFirewallRule -PolicyStore PersistentStore -Name $rule -DisplayName $rule `
     -Direction Inbound -Action Allow -Profile Public -InterfaceAlias 'Wi-Fi' `
     -Program $ollama -Protocol TCP -LocalPort 11434 `
     -LocalAddress '<WINDOWS_IP>' -RemoteAddress '<MAC_IP>' -EdgeTraversalPolicy Block
   ```

4. 停止本機 `ollama serve`，僅在啟動終端改設 `$env:OLLAMA_HOST = '<WINDOWS_IP>:11434'`，保留使用者層的回送位址與程序的 `OLLAMA_NO_CLOUD=1`。再次執行 `ollama serve`，確認 `11434` 只監聽該 Wi-Fi IPv4，讓指定 Mac 開始測試。

### Mac 驗收

在指定 Mac 的終端執行以下命令。`-N` 關閉 curl 的輸出緩衝，可直接觀察串流片段。

```sh
base='http://<WINDOWS_IP>:11434'
curl --noproxy '*' -fsS --connect-timeout 5 -w '\nHTTP %{http_code}\n' "$base/api/tags"
curl --noproxy '*' -fsS --connect-timeout 5 --max-time 120 -w '\nHTTP %{http_code}\n' \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen3.5:9b","messages":[{"role":"user","content":"What is 12 + 30? Reply only with the number."}],"think":false,"stream":false}' \
  "$base/api/chat"
curl --noproxy '*' -fsSN --connect-timeout 5 --max-time 120 -w '\nHTTP %{http_code}\n' \
  -H 'Content-Type: application/json' \
  -d '{"model":"qwen3.5:9b","messages":[{"role":"user","content":"List the numbers 1 through 12 separated by spaces."}],"think":false,"stream":true}' \
  "$base/api/chat"
```

| 時間 | 請求 | 實測結果 |
| --- | --- | --- |
| 11:53:19 | `GET /api/tags` | HTTP 200，模型清單包含 `qwen3.5:9b` |
| 11:53:26 | 非串流 `POST /api/chat` | HTTP 200，`model=qwen3.5:9b`，回覆 `42`，`done=true` |
| 11:53:32 | 串流 `POST /api/chat` | HTTP 200，生成期間收到 15 段非空 NDJSON 文字，合併為 `1 2 3 4 5 6 7 8 9 10 11 12`，最後收到 `done=true` |

**指定 Mac 的內網推論與串流驗收通過。** 測試期間只有一台 Mac，沒有第二台裝置可驗證未放行來源的阻擋結果。

### 還原與重測

1. 停止此次 LAN 監聽的 `ollama serve`。在管理員 PowerShell 執行 `Remove-NetFirewallRule -PolicyStore PersistentStore -Name 'Ollama-Qwen-LAN-POC'`，確認同名規則已從 `ActiveStore` 與 `PersistentStore` 移除。如曾暫停既有規則，依紀錄恢復。
2. 將啟動程序的 `OLLAMA_HOST` 恢復為 `127.0.0.1:11434`，保留 `OLLAMA_NO_CLOUD=1`，重新執行 `ollama serve`。實測只剩回送位址監聽，本機 Qwen 再測 HTTP 200 並回覆「四十二」。
3. 從剛才獲准的 Mac 重跑上述三條命令。三筆均在約 5 秒後連線逾時，curl 回傳 `28` 並顯示 `HTTP 000`，表示未收到 HTTP 回應。已確認還原後原獲准的 Mac 無法連上內網端點。

## Human check

repo 已由使用者移至 GitHub Public。後續推送前，檢查跨機實測結果、重現步驟及 Git diff，確認沒有 Windows 的實際私人 IP 或其他私密資料。

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
- 該次 Windows 本機驗證未變更程式碼、持久環境變數或防火牆規則；後續跨機結果見上節。

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
