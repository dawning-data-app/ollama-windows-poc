# 待決策：同一固定 Qwen 的 thinking 路徑最小驗證

這是未採用／未執行的提案，不更改本輪 excel-aligned-v1。E008 正常91.871秒、3steps後自行停在計畫；missing補驗已實得原始FileNotFoundError後仍擴查父目錄／變更路徑，不能單靠GUI恢復或指令對齊宣稱修正。corrupt仍依本輪原計畫完成，結果另列。

## 文件與本機證據

- [Qwen3.5-9B官方model card](https://huggingface.co/Qwen/Qwen3.5-9B) 分別列thinking與non-thinking模式的採樣建議，其中精確coding的thinking建議包含temperature0.6。這不保證本情境成功，也不能把目前none搭配0.6直接判成唯一根因。
- [Ollama thinking](https://docs.ollama.com/capabilities/thinking) 與 [OpenAI-compatible控制](https://docs.ollama.com/api/openai-compatibility) 說明thinking需由API控制；目前文件的boolean模型相容effort以none關閉、已識別effort啟用。文件可能新於本機0.31.1，不能直接冒充固定版實測。
- 本機同一tag的唯讀 /api/show 有capability thinking，但沒有thinking metadata物件；原參數／digest不改。本輪只查metadata，沒有啟用thinking。固定OpenCode1.19.5／SDK是否把選項傳入、reasoning/tool replay是否相容，仍需驗證。

## 可審查的唯一設定變因

以已批准的aligned config為基礎，只把

`/provider/ollama/models/qwen3.5:9b/options/reasoningEffort`

由`none`改為`medium`（OpenAI-compatible相容值候選，不把它稱為本機已驗證的具名level）。另記protocol與config hash；原default、E008與所有失敗保留。Qwen digest、65536 context、sampler、steps20、output8192、主輔同模型本機路由、system/user指令、Excel／uv.lock／oracle／E004權限與隔離全不改。不升級backend、不改外部SDK、不自製extension、不提供分析器或舊答案。

## 有限投入與停止

若使用者採用：先最多10分鐘／單一候選的工具鏈MVP，不先做正式Excel；確認同一OpenCode實際產生非空reasoning訊號並完成無害Python工具及最後答案、主輔只走本機、context/hash/隔離一致。僅讀reasoning的存在與長度作證，不把內容作答案。無法證實或需升級／改SDK／加權限就停止，交回決策。

工具鏈成立後才在同一批准配置做正常／missing／corrupt各一個fresh GUI MVP，每例600秒、最多40分鐘含setup；總投入最多50分鐘，單一配置不重試，不把舊正常替換成通過。output8192仍可能使thinking截斷；遇到長度上限需標明此限制，不能據此宣稱所有thinking不可行，也不自動放大output。完整三例仍未成立就不進正式十例。

這會改變推理模式契約、增加時間／token成本，故依使用者原限制先決策。替代選擇為保留目前needs-rework／human review，不啟動新推論。三例即使成立也只是進正式重驗的證據，不等於原Mac驗收完成。
