````skill
---
name: browser-test-reporter
description: "Use this skill when the user (typically a PM, SA, or non-engineer) wants to run automated browser tests based on a Word document (.docx) describing test cases, and receive: (1) a self-contained one-page HTML test report with screenshots and video links, and (2) an updated Word document with test results, PASS/FAIL status and embedded screenshots. Triggers include: 'test my website using a Word file', 'run QA from my docx', 'automated browser test', 'generate test report from Word', '用Word做自動化測試', '瀏覽器功能測試報告'. The skill orchestrates docx parsing → Playwright browser automation → screenshot/video capture → HTML report generation → Word document update."
license: Apache 2.0
---

# Browser Test Reporter (Word 路線)

以 Word 文件（`.docx`）為輸入，使用 **AI Agent + browser_subagent** 統一執行引擎，自動執行瀏覽器測試，
產出 HTML 測試報告 + 更新後的 Word 文件（含截圖與PASS/FAIL 標示）。

> **執行引擎與方案 A (autoTestReport) 完全一致**  
> 差異僅在輸入格式：方案 A 使用 `.md`，方案 B 使用 `.docx`。

---

## Available Scripts

| Script | Purpose |
|--------|---------|
| `scripts/parse_docx.exe` | Extract structured test cases from `.docx` → JSON |
| `scripts/run_tests.py` | Execute test cases with Playwright (screenshots + video) |
| `scripts/generate_report.exe` | Build self-contained one-page HTML report |
| `scripts/update_docx.exe` | Inject results and screenshots back into the Word doc |

**Always run each script with `--help` first** to see its exact usage before invoking it.

---

## End-to-End Workflow

```
Step 1  parse_docx.exe      → reports/test_cases.json  (parse Word input)
Step 2  AI Agent + browser_subagent  → reports/walkthrough.md + 截圖 + 錄影  (execute tests)
Step 3  generate_report.exe → reports/report.html  (build HTML report)
Step 4  update_docx.exe     → reports/report_<original>.docx  (update Word doc)
```

### Step 1 – Parse the Word Document

```bash
.agent/skills/browser-test-reporter/scripts/parse_docx.exe docs/input.docx --output reports/test_cases.json
```

- Calls `pandoc` to convert `.docx` → Markdown, then uses LLM-friendly JSON schema
- Supported Word layouts: numbered lists, tables, free prose
- Output: `reports/test_cases.json` (see schema below)

### Step 2 – 執行測試（AI Agent + browser_subagent）

對 `reports/test_cases.json` 中的每一個 test case，依序呼叫 `browser_subagent` 執行：

- 將測試案例的步驟、Base URL、預期結果作為 Task 提示詞傳遞給 Subagent
- 設定 `RecordingName` 參數（如 `tc001_recording`）以機器錄影
- Subagent 返回後，整理結果（步驟狀態、錯誤訊息、截圖、PASS/FAIL）
- **[重要產出]：除了 HTML 與 Word，Agent 會強制產生一份結構化的 Markdown 圖文驗證報告（例如另存至 `reports/walkthrough_<name>.md`，內含「各案例執行細節」與相對應的截圖連結），以利後續原始碼區檢閱。**

> **備用**：`run_tests.py` 保留作為 Playwright 直接執行的 CI/CD 備用方案。

- Launches Chromium via Playwright
- Takes screenshots at every step + on failure
- Saves one `.webm` video per test case (optional)
- Writes `reports/results.json`

### Step 3 – Generate HTML Report

```bash
.agent/skills/browser-test-reporter/scripts/generate_report.exe reports/results.json \
  --screenshots-dir ./reports/screenshots \
  --videos-dir ./reports/videos \
  --output reports/report.html
```

- Produces a single self-contained `.html` (screenshots base64-inlined)
- Sections: Summary banner → Environment info → Test case cards → Screenshot lightbox
- PASS = green, FAIL = red, SKIP = grey
- Can be printed to PDF from the browser

### Step 4 – Update Word Document

```bash
.agent/skills/browser-test-reporter/scripts/update_docx.exe docs/input.docx reports/results.json \
  --screenshots-dir ./reports/screenshots \
  --walkthrough reports/walkthrough.md \
  --output reports/report_input.docx
```

- Appends a "Test Execution Summary" section to the original Word doc
- Inserts PASS/FAIL status (green/red) next to each test case
- Embeds representative screenshots beneath each test case heading

---

## reports/test_cases.json Schema

```json
{
  "meta": {
    "title": "Test Suite Name",
    "base_url": "https://example.com",
    "environment": "staging",
    "tested_by": "PM Name",
    "date": "2026-02-25"
  },
  "test_cases": [
    {
      "id": "TC-001",
      "name": "User Login",
      "description": "Verify that a registered user can log in successfully",
      "steps": [
        { "action": "goto", "target": "/login" },
        { "action": "fill", "target": "#email", "value": "test@example.com" },
        { "action": "fill", "target": "#password", "value": "secret" },
        { "action": "click", "target": "button[type=submit]" },
        { "action": "assert_url", "target": "/dashboard" },
        { "action": "assert_visible", "target": "text=Welcome" }
      ],
      "expected_result": "User is redirected to dashboard and sees welcome message"
    }
  ]
}
```

### Supported Step Actions

| Action | Parameters | Description |
|--------|-----------|-------------|
| `goto` | `target` = URL path | Navigate to URL |
| `click` | `target` = selector | Click an element |
| `fill` | `target` = selector, `value` = string | Type into input |
| `select` | `target` = selector, `value` = option | Select dropdown option |
| `hover` | `target` = selector | Hover over element |
| `wait` | `target` = milliseconds | Pause execution |
| `screenshot` | `name` = filename | Explicit screenshot |
| `assert_visible` | `target` = selector/text | Assert element visible |
| `assert_text` | `target` = selector, `value` = expected text | Assert text content |
| `assert_url` | `target` = URL path (partial match) | Assert current URL |
| `assert_title` | `target` = page title (partial match) | Assert page title |

---

## results.json Schema (Output of run_tests.py)

```json
{
  "meta": { "...same as test_cases.json meta..." },
  "summary": {
    "total": 5, "passed": 4, "failed": 1, "skipped": 0,
    "duration_seconds": 42.3,
    "started_at": "2026-02-25T14:00:00Z",
    "finished_at": "2026-02-25T14:00:42Z"
  },
  "test_cases": [
    {
      "id": "TC-001",
      "name": "User Login",
      "status": "passed",
      "duration_seconds": 8.1,
      "steps": [
        {
          "index": 0, "action": "goto", "target": "/login",
          "status": "passed",
          "screenshot": "screenshots/TC-001_step_0_goto.png"
        }
      ],
      "video": "videos/TC-001.webm",
      "error": null
    }
  ]
}
```

---

## Decision Tree

```
User provides .docx
       ↓
Does the Word doc have a clear table/list structure?
  ├─ Yes → parse_docx.py will auto-extract test cases
  └─ No  → Ask user to confirm/edit reports/test_cases.json before running
       ↓
Does the site require login?
  ├─ Yes → Add login step as TC-000 or inject credentials via --cookies
  └─ No  → Proceed directly
       ↓
Run run_tests.py (headless for speed, headed for debugging)
       ↓
Did any tests FAIL?
  ├─ Yes → Review failure screenshots, optionally re-run single case:
  │         python scripts/run_tests.py reports/test_cases.json --filter TC-001
  └─ No  → Proceed to report generation
       ↓
Generate report.html + updated .docx
```

---

## Common Pitfalls

- **Dynamic content**: Always wait for `networkidle` or use `assert_visible` before assertions
- **Selector fragility**: Prefer text-based selectors (`text=Login`) over CSS paths
- **Video size**: Videos can be large; disable with omitting `--video` flag for quick runs
- **Word parsing ambiguity**: If `parse_docx.py` cannot identify test cases, present the raw Markdown to the user and ask them to confirm the JSON structure

---

## Dependencies Installation

```bash
# Python dependencies
pip install playwright python-docx Pillow jinja2 pandoc

# Playwright browser
playwright install chromium

# pandoc (system-level)
# Windows: winget install --id JohnMacFarlane.Pandoc
# macOS:   brew install pandoc
# Linux:   apt install pandoc
```
````
