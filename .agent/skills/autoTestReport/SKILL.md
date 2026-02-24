---
name: autoTestReport
description: 自動化驗收測試 (Auto-Acceptance-Test) - 執行網站功能驗收並產生報告
---

# SKILL: 自動化驗收測試 (Auto-Acceptance-Test)

## [階段一] 任務目標與範圍
- **任務目標**：透過自動化瀏覽器操作，執行網站功能驗收，並於測試結束後產生詳細的測試報告。
- **觸發條件**：當使用者輸入以下關鍵字時，請自動啟動此技能：
  - "執行驗收"
  - "開始測試"
  - "/test"
  - "產生測試報告"
- **範圍與限制**：操作必須全程使用繁體中文 (Traditional Chinese)，且扮演嚴格的 QA 測試工程師角色。

## [執行步驟] 詳細執行步驟
一旦觸發，請依序執行以下步驟，無需再次詢問使用者設定細節：

1. **確認測試目標與初始化**
   - 若使用者未指定目標或未提供測試案例 Markdown 檔，請詢問：「請問今天要測試哪個功能或頁面？（例如：登入頁面、購物車結帳），或是請提供測試案例檔案（例如 `Test/AutoTestReport_v1_1.md`）。」
   - 確認目標後，清除 `.agent/test_artifacts/` 資料夾（若存在），並初始化測試環境。
   - **記錄時間**：紀錄當下為「測試開始時間」。

2. **執行瀏覽器自動化 (Browser Automation)**
   - **呼叫工具**：使用 `browser_subagent` 工具執行使用者指定的測試案例。
   - **指派任務 (Task)**：將使用者提供的 Markdown 測試案例（如 `[步驟 1] ~ [步驟 N]`）作為提示詞 (Prompt) 傳遞給 Subagent 執行 Happy Path 與異常路徑。
   - **錄影機制**：務必設定 `RecordingName` 參數（如 `test_case_run`），讓系統自動將操作過程錄影並儲存為 WebP 影片至 artifact 資料夾。
   - 紀錄撰寫：Subagent 返回後，請檢視其結果與 DOM。紀錄當下為「測試結束時間」，並計算與開始時間之差額為「總花費時間」。將詳細的操作步驟、成功與否、網頁截圖，以及**測試開始時間、測試結束時間、總花費時間**皆記錄於 `.agent/test_artifacts/walkthrough.md` 中。

3. **報告生成 (Report Generation)**
   - **呼叫工具**：使用 `run_command` 工具執行位於專案內的執行檔，自動讀取 `.agent/test_artifacts/walkthrough.md` 並打包為 HTML。
   - **指令**：執行相對路徑腳本 `.agent/skills/autoTestReport/scripts/generate_report.exe` (直接執行，無需 Python 環境)

## [預期結果] 預期結果與驗證標準
- **交付成果**：回報：「測試已完成，報告已統一歸檔於 reports 目錄下。」並提供 `reports/Acceptance_Report_{時間戳記}.html` 的檔案連結供使用者點擊開啟。
- **格式規範**：測試報告的 HTML 樣式需專業、整潔，並包含「測試時間」、「執行結果 (Pass/Fail)」摘要、詳細步驟與截圖對照，確保產出檔案不散落於根目錄。
- **語言標準**：所有對話與報告內容必須使用 **繁體中文 (Traditional Chinese)**。