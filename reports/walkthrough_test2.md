# `docs/test2.docx` 自動化測試執行報告

## 執行摘要
已使用 `browser-test-reporter` 的 AI Agent 執行引擎，根據提供的 `docs/test2.docx` 內容完成了 6 項測試案例的自動化執行。

- **目標網站**：`https://tais.ith.sinica.edu.tw/`
- **測試總數**：6 項
- **通過數量**：5 項
- **失敗數量**：1 項 (TC-006 檢索驗證機制)

## 成果產出
所有測試過程皆已自動錄影與截圖，並更新了相關的測試報告檔案：

1. **HTML 互動式報告**：[reports/report_test2.html](./report_test2.html)
2. **Word 更新報告**：[docs/report_test2.docx](../docs/report_test2.docx)
3. **機器可讀結果**：[test_output/results.json](../test_output/results.json)

## 各案例執行細節

1. **TC-001：進入首頁，切換全宗範圍** (PASS)
   - 成功點選「最新開放」選項，頁面正常載入與呈現。
   - ![TC-001](../test_output/screenshots/TC-001.png)

2. **TC-002：全宗瀏覽** (PASS)
   - 透過主選單成功進入全宗瀏覽列表頁面。
   - ![TC-002](../test_output/screenshots/TC-002.png)

3. **TC-003：影像瀏覽器** (PASS)
   - 深入點選單件內容（如「日月潭水力發電工事寫真帖」相關單件），成功開啟單件資訊與觸發影像檢視介面。
   - ![TC-003](../test_output/screenshots/TC-003.png)

4. **TC-004：網站支援各種瀏覽裝置** (PASS)
   - 模擬 Mobile 視窗大小 (375x812) 重新載入首頁，成功呈現響應式（RWD）漢堡選單。
   - ![TC-004](../test_output/screenshots/TC-004.png)

5. **TC-005：關鍵字查詢** (PASS)
   - 輸入「南方資料館」並執行檢索，成功回傳 18 筆相關資料結果。
   - ![TC-005](../test_output/screenshots/TC-005.png)

6. **TC-006：檢索驗證機制** (FAIL)
   - **說明**：以腳本在一分鐘內發送超過一百次快速查詢請求，嘗試觸發「安全驗證功能」（如 CAPTCHA 或阻擋頁面）。
   - **結果**：網站伺服器重置了部分連線（連線逾時），但並未顯示任何使用者可見的「安全驗證功能」或機器人阻擋提示，後續正常請求仍可成功執行。此項目因未符合「顯示安全驗證功能」之預期結果而標為 FAIL。
