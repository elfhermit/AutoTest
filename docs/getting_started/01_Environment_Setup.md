# 01. 環境建置指南 (Environment Setup)

本章節將指導您如何從零開始，配置能夠運行本專案 AI Agent（如：`autoTestReport`、`browser-test-reporter`）的開發與測試環境。

---

## 步驟一：準備專案原始碼

無論您是 PM、SA 還是工程師，都需要先取得專案原始碼才能開始測試。

1. **下載專案**：透過 Git Clone 或直接下載 ZIP 檔，將本專案 (`AutoTest`) 下載並解壓縮至您的本機電腦中。
2. **記住路徑**：請記下此資料夾的存放路徑（例如 `C:\AutoTest` 或 `D:\AutoTest`）。

---

## 步驟二：安裝與設定 Google Antigravity IDE

本專案依賴 Google 專為 AI 代理程式開發的 **Antigravity IDE**。請依循以下步驟進行安裝與設定：

### 1. 下載與安裝 Antigravity IDE
1. 前往 Google Antigravity 的內部發布平台或官方下載點，取得最新版本的安裝檔（Installer）。
2. 雙擊執行安裝程式，並依循畫面指示完成標準安裝。
3. 安裝完畢後，從應用程式選單中啟動 **Antigravity IDE**。

### 2. 登入與授權
第一次開啟 IDE 時，必須進行身分認證才能使用 AI 功能：
1. 點擊畫面上的 **Sign In** (登入) 按鈕。
2. 使用您的 Google 帳號完成 OAuth 授權登入，或輸入系統管理員配發的 API 授權金鑰。

### 3. 載入工作區 (Workspace)
為了讓 AI 能夠讀取您寫好的測試需求，並將產出的報告正確寫入 `reports/` 目錄：
1. 在 Antigravity IDE 頂部選單，點擊 `File` (檔案) > `Open Folder...` (開啟資料夾)。
2. 選擇您在步驟一準備好的 `AutoTest` 目錄。
3. 若系統跳出安全性提示詢問「是否信任此工作區 (Trust the authors of the files in this folder?)」，請務必點選 **Yes, I trust the authors**，否則 AI 將無法寫入檔案。

### 4. 驗證環境
1. 尋找 IDE 介面中的 AI 聊天對話框 (Chat Panel)。
2. 於文字框輸入：「`Hello`」。
3. 若 AI 正常回覆問候語，即代表您的測試指揮中心已連線完畢！

---

## 步驟三：基礎 Python 環境 (給需要本機深層除錯的 QA/PG)

> **⛔ PM / SA 請注意**：您 **不需安裝** Python、Node.js 或是任何工程軟體！
> 專案內已將核心報表生成工具封裝為 `.exe` 執行檔，而其餘驗證動作皆由 Antigravity IDE 內的 AI 核心直接代理處理。
> 您只要完成上述的「步驟一」與「步驟二」，就可以關閉此頁面，直接進入 [給 PM / SA 的零程式碼測試教學](02_Tutorial_for_PM_SA.md) 開始工作！

---

**(以下為工程師專屬)** 若您需要修改報告生成系統底層或開發新技能，請依以下步驟使用 `uv` 管理環境：

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
