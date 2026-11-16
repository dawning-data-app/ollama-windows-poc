# E009 thinking 限定 MVP：工具鏈成立，完整驗收未通過

使用者只批准reasoningEffort none→medium的一個候選：先10分鐘工具鏈、成立後最多40分鐘三例、總50。原模型／context／sampler／output／指令／權限／E004隔離均保留，原預設不變。功能前提與逐字格式差異、證據審查晚39秒的限制均明列於 [完整E009](../../../experiments/E009/README.md)，不冒稱嚴格全數通過。

| case | fresh run／session | 實際結果 |
|---|---|---|
| probe | `20261110T060044-503ef6c6` / `ses_e3bf0f9fbffe2jzPxTHWbv4BqI` | 218.721秒；功能成功；實際thinking／uv Python／GUI最後繁中JSON，純JSON與原fence要求有差異；審查晚39秒明列，不算Excel樣本。 |
| sales | `20261110T061154-609816e1` / `ses_e3be87cfdffe7Db6M4fcQ3S0UU` | 600.715秒；失敗／限時未完成：錯將指定有空格路徑改成無空格，反覆FileNotFoundError與SyntaxError；未完成分析、無answer／最後回答。guard實停600.715秒。 |
| missing | `20261110T062501-4a373eda` / `ses_e3bda5f8fffemzifP5QoCzsZyC` | 582.333秒；失敗：精確目錄ls錯誤後仍擴查workspace／find及錯別路徑；自主check_excel.py實跑但自行raise中文訊息、exit0；13steps自行stop（非20step上限），最後僅reasoning、無文字／answer。 |
| corrupt | `20261110T063943-c5d85781` / `ses_e3bcf7367ffeyuCtiLYTzTjDzk` | 461.603秒；限時未完成／不通過：7steps／6tools；首跑NameError，修正後只列精確目錄／檔名並印directory_ok，後補開檔程式又有f-string SyntaxError，尚未真實開啟工作簿／BadZipFile。總截止實停461.603秒，無answer／最後回答；損毀檔案處理能力無法判定，已見Python流程失敗。 |

本批是真正OpenChamber側欄各一次fresh送出；正常未完整完成，負面依raw判定，沒有補追問或重新抽樣。每例600秒、總06:49 UTC優先；guard輪詢的實際停止秒數另留receipt。官方TUI新版候選未重驗，正式十例／Windows未執行，原兩介面正常JSON各2/3及E005–E008失敗保留。安裝、啟動、thinking capability、46/46 helper測試或errors=[]均不代表Excel E2E。

新config hash `802cb27bee00a4a07a65d505a64617a314bd9f99f366cbbeb27b46199145da3b`，相對aligned34b0dce9…只改唯一模式欄位。實際本機主輔stream、Qwen digest／65536、hashes、原始文字上下文、工具／source／final與GUI觀察另存evaluator-only `local-excel-thinking-20261110`，不提供代理。各類根因、排除與未排除項、下一待決策見E009；本輪候選不採用，Draft交human review／needs-rework，不合併。
