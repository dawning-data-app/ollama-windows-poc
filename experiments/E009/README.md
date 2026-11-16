# E009：同一固定 Qwen 的 thinking 工具鏈與條件式 Excel MVP

## 驗證什麼
設計時（2026-11-10）E009未占用。使用者已明確採用E008補驗內的thinking提案。主要問題：僅將已批准aligned模型選項reasoningEffort none改medium候選，固定版OpenCode1.19.5／Ollama0.31.1是否真正產生thinking、完成自主Python工具與最後回答；前提成立才測三例Excel。

## 為什麼
E008三例未成立：正常3steps只探索／計畫；missing真實錯誤後擴查；corrupt錯誤路徑／重跑與格式錯。Qwen官方model card區分模式採樣，Ollama文件記載reasoning_effort控制；本機capabilities有thinking但無thinking metadata，文件可能新於0.31.1，固定SDK傳遞與replay仍未知，不能由文檔宣稱可用或必然改善。來源與完整user決策見E008/followup-thinking-proposal.md及本輪外部thinking-decision.json。

## 成功與失敗判準
使用者批准先最多10分鐘工具鏈、成立後最多40分鐘三例、總50；本輪開始05:59:00 UTC，phase1截止06:09:00，overall截止06:49:00。單一候選excel-thinking-v1，僅相對aligned config的 /provider/ollama/models/qwen3.5:9b/options/reasoningEffort 改medium，不把它稱為本機已證實的具名level。模型digest、65536、sampler、output8192、steps20、指令、資料、權限／隔離不變；有效config及語義diff、hash核對。

phase1：真實側欄送出一個fresh無害runtime probe，代理自主寫／uv執行runtime_probe.py，真實sys.executable／sys.prefix在本次venv與marker，GUI工具／最後繁中JSON已見；export必須有非空reasoning parts作實際訊號，主輔本機／digest／context／hash相符。只有設定／安裝／build不成立。沒有足夠訊號、缺工具／final、環境不足為無法判定或按已見違規判失敗；需要升級SDK/backend或加權限就停止，不做Excel。

phase1全部成立才phase2：相同候選三種各一個fresh GUI，case最多600秒、phase2最多40分鐘且overall優先；正常真實自主探索／分析、原schema／數值／月份／region／排名與final全對；負面精確路徑真實原始例外、停止、不建answer。不得重試／替換舊失敗，不直接正式十例。遇output8192截斷如實標限制，不自動加output、不泛稱thinking不可行。越界取得內容／保護漂移停止依賴。

## 環境與前置條件
feature branch/worktree head5df9a5a clean，Draft PR open/unmerged；E008補驗backend停止／測試窗關閉。原Qwen digest／65536／sampler／synthetic Excel／uv.lock／oracle／E004隔離固定。原default／CLI/TUI／aligned及其他實驗保留。新模組只配置／指令／evaluator，不提供分析器、oracle或舊答案。phase1用無Excel的missing準備環境＋probe標記，明確不分析資料，不冒充missing受測案例。

## 重現步驟
新增互斥--thinking-probe／--thinking-workflow。先寫aligned baseline再只改reasoningEffort，保存原7dac…／aligned34b…／new hash，effective確認同agent指令與medium。probe要求自主寫Python印marker／sys.executable／sys.prefix，只回繁中句及相同JSON；不供應程式／分析器。真實OpenChamber送出，GET/export只收證。用raw reasoning存在與字元數，不把思考內容當答案。成功後另列phase2時間與三個fresh workspace，序列一server／視窗、不預暖，指令沿用aligned.prompt不改。root /private/tmp/local-excel-extensions/runs/thinking-20261110，外部證據/private/tmp/local-excel-thinking-20261110。

## 是否成功

工具鏈前提功能成功；Excel 候選未成立，Mac 完整驗收目標未達成。三種各一次新側欄樣本均保留，不重試、不挑成功樣本。官方 TUI 的本候選尚未重驗，正式兩介面十例／Windows **未執行**。

| case | fresh run／session | 實際結果 |
|---|---|---|
| probe | `20261110T060044-503ef6c6` / `ses_e3bf0f9fbffe2jzPxTHWbv4BqI` | 218.721秒；功能成功；實際thinking／uv Python／GUI最後繁中JSON，純JSON與原fence要求有差異；審查晚39秒明列，不算Excel樣本。 |
| sales | `20261110T061154-609816e1` / `ses_e3be87cfdffe7Db6M4fcQ3S0UU` | 600.715秒；失敗／限時未完成：錯將指定有空格路徑改成無空格，反覆FileNotFoundError與SyntaxError；未完成分析、無answer／最後回答。guard實停600.715秒。 |
| missing | `20261110T062501-4a373eda` / `ses_e3bda5f8fffemzifP5QoCzsZyC` | 582.333秒；失敗：精確目錄ls錯誤後仍擴查workspace／find及錯別路徑；自主check_excel.py實跑但自行raise中文訊息、exit0；13steps自行stop（非20step上限），最後僅reasoning、無文字／answer。 |
| corrupt | `20261110T063943-c5d85781` / `ses_e3bcf7367ffeyuCtiLYTzTjDzk` | 461.603秒；限時未完成／不通過：7steps／6tools；首跑NameError，修正後只列精確目錄／檔名並印directory_ok，後補開檔程式又有f-string SyntaxError，尚未真實開啟工作簿／BadZipFile。總截止實停461.603秒，無answer／最後回答；損毀檔案處理能力無法判定，已見Python流程失敗。 |

## 結果與證據

事前實驗窗口05:59–06:49 UTC（台北13:59–14:49），沒有自動加時；截止後僅收證、核對、文件及交付，不新增推論。probe 實際執行在06:08:19.627完成，早於10分鐘截止；人工／source／reviewer核對至06:09:39才完成，**證據審查晚39秒**。最初 reviewer誤把同一venv的python3別名及純JSON當失敗；只修 evaluator並加回歸，未重送probe／改模型輸入，Excel parser完全不放寬。以截止前完成的真實thinking／工具／回答確認功能前提後進三例；總截止不補回39秒。probe格式對原文要求的json fence有差異，功能成立不等於逐字格式完全符合。

probe有1段非空reasoning／127字元、實際自主runtime_probe.py與uv Python、本次venv interpreter／prefix及最後繁中JSON，GUI已見。medium只證實能在固定版觸發thinking，不稱為本機具名推理level。

相對aligned唯一config差異為`/provider/ollama/models/qwen3.5:9b/options/reasoningEffort` none→medium。原7dac6527…、aligned34b0dce9…與新`802cb27bee00a4a07a65d505a64617a314bd9f99f366cbbeb27b46199145da3b`均記manifest／effective／config-diff。各run的config／uv.lock／context-probe／prompt／工作簿（負面依本次fixture）hash、固定Qwen digest／恰好65536、主輔本機stream與cwd／uv receipt逐項核對，見audit；raw user都只有本輪文字、去尾空白相同，無選取／附檔上下文。不把reasoning內容作答案或回餵其他session。

46/46 POC回歸只支持helper／模式契約／原隔離；原tinyllama CLI／腳本／測試／簡報未改，舊測試未在本輪重跑。probe與Excel raw export、工具／生成source／final、GUI觀察、資源GET、manifest／hashes、guard停止receipt，另存 evaluator-only `/Users/andrew/.codex/artifacts/local-excel-thinking-20261110` 的ZIP／SHA。不複製auth、launch-env、依賴樹、state DB或oracle；舊archive不覆蓋。

## 結論與限制

正常樣本的根因證據屬**執行流程**：生成程式把「銷售 資料」改為無空格目錄，還有Python語法錯誤；實際正確路徑的工作簿存在且hash一致。沒有成功讀取後的分析／answer，不足以判定新候選的月份／region理解與排名能力，這些數值及最後所有額外敘述均未達驗收。不得把未算出答案說成數值通過。

負面樣本依各工具與最後回答判讀，錯路徑、擴查、實際例外與自行描述分開記；詳見逐例摘要與raw。原E008已見的停止不遵從，沒有因thinking工具鏈成立就被排除。原模型／資料／鎖檔漂移與額外引用污染未見證據；不能因此排除推論資源負擔或SDK語意問題。missing初始一段時間無工具，但Ollama仍解碼約15–16tokens/s、GET可用，當時free約8%、swap使用約22GB；不能單憑GET快或空白UI斷言沒在推論，也不能因相關性確證記憶體是唯一原因。

本輪是單一候選有限樣本，並非thinking與none的公平成效比較；output8192、steps20與有限硬體／時間保留。不延長生成上限、不自行改sampler／模型digest／context、升級OpenCode／Ollama或自製extension。原default／CLI/TUI、各舊失敗／GUI setup與九欄位契約保持。Archify復用凍結架構圖、showcase再驗9/9（0error／0warning），沿用原四種viewport視覺檢視、未新render；Graphify無既有可用圖、未建圖。PR Lens僅本次真實5df9a5a→交付head的bounded diff，外部本機validate/render，不是整支PR相對main或E2E通過證據。

下一個待決策：不採用thinking候選、不啟動正式十例，交human review／needs-rework。若仍要求完整自主分析可靠度，須先決定是否另評估模型／runtime契約及給定新的有限驗證範圍；現有證據不支持以重試或再加同樣流程宣稱修正成立。本輪沒有授權這些改動，不自行執行；維持Draft、不合併、不進Windows。
