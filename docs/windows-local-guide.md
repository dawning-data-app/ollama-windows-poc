# Windows 本機從建置到驗證

本教程供一般 Windows 使用者執行：取得專案、安裝必要軟體、下載模型、跑測試，再由原始 Python CLI 驗證本機推論。腳本明確指定本機端點，會覆蓋 `.env` 的遠端端點設定。Mac 與跨機連線請依 README 的既有流程處理。

## 前置條件與下載

- Windows 10 22H2 或 Windows 11；Windows PowerShell 5.1 或 PowerShell 7。
- 可連上 GitHub、winget 來源及 Ollama 模型 registry 的網路。
- winget（App Installer）。先執行 `winget --version`；缺少時由 Microsoft Store 安裝或更新 App Installer。
- Ollama 官方說明至少預留 4 GB 安裝空間，模型另外占用空間。本 POC 的 `tinyllama:latest` 此次約 638 MB；安裝檔及下載暫存也需要空間，建議至少預留 8 GB。模型與安裝程式的大小會隨版本改變。[官方 Windows 文件](https://docs.ollama.com/windows)

`Setup`／`All` 會接受 winget 套件及來源協議、安裝缺少的 Python／Ollama，並下載指定模型。已有 Python 3.12 以上、Ollama 與模型時沿用，不自動升級。腳本不建立 venv，也不安裝 pip 相依。下載可能需數分鐘以上，請依終端進度等待。

## 1. 取得 repo

在一般 PowerShell 執行。未安裝 Git 者先執行：

```powershell
winget install --id Git.Git --exact --source winget --no-upgrade
```

安裝後重新開啟 PowerShell，確認 `git --version`。以下範例使用 D 槽；沒有 D 槽者換成自己的目錄：

```powershell
New-Item -ItemType Directory -Path D:\code\python -Force | Out-Null
Set-Location D:\code\python
git clone https://github.com/dawning-data-app/ollama-windows-poc.git
Set-Location .\ollama-windows-poc
```

若目標已存在，先檢查 remote、branch 與 `git status`，不要再次 clone 到同一目錄或覆寫現有修改。腳本本身不 clone、pull、commit 或 push。

## 2. 一次執行全部階段

```powershell
.\scripts\windows-local.ps1 -Action All
$LASTEXITCODE
```

預期依序看到：
1. `SETUP_OK`：Python、Ollama API 與模型已準備好。
2. 既有 unittest 全部通過，CLI help 與語法編譯成功，最後顯示 `TEST_OK`。
3. `GENERATED HTTP 200: ...`，包含非空模型回覆；整個流程結束碼為 0。

任何階段失敗立即停止，後面階段不會執行。模型回答可能每次不同，不需要完全等於 `Hi there!`。

## 3. 分階段執行

```powershell
.\scripts\windows-local.ps1 -Action Setup
$LASTEXITCODE
.\scripts\windows-local.ps1 -Action Test
$LASTEXITCODE
.\scripts\windows-local.ps1 -Action Verify -Model tinyllama:latest -Timeout 180
$LASTEXITCODE
```

`Test` 與 `Verify` 不安裝軟體、下載模型或啟動 Ollama；需要時先執行 `Setup`。可先讀取說明：`Get-Help .\scripts\windows-local.ps1 -Detailed`。

從其他目錄執行也可；腳本依自身位置找到 repo，結束後恢復原本工作目錄：

```powershell
& 'D:\code\python\ollama-windows-poc\scripts\windows-local.ps1' -Action Test
```

`-Model` 預設 `tinyllama:latest`。更換模型時先用該模型執行 `Setup`，再 `Verify`；下載大小可能大幅增加。`-Timeout` 預設 180 秒、必須為有限正數，是 CLI 每個 HTTP 請求的逾時設定，不是安裝或模型下載的總時間限制。

## 4. 結果與 human check

| 階段／結果 | 結束碼 | 意義 |
| --- | --- | --- |
| Setup／Test 成功 | 0 | 該階段完成 |
| Setup／Test 或腳本執行錯誤 | 1 | 必要條件或命令失敗 |
| GENERATED | 0 | 非空回覆，本機推論成功 |
| OLLAMA_API_ERROR | 2 | Ollama 有回應，但生成失敗 |
| TRANSPORT_ERROR／INVALID_RESPONSE | 3 | 連線或回應格式錯誤，不算推論成功 |

`All` 保留第一個失敗階段的結束碼。只有原始 CLI 顯示 `GENERATED` 且結束碼 0，才能完成本教程的推論驗收。

Human check：
- 在一般 Windows 原生環境執行 `All`，確認上述三階段完成。
- 再次執行 `Setup`，確認已有軟體與模型沿用、不重新安裝。
- 從其他目錄、含空白的 repo 路徑執行 `Test`。
- 保留日期、Python／Ollama 版本、模型、執行階段與結束碼的遮蔽摘要。公開紀錄不放私人 IP、憑證、敏感提示或原始完整日誌。
- 本機成功只證明 Windows 本機流程，不代表 Mac 跨機連線成功。

## 故障排查

- **winget 缺少／安裝失敗**：更新 App Installer，查看 winget 的錯誤。可手動從 [Python](https://www.python.org/downloads/windows/)／[Ollama](https://ollama.com/download/windows) 官方網站安裝，再重跑。腳本每次安裝後會重新解析路徑，不依賴原終端 PATH 立即更新。[winget install 文件](https://learn.microsoft.com/en-us/windows/package-manager/winget/install)
- **Python 不符合版本**：需要 3.12 以上。腳本依序檢查 launcher、原生 PATH、Python registry 與預設使用者安裝目錄，忽略 WindowsApps 別名與專案 .venv。
- **PowerShell／Python 被政策阻擋**：依組織規則處理；不要關閉 WDAC、AppLocker 或變更執行政策以繞過限制。必要時請管理員提供核准的執行方式。
- **Ollama 未就緒**：腳本最多等待 60 秒。由開始功能表啟動 Ollama，檢查 `http://127.0.0.1:11434/api/tags`，並查看 `$env:LOCALAPPDATA\Ollama\server.log`。若同埠是其他服務，先確認衝突，不要任意結束不明程序。
- **模型下載失敗**：查看終端錯誤與可用磁碟空間，確認 registry 網路存取後重跑 Setup；不要把預先配置的模型檔大小當作下載完成。
- **生成逾時**：首次模型載入可能較慢，增加 `-Timeout` 並查看 Ollama 日誌。
- **連線目標**：固定本機 loopback。模型下載的 Ollama 子程序也固定 loopback；腳本不修改使用者、系統或父程序的 `OLLAMA_HOST`，不新增防火牆規則或 Windows service。啟動的 Ollama app 會保留運作供後續使用。
