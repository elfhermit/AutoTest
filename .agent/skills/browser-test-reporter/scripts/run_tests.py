#!/usr/bin/env python3
"""
run_tests.py — Execute browser test cases from a test_cases.json file using Playwright.

Captures screenshots at every step, records optional video per test case, and
writes a results.json + organised screenshot/video directories.

Usage:
    python scripts/run_tests.py reports/test_cases.json
    python scripts/run_tests.py reports/test_cases.json --output-dir ./reports
    python scripts/run_tests.py reports/test_cases.json --output-dir ./reports --headed
    python scripts/run_tests.py reports/test_cases.json --output-dir ./reports --video
    python scripts/run_tests.py reports/test_cases.json --output-dir ./reports --filter TC-001
    python scripts/run_tests.py reports/test_cases.json --output-dir ./reports --base-url https://staging.example.com
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, Page, BrowserContext
except ImportError:
    print("[ERROR] Playwright not installed. Run: pip install playwright && playwright install chromium", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Action executor
# ---------------------------------------------------------------------------

SCREENSHOT_VIEWPORT = {"width": 1280, "height": 800}

# 逾時常數（毫秒）
NAVIGATION_TIMEOUT_MS = 15_000
INTERACTION_TIMEOUT_MS = 10_000
POST_ACTION_TIMEOUT_MS = 8_000
RETRY_TIMEOUT_MS = 3_000
FILL_PROBE_TIMEOUT_MS = 1_500


# Common HTML element tag names treated as CSS selectors (not text)
_HTML_TAGS = {"body", "html", "head", "main", "header", "footer", "nav",
              "section", "article", "div", "span", "a", "p", "ul", "li",
              "form", "input", "button", "select", "textarea", "table",
              "tr", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6", "img"}

def _selector_or_text(target: str) -> str:
    """Return a robust selector; if target has no CSS-like chars, wrap as text=."""
    if target.startswith(("text=", "role=", "css=", "#", ".", "[", "//", "xpath=")):
        return target.removeprefix("css=")
    # Pure HTML tag name → CSS selector
    if target.lower() in _HTML_TAGS:
        return target
    # Has CSS special chars → treat as CSS selector
    if re.search(r"[#\[\].:>+~()]", target):
        return target
    # Otherwise wrap as text= for natural language matching
    return f"text={target}"


import re


def execute_step(page: Page, step: dict, screenshot_dir: Path, tc_id: str, step_idx: int) -> dict:
    """Execute a single step dict. Returns step result dict."""
    action = step.get("action", "")
    target = step.get("target", "")
    value = step.get("value", "")
    name = step.get("name", f"{tc_id}_step_{step_idx:02d}_{action}")

    result: dict = {
        "index": step_idx,
        "action": action,
        "target": target,
        "value": value,
        "status": "passed",
        "screenshot": None,
        "error": None,
    }

    screenshot_path = screenshot_dir / f"{tc_id}_step_{step_idx:02d}_{action}.png"

    try:
        if action == "goto":
            page.goto(target if target.startswith("http") else target)
            page.wait_for_load_state("networkidle", timeout=15_000)
        elif action == "click":
            locator = page.locator(_selector_or_text(target))
            try:
                locator.first.click(timeout=10_000)
            except Exception:
                # First match may be hidden (e.g. responsive sidebar duplicate);
                # try subsequent visible matches before giving up.
                count = locator.count()
                clicked = False
                for i in range(1, min(count, 5)):
                    try:
                        locator.nth(i).click(timeout=3_000)
                        clicked = True
                        break
                    except Exception:
                        continue
                if not clicked:
                    raise
            page.wait_for_load_state("networkidle", timeout=8_000)
        elif action == "fill":
            # Support multi-selector (comma-separated): try each until one works
            selectors = [s.strip() for s in target.split(",")]
            filled = False
            for sel in selectors:
                try:
                    loc = page.locator(sel).first
                    loc.wait_for(state="visible", timeout=1_500)
                    loc.fill(value, timeout=5_000)
                    filled = True
                    break
                except Exception:
                    continue
            if not filled:
                # Fallback: try original target as-is
                page.locator(_selector_or_text(target)).first.fill(value, timeout=10_000)
        elif action == "select":
            page.locator(_selector_or_text(target)).first.select_option(value, timeout=10_000)
        elif action == "hover":
            page.locator(_selector_or_text(target)).first.hover(timeout=10_000)
        elif action == "wait":
            ms = int(target) if str(target).isdigit() else 1000
            page.wait_for_timeout(ms)
        elif action == "scroll":
            px = int(target) if str(target).isdigit() else 500
            page.evaluate(f"window.scrollBy(0, {px})")
            page.wait_for_timeout(500)
        elif action == "screenshot":
            screenshot_path = screenshot_dir / f"{name}.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            result["screenshot"] = str(screenshot_path.name)
            return result
        elif action == "assert_visible":
            page.locator(_selector_or_text(target)).first.wait_for(state="visible", timeout=10_000)
        elif action == "assert_text":
            actual = page.locator(_selector_or_text(target)).first.inner_text(timeout=10_000)
            assert value.lower() in actual.lower(), f"Expected '{value}' in '{actual}'"
        elif action == "assert_url":
            current = page.url
            assert target in current, f"Expected URL to contain '{target}', got '{current}'"
        elif action == "assert_title":
            current = page.title()
            assert target.lower() in current.lower(), f"Expected title to contain '{target}', got '{current}'"
        else:
            print(f"  [WARN] Unknown action '{action}', skipping", file=sys.stderr)

        # Take screenshot after each successful action
        page.screenshot(path=str(screenshot_path), full_page=True)
        result["screenshot"] = str(screenshot_path.name)

    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        # Failure screenshot
        fail_path = screenshot_dir / f"{tc_id}_step_{step_idx:02d}_FAIL.png"
        try:
            page.screenshot(path=str(fail_path), full_page=True)
            result["screenshot"] = str(fail_path.name)
        except Exception:
            pass

    return result


# ---------------------------------------------------------------------------
# Test case runner
# ---------------------------------------------------------------------------

def run_test_case(
    context: BrowserContext,
    tc: dict,
    base_url: str,
    screenshot_dir: Path,
    video_dir: Path,
    record_video: bool,
) -> dict:
    """Run a single test case; return results dict."""
    tc_id: str = tc.get("id", "TC-???")
    print(f"\n  ▶ {tc_id}: {tc['name']}")

    video_context: BrowserContext | None = None
    page: Page

    if record_video:
        video_context = context.browser.new_context(  # type: ignore[union-attr]
            viewport=SCREENSHOT_VIEWPORT,
            record_video_dir=str(video_dir),
            record_video_size=SCREENSHOT_VIEWPORT,
        )
        page = video_context.new_page()
    else:
        page = context.new_page()

    started = time.time()
    step_results: list[dict] = []
    tc_status = "passed"
    tc_error: str | None = None

    # Prepend base_url to relative goto targets; auto-add goto if missing
    steps = tc.get("steps", [])
    has_goto = any(s.get("action") == "goto" for s in steps)
    resolved_steps = []
    if not has_goto and base_url:
        # Auto-navigate to base_url before the first step
        resolved_steps.append({"action": "goto", "target": base_url})
    for s in steps:
        s2 = dict(s)
        if s2.get("action") == "goto":
            target = s2["target"]
            if target.startswith("http"):
                pass  # Full URL, keep as-is
            elif target.startswith("/"):
                s2["target"] = base_url.rstrip("/") + "/" + target.lstrip("/")
            else:
                # Non-URL, non-path target (e.g. "首頁") → navigate to base_url
                s2["target"] = base_url.rstrip("/") + "/"
        resolved_steps.append(s2)

    interaction_failed = False
    try:
        for idx, step in enumerate(resolved_steps):
            action = step.get("action", "")
            # After an interaction failure, skip further interactions
            # but still execute goto / screenshot / wait steps
            if interaction_failed and action in (
                "click", "fill", "select", "hover",
                "assert_visible", "assert_text", "assert_url", "assert_title",
            ):
                step_results.append({
                    "index": idx, "action": action,
                    "target": step.get("target", ""),
                    "value": step.get("value", ""),
                    "status": "skipped", "screenshot": None,
                    "error": "Skipped: prior step failed",
                })
                print(f"    [{idx+1}/{len(resolved_steps)}] {action} \u2192 SKIPPED (prior failure)")
                continue

            print(f"    [{idx+1}/{len(resolved_steps)}] {step['action']} \u2192 {step.get('target','')[:60]}")
            r = execute_step(page, step, screenshot_dir, tc_id, idx)
            step_results.append(r)
            if r["status"] == "failed":
                tc_status = "failed"
                if not tc_error:
                    tc_error = r["error"]
                print(f"    \u2717 FAILED: {r['error']}")
                if action in ("click", "fill", "select", "hover"):
                    interaction_failed = True
            else:
                print(f"    \u2713 ok")
    except Exception as e:
        tc_status = "failed"
        tc_error = tc_error or traceback.format_exc()
    finally:
        page.close()

    # Save video
    video_file: str | None = None
    if record_video and video_context:
        video_context.close()  # This triggers video finalization
        # Playwright saves video with a random name in video_dir
        videos = sorted(video_dir.glob("*.webm"), key=lambda p: p.stat().st_mtime)
        if videos:
            final_path = video_dir / f"{tc_id}.webm"
            videos[-1].rename(final_path)
            video_file = str(final_path.name)

    duration = round(time.time() - started, 2)
    status_icon = "✅" if tc_status == "passed" else "❌"
    print(f"  {status_icon} {tc_id}: {tc_status.upper()} ({duration}s)")

    return {
        "id": tc_id,
        "name": tc["name"],
        "status": tc_status,
        "duration_seconds": duration,
        "steps": step_results,
        "video": video_file,
        "error": tc_error,
    }


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute browser test cases from test_cases.json using Playwright",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("test_cases", help="Path to test_cases.json (from parse_docx.py)")
    parser.add_argument("--output-dir", "-d", default="./reports", help="Directory for results, screenshots, videos")
    parser.add_argument("--headed", action="store_true", help="Run browser in headed (visible) mode")
    parser.add_argument("--video", action="store_true", help="Record video for each test case (.webm)")
    parser.add_argument("--base-url", default="", help="Override base URL from test_cases.json meta")
    parser.add_argument("--filter", metavar="TC_ID", help="Run only the specified test case ID (e.g. TC-001)")
    parser.add_argument("--timeout", type=int, default=30, help="Default page timeout in seconds (default: 30)")
    args = parser.parse_args()

    # Load test cases
    tc_path = Path(args.test_cases)
    if not tc_path.exists():
        print(f"[ERROR] File not found: {tc_path}", file=sys.stderr)
        sys.exit(1)
    payload = json.loads(tc_path.read_text(encoding="utf-8"))
    meta = payload.get("meta", {})
    test_cases: list[dict] = payload.get("test_cases", [])

    # Apply filter
    if args.filter:
        test_cases = [tc for tc in test_cases if tc.get("id") == args.filter]
        if not test_cases:
            print(f"[ERROR] No test case with id '{args.filter}' found.", file=sys.stderr)
            sys.exit(1)

    base_url = args.base_url or meta.get("base_url", "")
    if not base_url:
        print("[WARN] No base URL set. Relative goto targets may fail.", file=sys.stderr)

    # Prepare output dirs
    out_dir = Path(args.output_dir)
    screenshot_dir = out_dir / "screenshots"
    video_dir = out_dir / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)
    screenshot_dir.mkdir(exist_ok=True)
    if args.video:
        video_dir.mkdir(exist_ok=True)

    started_at = datetime.now(timezone.utc).isoformat()
    print(f"\n🔍 Browser Test Runner")
    print(f"   Suite      : {meta.get('title', 'Unnamed')}")
    print(f"   Base URL   : {base_url or '(none)'}")
    print(f"   Test cases : {len(test_cases)}")
    print(f"   Headed     : {args.headed}")
    print(f"   Video      : {args.video}")
    print(f"   Output dir : {out_dir.resolve()}")
    print(f"{'─'*60}")

    all_results: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        context = browser.new_context(viewport=SCREENSHOT_VIEWPORT)
        context.set_default_timeout(args.timeout * 1000)

        for tc in test_cases:
            result = run_test_case(
                context=context,
                tc=tc,
                base_url=base_url,
                screenshot_dir=screenshot_dir,
                video_dir=video_dir,
                record_video=args.video,
            )
            all_results.append(result)

        context.close()
        browser.close()

    finished_at = datetime.now(timezone.utc).isoformat()

    # Build summary
    passed = sum(1 for r in all_results if r["status"] == "passed")
    failed = sum(1 for r in all_results if r["status"] == "failed")
    skipped = sum(1 for r in all_results if r["status"] == "skipped")
    total_dur = round(sum(r["duration_seconds"] for r in all_results), 2)

    results_payload = {
        "meta": meta,
        "summary": {
            "total": len(all_results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "duration_seconds": total_dur,
            "started_at": started_at,
            "finished_at": finished_at,
        },
        "test_cases": all_results,
    }

    results_path = out_dir / "results.json"
    results_path.write_text(json.dumps(results_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'─'*60}")
    print(f"📊 Results: {passed} passed / {failed} failed / {skipped} skipped  ({total_dur}s)")
    print(f"✅ results.json → {results_path.resolve()}")
    print(f"📸 Screenshots  → {screenshot_dir.resolve()}")
    if args.video:
        print(f"🎥 Videos       → {video_dir.resolve()}")
    print(f"\nNext step: python scripts/generate_report.py {results_path} --output reports/report.html")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
