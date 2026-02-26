# Auto-Acceptance-Test 專案介紹 (README)

本專案提供基於 AI 代理程式（AI Agent）的自動化驗收測試解決方案。透過定義明確的測試案例（Markdown 格式），專案內的 AI 技能 `autoTestReport` 能夠自動開啟瀏覽器執行操作、擷取關鍵畫面，並最終生成視覺化的 HTML 測試報告。本文件旨在協助 PM (專案經理)、SA (系統分析師) 及 QA (品質保證工程師) 快速理解並導入本專案。

## [階段一] 任務目標與範圍
- **任務目標**：降低手動回歸測試與驗收測試的成本，讓非程式開發人員 (PM, SA) 也能透過撰寫簡單的 Markdown 規格文件，交由 AI 自動執行網頁測試並產出具備截圖佐證的測試報告。
- **專案結構 (PM/SA 專注區塊)**：
  本專案已將工程細節封裝。您只需要關注以下兩個資料夾：
  - 📁 **`Test/` (輸入區)**：請將您撰寫好的測試案例件 (Markdown 格式) 統一放在這裡。
  - 📁 **`reports/` (輸出區)**：AI 測試完畢後，產生的 HTML 測試報告會統一歸檔於此。
- **適用範圍**：
  - Web 網頁前端功能驗證（如：登入流程、表單填寫、頁面導覽、跳出視窗/燈箱檢查）。
  - 效能初步查核（如：頁面載入時間、API 回應等待過久處理）。
- **目標受眾**：PM（負責驗收功能是否符合需求）、SA（負責制訂測試規格與驗證標準）、QA（負責檢視最終報告與例外狀況）。

## [執行步驟] 詳細執行步驟
欲使用本專案進行自動化測試，請依循以下步驟操作：

1. **環境準備**
   - 確認已具備執行 AI Agent 的開發環境（如 Gemini / Antigravity 擴充套件已啟用）。
   - 確保專案目錄下有提供 `generate_report.py` 或打包好的執行檔，用以生成最終報告。

2. **撰寫測試案例 (由 PM/SA 執行)**
   - 參考標準範例格式（詳見 `SOP.md`），建立一份新的測試案例檔案（例如 `Test/FeatureX_Test.md`）。
   - 在檔案中明確標示 `[階段一]`、`[執行步驟]`、`[預期結果]` 三大區塊。
     - **階段一**：定義測試的 URL、測試帳密、主要目標。
     - **執行步驟**：使用條列式詳細列出每一步要點擊的按鈕與輸入的值。
     - **預期結果**：定義通過 (Pass) 或失敗 (Fail) 的具體條件。

3. **觸發自動測試 (呼叫 AI Agent)**
   - 於 AI 聊天介面中輸入觸發關鍵字，例如：`「請依照 Test/FeatureX_Test.md 執行驗收」` 或 `「/test」`。
   - AI Agent 將會自動啟動 `autoTestReport` 技能。
   - Agent 會呼叫深層的 **Browser Subagent (瀏覽器子代理)**，開啟虛擬瀏覽器，依循測試案例中的步驟執行。
   - 執行過程會全程錄影（儲存為 WebP 格式），並在關鍵節點由子代理回報狀態與截圖DOM。

4. **報告生成與查閱**
   - 測試完成後，Agent 將自動使用終端機指令 (run_command) 觸發專案內建的報告生成器。
   - 執行檔路徑為：`.agent/skills/autoTestReport/scripts/generate_report.exe`
   - 執行後，專案的 `reports/` 目錄下將產生一份名為 `Acceptance_Report_{時間戳記}.html` 的文件。
   - 點擊該 HTML 檔案即可查看包含截圖、錄影、步驟說明及最終 Pass/Fail 判定結果的報告。

## [預期結果] 預期結果與驗證標準
- **交付成果**：每次執行測試後，皆會產生一份獨立且完整的 HTML 驗收測試報告。
- **驗證標準**：
  - 測試案例必須結構化、步驟清晰，避免模糊不清的指令。
  - 測試報告必須包含：執行日期時間、測試摘要（通過/失敗）、每個步驟的文字紀錄與實際網頁截圖。
  - 若測試結果為 Fail，報告中需明確指出是在哪一個步驟發生異常（例如：找不到指定元素、頁面超時等）。

---

## 專案檔案結構

```
AutoTest/
├── README.md               ← 📖 本文件（非工程人員入口）
├── SOP.md                  ← 📖 SOP 操作手冊
├── CONTRIBUTING.md         ← 🔧 工程開發指南
├── Test/                   ← 📝 測試案例存放區（PM/SA 撰寫）
│   ├── AutoTestReport_v1.md
│   ├── AutoTestReport_v1_1.md
│   └── AdvancedSearchTest.md
├── reports/                ← 📊 自動產生的 HTML 測試報告
├── docs/                   ← 🔧 工程技術文件
│   └── architecture.md
├── dev/                    ← 🔧 開發用原始碼
├── .agent/                 ← 🔧 AI Agent 技能設定
└── .github/                ← 🔧 CI/CD 設定
```

## 文件導覽

| 文件 | 閱讀對象 | 說明 |
|---|---|---|
| [README.md](README.md) | PM / SA / QA | 專案總覽與快速入門 |
| [SOP.md](SOP.md) | PM / SA / QA | 撰寫與執行測試案例的標準作業程序 |
| [Test/*.md](Test/) | PM / SA | 測試案例範例與範本 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 工程人員 | 開發環境設定、技術架構、版控指引 |
| [docs/architecture.md](docs/architecture.md) | 工程人員 | 系統架構設計與元件互動流程圖 |

---
**相關文件**
- [SOP 操作手冊](SOP.md)：詳細的測試案例撰寫與操作教學。
- [測試案例範例](Test/AutoTestReport_v1_1.md)：具體的 Markdown 測試案例參考。
- [工程開發指南](CONTRIBUTING.md)：開發者專用，包含環境設定與技術細節。
- [系統架構設計](docs/architecture.md)：系統流程圖與元件職責說明。

---

## AI 技能 (Skills) 使用指南與範例

為了讓非工程背景的成員能快速上手，本專案內建了幾個強大的 AI Skills，以下是具體的使用情境與觸發範例：

### 1. `autoTestReport` (Markdown 網頁自動化測試)
- **適用情境**：當您已經寫好了一份 Markdown (`.md`) 格式的測試案例，想讓 AI 自動打開網頁執行點擊、截圖，並產出 HTML 報告。
- **輸入範例 (對話框)**：
  > 「請依照 `Test/AutoTestReport_v1_1.md` 的步驟執行驗收測試。」
  > 「幫我跑一下 `Test/AdvancedSearchTest.md`，並產生測試報告給 QA。」
- **AI 執行內容**：讀取 Markdown 檔案 -> 啟動虛擬瀏覽器 -> 全程錄影並截圖 -> 判定每個步驟是否 Pass -> 輸出 `reports/Acceptance_Report_*.html`。

### 2. `browser-test-reporter` (Word 文件網頁自動化測試)
- **適用情境**：當您的測項是寫在 Word 文件 (`.docx`) 中（常見於傳統 PM/SA 發包規格），希望 AI 直接讀取 Word 表格進行測試，**並把測試結果 (Pass/Fail) 寫回 Word 文件中**，同時附上截圖與 HTML 報告。
- **輸入範例 (對話框)**：
  > 「請使用 `docs/test.docx` 進行自動化跑測，並產出報告。」
  > 「幫我用 Word 檔做自動化測試，檔案在 `docs/test2.docx`。」
- **AI 執行內容**：解析 Word 文件內容 -> 啟動虛擬瀏覽器測試 -> 將測試結果與截圖寫回一份新的 Word 文件（如 `docs/report_test.docx`）-> 同時輸出 HTML 網頁版報告。

### 3. `wrap-up` (專案收尾與 Git 自動版控)
- **適用情境**：當您（或工程師）完成了一次修改或測試，準備結束工作，希望 AI 幫忙整理剛剛的產出、把該進版控的程式碼透過 Git 提交，並且自動反思今天學到的經驗（記錄到 `lessons.md`）。
- **輸入範例 (對話框)**：
  > 「完成任務，幫我收尾 wrap up」
  > 「close session」
- **AI 執行內容**：檢查未提交的檔案 -> 生成符合規範的中文 Commit Message -> 提交進遠端分支 -> 記錄本次對話的知識點避免下次再犯。
