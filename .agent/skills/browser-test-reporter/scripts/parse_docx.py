#!/usr/bin/env python3
"""
parse_docx.py — Extract structured test cases from a Word (.docx) document.

Converts the document to Markdown via pandoc, then applies heuristic parsing
to produce a test_cases.json file consumable by run_tests.py.

Usage:
    python scripts/parse_docx.py input.docx
    python scripts/parse_docx.py docs/input.docx --output reports/test_cases.json
    python scripts/parse_docx.py docs/input.docx --output reports/test_cases.json --base-url https://example.com
    python scripts/parse_docx.py input.docx --dump-markdown   # Debug: show raw markdown
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path


# ---------------------------------------------------------------------------
# Pandoc conversion
# ---------------------------------------------------------------------------

def docx_to_markdown(docx_path: Path) -> str:
    """Run pandoc to convert .docx → Markdown string."""
    try:
        result = subprocess.run(
            ["pandoc", "--track-changes=all", str(docx_path), "-t", "markdown"],
            capture_output=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout
    except FileNotFoundError:
        print("[ERROR] pandoc not found. Install it: winget install JohnMacFarlane.Pandoc", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] pandoc failed: {e.stderr}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Heuristic parsers
# ---------------------------------------------------------------------------

_TC_HEADER_RE = re.compile(
    r"^#{1,4}\s*(?:TC[-\s]?(\d+)[:\s]?\s*)?(.+)$", re.IGNORECASE
)
_NUMBERED_STEP_RE = re.compile(r"^\d+[\.\)]\s+(.+)")
_BULLET_STEP_RE = re.compile(r"^[-*]\s+(.+)")
_EXPECTED_RE = re.compile(
    r"(?:expected|預期結果|期望|result|verify|驗證)[\s:：]+(.+)", re.IGNORECASE
)
_URL_RE = re.compile(r"https?://[^\s\"'>]+")
# Note: \s* is used instead of \s+ for Chinese patterns because Chinese
# text typically has no space between keyword and target (e.g. "進入首頁").

# 搜尋框常見 CSS 選擇器（供 fill_search 與 fallback 使用）
_SEARCH_INPUT_SELECTORS = (
    "input[name*=keyword], input[name*=Keyword], "
    "input[placeholder*=檢索], input[placeholder*=搜尋], input[placeholder*=查詢], "
    "input.ui-autocomplete-input, input[type=search], "
    "input[name*=search], input[name*=query], #search, .search-input"
)

_STEP_ACTION_PATTERNS = [
    # --- goto / navigate ---
    (re.compile(r"^(?:navigate|go\s*to)\s+(.+)", re.I), "goto"),
    (re.compile(r"^(?:開啟|前往|瀏覽|進入|連到|連至|造訪|訪問|到)\s*(.+)", re.I), "goto"),
    # --- click ---
    (re.compile(r"^(?:click)\s+(.+)", re.I), "click"),
    (re.compile(r"^(?:按下|點擊|點選|按|點|選按|勾選|展開|收合|切換|按鈕)\s*(.+)", re.I), "click"),
    # --- fill ---
    (re.compile(r"^(?:type|enter|input|fill)\s+[\"']?(.+?)[\"']?\s+(?:in(?:to)?)\s+(.+)", re.I), "fill"),
    (re.compile(r"^(?:輸入|填入|填寫|鍵入)\s*[「「\"']?(.+?)[」」\"']?\s*(?:於|到|在|至)\s*(.+)", re.I), "fill"),
    # fill without explicit target: "輸入『南方資料館』關鍵字" → fill search box
    (re.compile(r"^(?:輸入|填入|填寫|鍵入)\s*[「「\"']?(.+?)[」」\"']?\s*(?:關鍵字|搜尋|查詢|字串)", re.I), "fill_search"),
    # --- select ---
    (re.compile(r"^(?:select)\s+[\"']?(.+?)[\"']?\s+(?:from|in)\s+(.+)", re.I), "select"),
    (re.compile(r"^(?:選擇|選取|下拉選)\s*[「「\"']?(.+?)[」」\"']?\s*(?:於|在|從)\s*(.+)", re.I), "select"),
    # --- hover ---
    (re.compile(r"^(?:hover)\s+(.+)", re.I), "hover"),
    (re.compile(r"^(?:滑鼠移至|移至|移到|懸停)\s*(.+)", re.I), "hover"),
    # --- assert_visible ---
    (re.compile(r"^(?:verify|assert|check)\s+(.+?)\s+(?:is\s+visible|appears?)", re.I), "assert_visible"),
    (re.compile(r"^(?:確認|驗證|確保|檢查)\s*(.+?)\s*(?:可見|存在|出現|顯示|呈現)", re.I), "assert_visible"),
    # --- assert_url ---
    (re.compile(r"^(?:verify|assert|check|確認|驗證)\s*(?:url|網址|連結)\s*(?:is|contains?|包含|為)?\s*(.+)", re.I), "assert_url"),
    # --- assert_text ---
    (re.compile(r"^(?:verify|assert|check|確認|驗證)\s*(?:文字|text|內容)\s*(?:is|contains?|包含|為)?\s*(.+)", re.I), "assert_text"),
    # --- wait ---
    (re.compile(r"^(?:wait|等待)\s*(\d+)", re.I), "wait"),
    # --- screenshot ---
    (re.compile(r"^(?:screenshot|截圖|擷圖|截取畫面)\s*(.*)", re.I), "screenshot"),
    # --- scroll ---
    (re.compile(r"^(?:scroll|捲動|滾動|向下捲)\s*(.*)", re.I), "scroll"),
]

# Broader "verb-like" Chinese keywords for second-pass matching
_ZH_GOTO_VERBS = re.compile(r"^(?:進入|開啟|前往|瀏覽|連到|連至|造訪|訪問|查看|檢視|打開)")
_ZH_CLICK_VERBS = re.compile(r"^(?:點選|點擊|按下|按|點|選按|勾選|展開|收合|切換)")
_ZH_FILL_VERBS = re.compile(r"^(?:輸入|填入|填寫|鍵入)")
_ZH_ASSERT_VERBS = re.compile(r"^(?:確認|驗證|確保|檢查)")
_ZH_BROWSE_KEYWORDS = re.compile(r"(?:使用|利用|透過|以).*(?:開啟|瀏覽|檢視|查看|進入)")


def _resolve_arrow_chains(text: str) -> str:
    """
    Handle → as a navigation-chain indicator, NOT a step separator.
    "點選主選單→全宗瀏覽" → "點選全宗瀏覽" (keep verb, use final target).
    Works on comma-separated text: each comma-fragment is resolved individually.
    """
    if "→" not in text:
        return text
    result_parts = []
    for fragment in re.split(r"[,，；;]", text):
        fragment = fragment.strip()
        if "→" not in fragment:
            result_parts.append(fragment)
            continue
        arrow_parts = [p.strip() for p in fragment.split("→") if p.strip()]
        if len(arrow_parts) < 2:
            result_parts.append(fragment.replace("→", ""))
            continue
        first, last = arrow_parts[0], arrow_parts[-1]
        verb_match = re.match(
            r"^(點選|點擊|按下|按|點|選按|切換|展開|進入|前往|開啟|瀏覽|到)\s*",
            first,
        )
        if verb_match:
            result_parts.append(f"{verb_match.group(1)}{last}")
        else:
            result_parts.append(f"點選{last}")
    return "，".join(result_parts)


def infer_step(raw: str) -> dict:
    """Best-effort conversion of a free-text step into an action dict."""
    text = raw.strip()
    # Strip common leading markers like "步驟1.", "Step 1:", bullets, etc.
    text = re.sub(r"^(?:步驟|step)\s*\d*[.、:：]?\s*", "", text, flags=re.I).strip()
    if not text:
        return {"action": "screenshot", "name": "blank_step"}
    # Resolve arrow chains within text: "點選X→Y" → "點選Y"
    if "→" in text:
        text = _resolve_arrow_chains(text)

    # --- First pass: explicit regex patterns ---
    for pattern, action in _STEP_ACTION_PATTERNS:
        m = pattern.match(text)
        if m:
            groups = m.groups()
            step: dict = {"action": action}
            if action == "fill" and len(groups) >= 2:
                step["target"] = groups[1].strip()
                step["value"] = groups[0].strip()
            elif action == "fill_search":
                # Special: fill a search box with the captured value
                step["action"] = "fill"
                step["target"] = _SEARCH_INPUT_SELECTORS
                step["value"] = groups[0].strip().strip("「」\"'")
            elif action == "select" and len(groups) >= 2:
                step["target"] = groups[1].strip()
                step["value"] = groups[0].strip()
            elif action == "wait":
                step["target"] = groups[0].strip()
            elif action == "scroll":
                step["target"] = groups[0].strip() if groups[0].strip() else "500"
            else:
                step["target"] = groups[0].strip() if groups else text
            return step

    # --- Second pass: broad Chinese verb detection ---
    if _ZH_GOTO_VERBS.search(text):
        return {"action": "goto", "target": "/"}
    if _ZH_BROWSE_KEYWORDS.search(text):
        return {"action": "goto", "target": "/"}
    if _ZH_CLICK_VERBS.search(text):
        remainder = _ZH_CLICK_VERBS.sub("", text).strip()
        return {"action": "click", "target": f"text={remainder}" if remainder else "body"}
    if _ZH_FILL_VERBS.search(text):
        remainder = _ZH_FILL_VERBS.sub("", text).strip()
        # Try to extract quoted value
        qm = re.search(r"[「「\"'](.+?)[」」\"']", remainder)
        if qm:
            return {"action": "fill", "target": _SEARCH_INPUT_SELECTORS, "value": qm.group(1)}
        return {"action": "fill", "target": "input[type=text]", "value": remainder}
    if _ZH_ASSERT_VERBS.search(text):
        remainder = _ZH_ASSERT_VERBS.sub("", text).strip()
        return {"action": "assert_visible", "target": f"text={remainder[:60]}" if remainder else "body"}

    # --- Fallback: screenshot-only step (don't fail on unrecognized text) ---
    return {"action": "screenshot", "name": re.sub(r'[^\w]', '_', text[:40])}


def parse_markdown_to_cases(md: str, base_url: str = "") -> dict:
    """Heuristically parse Markdown produced from a Word doc into test cases."""
    lines = md.splitlines()
    meta: dict = {
        "title": "Test Suite",
        "base_url": base_url,
        "environment": "",
        "tested_by": "",
        "date": str(date.today()),
    }
    test_cases: list[dict] = []

    # --- Detect meta block (first few lines before first header) -----------
    for line in lines[:20]:
        if re.search(r"(?:URL|base.?url|網址|網站)", line, re.I):
            urls = _URL_RE.findall(line)
            if urls and not meta["base_url"]:
                meta["base_url"] = urls[0]
        if re.search(r"(?:title|名稱|測試名|project)", line, re.I):
            parts = re.split(r"[：:\t]+", line, maxsplit=1)
            if len(parts) == 2:
                meta["title"] = parts[1].strip()
        if re.search(r"(?:環境|environment|env)", line, re.I):
            parts = re.split(r"[：:\t]+", line, maxsplit=1)
            if len(parts) == 2:
                meta["environment"] = parts[1].strip()
        if re.search(r"(?:author|by|by|撰寫者|PM|SA)", line, re.I):
            parts = re.split(r"[：:\t]+", line, maxsplit=1)
            if len(parts) == 2:
                meta["tested_by"] = parts[1].strip()

    # --- Detect table-based test cases ------------------------------------
    table_cases = _parse_table_cases(lines)
    if table_cases:
        return {"meta": meta, "test_cases": table_cases}

    # --- Detect pandoc grid table (complex Word tables) -------------------
    grid_cases = _parse_grid_table_cases(md)
    if grid_cases:
        return {"meta": meta, "test_cases": grid_cases}

    # --- Detect section-based test cases (numbered/bulleted steps) --------
    current_case: dict | None = None
    tc_counter = 0

    for line in lines:
        h_match = _TC_HEADER_RE.match(line)
        if h_match and re.search(r"TC|test case|測試|案例", line, re.I):
            # Save previous
            if current_case and current_case.get("steps"):
                test_cases.append(current_case)
            tc_counter += 1
            tc_num = h_match.group(1) or str(tc_counter)
            tc_name = h_match.group(2).strip()
            current_case = {
                "id": f"TC-{int(tc_num):03d}",
                "name": tc_name,
                "description": "",
                "steps": [],
                "expected_result": "",
            }
            continue

        if current_case is None:
            continue

        # Numbered / bullet steps
        s_match = _NUMBERED_STEP_RE.match(line) or _BULLET_STEP_RE.match(line)
        if s_match:
            step_text = s_match.group(1).strip()
            exp_m = _EXPECTED_RE.match(step_text)
            if exp_m:
                current_case["expected_result"] = exp_m.group(1).strip()
            else:
                current_case["steps"].append(infer_step(step_text))
            continue

        # Expected result line
        exp_m = _EXPECTED_RE.search(line)
        if exp_m and not line.startswith("#"):
            current_case["expected_result"] = exp_m.group(1).strip()
            continue

    if current_case and current_case.get("steps"):
        test_cases.append(current_case)

    # If nothing found, create a single "exploratory" test case
    if not test_cases:
        print("[WARN] Could not detect structured test cases. Creating a single exploratory case.", file=sys.stderr)
        test_cases = [{
            "id": "TC-001",
            "name": "Exploratory Test",
            "description": "Parsed from unstructured Word document — please edit steps manually",
            "steps": [
                {"action": "goto", "target": meta.get("base_url", "/")},
                {"action": "screenshot", "name": "home"},
            ],
            "expected_result": "Page loads without errors",
        }]

    return {"meta": meta, "test_cases": test_cases}


def _parse_table_cases(lines: list[str]) -> list[dict]:
    """
    Detect Markdown pipe-table with columns like:
    | ID | Name | Steps | Expected |
    Returns list of test case dicts, or empty list if not found.
    """
    in_table = False
    headers: list[str] = []
    cases: list[dict] = []

    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            if in_table:
                break
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        # Separator row (---|---|...)
        if all(re.match(r"^[-:]+$", c) for c in cells if c):
            continue
        if not in_table:
            # Header row
            headers = [h.lower() for h in cells]
            in_table = True
            continue
        # Data row
        row = dict(zip(headers, cells))
        id_val = row.get("id", row.get("編號", ""))
        name_val = row.get("name", row.get("test case", row.get("名稱", row.get("測試案例", ""))))
        steps_raw = row.get("steps", row.get("步驟", row.get("step", "")))
        expected = row.get("expected", row.get("expected result", row.get("預期結果", "")))

        if not name_val:
            continue

        step_list = []
        for s in re.split(r"[;\n。；]", steps_raw):
            s = s.strip()
            if s:
                step_list.append(infer_step(s))

        tc_counter = len(cases) + 1
        cases.append({
            "id": id_val or f"TC-{tc_counter:03d}",
            "name": name_val,
            "description": "",
            "steps": step_list if step_list else [{"action": "goto", "target": "/"}],
            "expected_result": expected,
        })

    return cases


def _parse_grid_table_cases(md: str) -> list[dict]:
    """
    Parse pandoc 'grid table' format (uses +---+---+ separators).
    Handles the complex multi-line cell format Word tables produce via pandoc.
    Returns list of test case dicts, or empty list if no useful rows found.
    """
    cases: list[dict] = []
    # Split by grid-table section separator (+===+) to find header vs data
    # Each row block starts with +----+ line, then | content | lines
    row_blocks: list[list[str]] = []
    current: list[str] = []
    in_grid = False

    for line in md.splitlines():
        if re.match(r"^\+[=\-]+", line):
            if current:
                row_blocks.append(current)
                current = []
            in_grid = True
            continue
        if in_grid and line.startswith("|"):
            current.append(line)
        elif in_grid and not line.startswith("|") and not line.startswith("+"):
            if current:
                row_blocks.append(current)
                current = []
            in_grid = False

    if current:
        row_blocks.append(current)

    def flatten_cell_lines(cell_lines: list[str]) -> str:
        """Join multi-line cell content into single string, stripping markup."""
        raw = " ".join(l.strip() for l in cell_lines if l.strip())
        # Remove bold markers
        raw = re.sub(r"\*\*(.+?)\*\*", r"\1", raw)
        return raw.strip()

    def extract_row_cells(row_lines: list[str]) -> list[str]:
        """Split a set of | ... | lines into per-column text."""
        if not row_lines:
            return []
        # Count columns from first line
        first = row_lines[0]
        col_texts: list[list[str]] = []
        raw_cells = first.strip("|").split("|")
        for _ in raw_cells:
            col_texts.append([])
        for l in row_lines:
            parts = l.strip("|").split("|")
            for i, p in enumerate(parts):
                if i < len(col_texts):
                    col_texts[i].append(p.strip())
        return [flatten_cell_lines(c) for c in col_texts]

    tc_counter = 0
    for block in row_blocks:
        cells = extract_row_cells(block)
        if len(cells) < 2:
            continue
        # Skip header rows (containing 個案編號, 項目序, 測試目標, etc.)
        first_cell = cells[0].strip()
        if re.search(r"個案編號|項目序|測試目標|測試紀錄", first_cell):
            continue
        # Data row: first cell is sequence number, second is test item name
        seq = first_cell
        name = cells[1] if len(cells) > 1 else ""
        steps_raw = cells[2] if len(cells) > 2 else ""
        expected = cells[3] if len(cells) > 3 else ""

        if not name or not re.match(r"^\d+", seq):
            continue

        # Build steps — resolve arrow chains, then split by standard separators
        processed = _resolve_arrow_chains(steps_raw)
        step_list = []
        for s in re.split(r"[,，；;]", processed):
            s = s.strip()
            if s:
                step_list.append(infer_step(s))
        # Ensure goto at start and screenshot at end for meaningful capture
        if not any(st.get("action") == "goto" for st in step_list):
            step_list.insert(0, {"action": "goto", "target": "/"})
        step_list.append({"action": "screenshot", "name": f"TC-{tc_counter+1:03d}_final"})

        tc_counter += 1
        cases.append({
            "id": f"TC-{tc_counter:03d}",
            "name": name,
            "description": steps_raw,
            "steps": step_list,
            "expected_result": expected,
        })

    return cases


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse a Word (.docx) test spec document → test_cases.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("docx", help="Path to the input .docx file")
    parser.add_argument("--output", "-o", default="reports/test_cases.json", help="Output JSON file (default: reports/test_cases.json)")
    parser.add_argument("--base-url", default="", help="Base URL to inject into meta (overrides any URL found in document)")
    parser.add_argument("--dump-markdown", action="store_true", help="Print the raw pandoc Markdown and exit (for debugging)")
    args = parser.parse_args()

    docx_path = Path(args.docx)
    if not docx_path.exists():
        print(f"[ERROR] File not found: {docx_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[1/3] Converting {docx_path.name} → Markdown via pandoc...")
    md = docx_to_markdown(docx_path)

    if args.dump_markdown:
        print(md)
        return

    print("[2/3] Parsing test cases from Markdown...")
    payload = parse_markdown_to_cases(md, base_url=args.base_url)

    # --- python-docx 直接讀取 fallback ---
    # pandoc 將複雜 Word 表格（含合併儲存格）轉為 HTML 而非 Markdown 表格，
    # 導致 heuristic parser 無法辨識。此處用 python-docx 直接讀取作為備援。
    try:
        import docx as _docx
        doc = _docx.Document(docx_path)
        docx_cases: list[dict] = []
        for table in doc.tables:
            headers: list[str] = []
            for row in table.rows:
                cells = [c.text.strip().replace('\n', ' ') for c in row.cells]
                if "項目序" in cells or "測試項目" in cells:
                    headers = [h.lower() for h in cells]
                    continue
                if headers and len(cells) == len(headers):
                    row_dict = dict(zip(headers, cells))
                    name_val = row_dict.get("測試項目", row_dict.get("test case", row_dict.get("name", "")))
                    steps_raw = row_dict.get("操作步驟", row_dict.get("steps", row_dict.get("step", "")))
                    expected = row_dict.get("預期結果", row_dict.get("expected result", row_dict.get("expected", "")))
                    if not name_val or name_val in ("測試項目", "test case", "name"):
                        continue
                    step_list = []
                    for s in re.split(r"[;\n。；]", steps_raw):
                        s = s.strip()
                        if s:
                            step_list.append(infer_step(s))
                    docx_cases.append({
                        "id": f"TC-{len(docx_cases)+1:03d}",
                        "name": name_val,
                        "description": steps_raw,
                        "steps": step_list if step_list else [{"action": "goto", "target": "/"}],
                        "expected_result": expected,
                    })
        if docx_cases:
            payload["test_cases"] = docx_cases
            print(f"  → python-docx 直接讀取成功，覆寫為 {len(docx_cases)} 筆測試案例")
    except Exception as e:
        print(f"[WARN] python-docx 直接讀取失敗: {e}", file=sys.stderr)

    n = len(payload["test_cases"])
    print(f"[3/3] Found {n} test case(s). Writing → {args.output}")
    out_path = Path(args.output)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ Done: {out_path.resolve()}")
    print(f"   Base URL : {payload['meta']['base_url'] or '(not set — add --base-url)'}")
    print(f"   Test cases:")
    for tc in payload["test_cases"]:
        print(f"     [{tc['id']}] {tc['name']} ({len(tc['steps'])} step(s))")
    print("\nNext step: python scripts/run_tests.py", out_path, "--output-dir ./reports")


if __name__ == "__main__":
    main()
