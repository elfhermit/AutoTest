---
name: wrap-up
description: 適用於使用者輸入 "wrap up", "close session", "完成任務" 或 "收尾" 時觸發。將自動執行包含程式碼提交、記憶鞏固（寫入 lessons.md）與知識萃取的標準收尾流程。
---

# Session Wrap-Up Protocol (會話收尾流程)

You must execute the following four phases sequentially. Do not ask for permission between phases; auto-apply the logic and present a consolidated final report in Traditional Chinese (zh-TW).

## Phase 1: 整理與交付 (Ship It)

1. **Git Commit**: 檢查專案目錄下的變更狀態 (`git status`)。若有未提交的變更，請自動生成符合常規的 commit message 並提交 (Commit)。如有遠端分支，嘗試 Push。
2. **File Organization**: 檢查本次對話中建立或修改的檔案。確認它們放置在正確的目錄下（例如：文件應移至 `docs/` 或 `.gemini/`）。若有錯置，自動移動它們。
3. **Task Cleanup**: 讀取 `.gemini/tasks/todo.md`。將已完成的任務標記為完成 (Done)，並列出尚未完成的遺留任務 (Pending)。

## Phase 2: 記憶鞏固與反思 (Remember & Reflect)

Review the entire session to extract knowledge. Categorize findings into the following specific locations:

- **Global Rules (`GEMINI.md`)**: 適用於整個專案的永久性架構決策或重要規範。
- **Local Rules (`.gemini/rules/`)**: 針對特定目錄或技術棧的局部規則（例如：`database-rules.md`）。
- **Lessons Learned (`.gemini/tasks/lessons.md`)**: 本次會話中 Gemini 犯的錯誤、掙扎的邏輯，或使用者糾正的痛點。必須提煉成「未來不再犯」的通用規則。
- **Local Context (`.gemini/local.md`)**: 僅限本機開發用的環境變數說明、暫存測試網址或個人筆記（不需要 Commit 的資訊）。

## Phase 3: 自動應用與總結 (Review & Apply)

Do not just suggest changes; physically write/update the files identified in Phase 2. 

Analyze the conversation for self-improvement. Categories include:
- **Skill Gap**: 需要多次嘗試才寫對的程式碼。
- **Friction**: 使用者必須重複提醒的繁瑣步驟。
- **Knowledge**: 專案中 Gemini 原本不知道但剛剛學到的機制。

**Action Required**:
Update `GEMINI.md`, create specific `.gemini/rules/` files, or append rules to `.gemini/tasks/lessons.md`.

Format your response summary exactly like this:

**[已應用的自我修正]**
* ✅ Skill Gap: (簡述問題) → [已更新 lessons.md] (簡述新增的規則)
* ✅ Knowledge: (簡述新知識) → [已更新 GEMINI.md] (簡述加入的段落)

**[無需動作]**
* (列出發現但已存在於文件中的知識)

## Phase 4: 知識萃取 (Publish It)

Review the completed work for publishable value. Look for:
- 獨特的技術解法或 Debug 過程。
- 值得分享的架構設計。

**If publishable material exists:**
Draft a short technical article or social media post in Traditional Chinese. Save it to `docs/drafts/Title-of-Post.md`.
Mention in your final output: "已在 docs/drafts/ 生成一篇技術分享草稿：[標題]"。

**If no publishable material exists:**
Simply state: "本次會話無產出需額外發佈的內容。"

---
**FINAL MANDATE**: All interactions and the final consolidated report MUST be output in Traditional Chinese (zh-TW).