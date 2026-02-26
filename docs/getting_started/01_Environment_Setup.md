# 01. 環境建置指南 (Environment Setup)

本章節將指導您如何從零開始，配置能夠運行本專案 AI Agent（如：`autoTestReport`、`browser-test-reporter`）的開發與測試環境。

---

## 步驟一：安裝基礎環境

無論您是 PM、SA 還是工程師，都需要具備最基本的環境才能啟動 AI Agent。

### 1. 安裝 Visual Studio Code (VS Code)
本專案的 AI 工具深度整合於編輯器中，請確保已安裝 VS Code。
- [下載並安裝 VS Code](https://code.visualstudio.com/)

### 2. 下載並開啟專案原始碼
透過 Git 或直接下載 ZIP 檔將本專案 (`AutoTest`) 解壓縮放在本機電腦中。
1. 打開 VS Code。
2. 點擊 `檔案 (File)` > `開啟資料夾 (Open Folder)`，選擇 `AutoTest` 目錄。

---

## 步驟二：安裝 Antigravity IDE (Gemini Agent)

本專案依賴強大的 AI 代理程式執行測試，請安裝官方提供的 Antigravity 擴充套件。

1. 在 VS Code 左側活動列點擊 **延伸模組 (Extensions)** 圖示 (或按 `Ctrl+Shift+X`)。
2. 於搜尋列輸入 `Antigravity` 或您組織專屬的 AI 擴充套件名稱。
3. 點擊 **安裝 (Install)**。
4. 安裝完成後，依據套件指示登入您的 Google 帳號或輸入專案的 API 授權金鑰。

### 配置 Workspace 權限
為了讓 AI 能夠讀取您寫好的測試文件（如 `.md` 或 `.docx`），並將截圖、報告正確寫入 `reports/` 目錄：
1. 確認您的 VS Code 當前開啟的根目錄是 `AutoTest`。
2. 若系統跳出「是否信任此工作區 (Trust the authors of the files in this folder?)」的提示，請務必點選 **Yes, I trust the authors**。
3. 您可以嘗試在 AI 聊天框輸入：「`Hello`」，確認 AI 有正常回應。

---

## 步驟三：基礎 Python 環境 (給需要本機測試的 QA/PG)

> **注意**：如果您只是 PM / SA（只負責寫測試規格請 AI 跑），可以直接跳過此步驟。本專案已備有編譯好的 `.exe` 執行檔，AI 跑完會自動呼叫。

若您需要修改報告生成邏輯或安裝相依套件，請依以下步驟使用 `uv` 管理環境：

1. **安裝 uv 工具**：
   在終端機 (Terminal) 中執行：
   ```powershell
   # Windows (PowerShell)
   iwr -useb https://astral.sh/uv/install.ps1 | iex
   ```
2. **建立虛擬環境**：
   在 `AutoTest` 根目錄下執行：
   ```bash
   uv venv .venv
   ```
3. **啟用虛擬環境與安裝相依套件**：
   ```powershell
   # Windows
   .\.venv\Scripts\Activate.ps1
   # 安裝 Markdown 報告解析套件、Word 解析等
   uv pip install markdown python-docx beautifulsoup4
   ```

---

## 🎉 下一步

環境配置完成！請根據您的角色選擇後續教學：
- 👉 [給 PM / SA 的零程式碼測試教學 (撰寫 .docx 與 .md)](02_Tutorial_for_PM_SA.md)
- 👉 [給 QA / PG 的進階除錯與維護教學](03_Tutorial_for_PG_QA.md)
