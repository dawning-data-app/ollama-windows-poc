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
