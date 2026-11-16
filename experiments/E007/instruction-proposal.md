# 待決策：只修訂 Excel 指令契約，不更換模型或推論參數

此文件只是提案，未修改或套用 runtime。E007 保持原 opencode.json／excel-short-v1，三個預定 fresh MVP 照原條件收證。

## 證據與原因區分

- 正常案例實讀五欄／型別，實際總額、月額、region 分組與排名順序正確；排名用了物件陣列。poc.py:prompt 原契約明訂 region_ranking 為區域名稱陣列，shortflow.py:prompt 卻漏列型別。這個 underspec 是作者缺口，不當作商品／區域理解錯誤。
- 主 agent 固定 system prompt 同時要求先寫 analysis.py、Do not stop after listing files；使用者短提示要求先寫 check_excel.py、目錄不存在就停止。存在順序／停止條件的語意張力；尚未以控制實驗證明因果。E007 missing 在 API 可回應下仍持續查父目錄／其他位置。
- 正常 stdout 違反已有的 only-JSON 要求，第一次把 answer 寫到 /answer.json 被 sandbox 拒絕，後來自行改相對路徑。這些是實際代理行為，不因提案而重新分類。

## 具體修改範圍

1. 原 opencode.json 的 agent.excel.prompt 改為以下文字；僅該 JSON 欄位改變，需新 config hash／protocol 記錄及同意，不能冒稱仍為原 config。主／輔模型、digest、65536、sampler、steps／output、provider、permissions、E004 sandbox 皆不改。

> You are a local Excel analysis agent. openpyxl is already installed in this workspace uv environment. Follow the user-provided target directory exactly. Autonomously write and execute a short runnable Python inspection first. On directory or workbook read errors, report the actual exception and exact failing path, then stop; do not search parent directories or other locations, create substitute inputs, or produce an analysis result. Only after successful inspection, autonomously write and execute analysis.py with bash: uv run --locked --offline python analysis.py. The python command also points to this session uv environment. Actually read and calculate workbook data. Do not install packages. Follow the requested answer format and reply in Traditional Chinese.

2. 下一版需求只補回既有輸出型別與 workspace 相對輸出路徑：total_sales 為數字、monthly_sales 為 YYYY-MM 到數字、regional_sales 為區域到數字、region_ranking 為區域名稱陣列；answer.json 位於本次 workspace，stdout 只輸出同一 JSON。不提供數值、分組值、迴圈、資料探索或分析程式。

3. 新版保持明確 opt-in，不覆寫原預設／E005／E006；新獨立實驗與 fresh session，正常／missing／corrupt 各一個，每例最多 600 秒、總計最多 40 分鐘（含 setup），單一候選、不重試。模型／鎖檔／資料／oracle／隔離保持，不能以成功樣本替換 E007。三例完成前不啟動正式十例，未通過就保留原始失敗與下一決策。

## 決策影響與限制

這是 system 指令／config 契約變更，先交使用者決策。它排除已知的指令歧義，不保證 Qwen 正確遵循，也不能解除 Mac 記憶體／swap 的資源限制。若維持原契約，不再藉更多相同樣本主張已修正；保留 Draft／needs-rework／human review。不得因此升級 OpenCode、改 thinking／model/context、放寬權限或自製 extension。
