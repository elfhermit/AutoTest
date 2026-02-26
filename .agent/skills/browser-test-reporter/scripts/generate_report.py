#!/usr/bin/env python3
"""
generate_report.py — Build a self-contained one-page HTML test report from results.json.

All screenshots are base64-inlined so the file can be shared as a single .html.
Videos are referenced by relative path (or absolute path if in the same directory).

Usage:
    python scripts/generate_report.py reports/results.json
    python scripts/generate_report.py reports/results.json --output reports/report.html
    python scripts/generate_report.py reports/results.json --output reports/report.html \
        --screenshots-dir ./reports/screenshots \
        --videos-dir ./reports/videos
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# HTML template (self-contained; no external CDN dependencies)
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{report_title} — Test Report</title>
<style>
  /* ── Reset & Base ─────────────────────────────────────────── */
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f5f6fa; color: #1a1a2e; font-size: 14px; line-height: 1.6; }}
  a {{ color: inherit; text-decoration: none; }}

  /* ── Layout ──────────────────────────────────────────────── */
  .container {{ max-width: 1100px; margin: 0 auto; padding: 24px 16px 60px; }}
  
  /* ── Header ──────────────────────────────────────────────── */
  .header {{ background: #1a1a2e; color: #fff; padding: 32px 40px; border-radius: 12px;
             margin-bottom: 28px; display: flex; justify-content: space-between; align-items: flex-start; }}
  .header h1 {{ font-size: 24px; font-weight: 700; letter-spacing: -0.5px; }}
  .header .meta {{ font-size: 12px; opacity: .75; margin-top: 6px; }}
  .header .print-btn {{ background: rgba(255,255,255,.15); border: 1px solid rgba(255,255,255,.3);
                         color: #fff; padding: 8px 18px; border-radius: 8px; cursor: pointer;
                         font-size: 13px; white-space: nowrap; margin-left: 24px; }}
  .header .print-btn:hover {{ background: rgba(255,255,255,.25); }}

  /* ── Summary Banners ─────────────────────────────────────── */
  .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
              gap: 14px; margin-bottom: 28px; }}
  .stat-card {{ background: #fff; border-radius: 10px; padding: 20px 24px;
                box-shadow: 0 1px 4px rgba(0,0,0,.07); text-align: center; }}
  .stat-card .num {{ font-size: 36px; font-weight: 700; line-height: 1; }}
  .stat-card .label {{ font-size: 12px; color: #666; margin-top: 6px; text-transform: uppercase; letter-spacing: .5px; }}
  .stat-card.pass .num {{ color: #16a34a; }}
  .stat-card.fail .num {{ color: #dc2626; }}
  .stat-card.skip .num {{ color: #9ca3af; }}
  .stat-card.total .num {{ color: #1a1a2e; }}
  .stat-card.duration .num {{ font-size: 26px; }}

  /* ── Pass-rate Bar ───────────────────────────────────────── */
  .pass-bar-wrap {{ background: #fff; border-radius: 10px; padding: 20px 24px;
                   box-shadow: 0 1px 4px rgba(0,0,0,.07); margin-bottom: 28px; }}
  .pass-bar-wrap .pb-label {{ font-size: 13px; color: #444; margin-bottom: 8px; }}
  .pass-bar {{ height: 18px; background: #e5e7eb; border-radius: 99px; overflow: hidden; }}
  .pass-bar .fill {{ height: 100%; border-radius: 99px;
                     background: linear-gradient(90deg, #16a34a, #4ade80); transition: width .5s; }}

  /* ── Environment Card ────────────────────────────────────── */
  .env-card {{ background: #fff; border-radius: 10px; padding: 20px 24px;
               box-shadow: 0 1px 4px rgba(0,0,0,.07); margin-bottom: 28px; }}
  .env-card h2 {{ font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 12px;
                  padding-bottom: 8px; border-bottom: 1px solid #f0f0f0; }}
  .env-table {{ display: grid; grid-template-columns: 140px 1fr; gap: 4px 16px; }}
  .env-table .k {{ color: #9ca3af; font-size: 12px; padding: 3px 0; }}
  .env-table .v {{ font-weight: 500; font-size: 13px; padding: 3px 0; word-break: break-all; }}

  /* ── Test Case Cards ─────────────────────────────────────── */
  .section-title {{ font-size: 16px; font-weight: 700; color: #1a1a2e; margin: 0 0 16px;
                    display: flex; align-items: center; gap: 10px; }}
  .section-title .badge {{ font-size: 11px; font-weight: 600; padding: 2px 10px;
                            border-radius: 99px; background:#e5e7eb; color:#666; }}
  .tc-card {{ background: #fff; border-radius: 10px; margin-bottom: 16px;
              box-shadow: 0 1px 4px rgba(0,0,0,.07); overflow: hidden; }}
  .tc-card.passed {{ border-left: 4px solid #16a34a; }}
  .tc-card.failed {{ border-left: 4px solid #dc2626; }}
  .tc-card.skipped {{ border-left: 4px solid #9ca3af; }}
  .tc-header {{ padding: 16px 20px; display: flex; align-items: center; gap: 14px;
                cursor: pointer; user-select: none; }}
  .tc-header:hover {{ background: #fafafa; }}
  .tc-status {{ font-size: 12px; font-weight: 700; padding: 3px 12px; border-radius: 99px; white-space: nowrap; }}
  .passed .tc-status {{ background: #dcfce7; color: #16a34a; }}
  .failed .tc-status {{ background: #fee2e2; color: #dc2626; }}
  .skipped .tc-status {{ background: #f3f4f6; color: #9ca3af; }}
  .tc-id {{ font-size: 11px; color: #9ca3af; font-family: monospace; }}
  .tc-name {{ font-weight: 600; flex: 1; }}
  .tc-dur {{ font-size: 12px; color: #9ca3af; white-space: nowrap; }}
  .tc-chevron {{ color: #9ca3af; font-size: 16px; transition: transform .2s; }}
  .tc-card.open .tc-chevron {{ transform: rotate(90deg); }}
  .tc-body {{ padding: 0 20px 20px; display: none; }}
  .tc-card.open .tc-body {{ display: block; }}

  /* ── Error block ─────────────────────────────────────────── */
  .tc-error {{ background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;
               padding: 12px 16px; margin-bottom: 14px; font-family: monospace;
               font-size: 12px; color: #991b1b; white-space: pre-wrap; word-break: break-word; }}

  /* ── Steps table ─────────────────────────────────────────── */
  .steps-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  .steps-table th {{ text-align: left; padding: 8px 12px; background: #f9fafb;
                      font-size: 11px; text-transform: uppercase; letter-spacing: .5px;
                      color: #6b7280; border-bottom: 1px solid #e5e7eb; }}
  .steps-table td {{ padding: 9px 12px; border-bottom: 1px solid #f3f4f6; vertical-align: top; }}
  .steps-table tr:last-child td {{ border-bottom: none; }}
  .step-pass {{ color: #16a34a; font-weight: 700; }}
  .step-fail {{ color: #dc2626; font-weight: 700; }}
  .step-action {{ font-family: monospace; background: #f3f4f6; border-radius: 4px;
                   padding: 1px 6px; font-size: 12px; }}
  .step-ss {{ cursor: pointer; color: #6366f1; text-decoration: underline; font-size: 12px; }}
  .step-error {{ color: #dc2626; font-size: 12px; }}

  /* ── Video ───────────────────────────────────────────────── */
  .video-wrap {{ margin-top: 14px; }}
  .video-wrap label {{ font-size: 12px; font-weight: 600; color: #374151; display: block; margin-bottom: 6px; }}
  .video-wrap video {{ width: 100%; max-width: 720px; border-radius: 8px; 
                        box-shadow: 0 2px 8px rgba(0,0,0,.15); display: block; }}

  /* ── Lightbox ────────────────────────────────────────────── */
  #lightbox {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,.85);
               z-index: 9999; align-items: center; justify-content: center; }}
  #lightbox.active {{ display: flex; }}
  #lightbox img {{ max-width: 92vw; max-height: 92vh; border-radius: 8px;
                    box-shadow: 0 8px 32px rgba(0,0,0,.5); }}
  #lightbox-close {{ position: fixed; top: 20px; right: 24px; color: #fff; font-size: 32px;
                      cursor: pointer; line-height: 1; }}

  /* ── Fail Summary ────────────────────────────────────────── */
  .fail-summary {{ background: #fff; border-radius: 10px; padding: 20px 24px;
                   box-shadow: 0 1px 4px rgba(0,0,0,.07); margin-bottom: 28px;
                   border-left: 4px solid #dc2626; }}
  .fail-summary h2 {{ font-size: 14px; font-weight: 600; color: #dc2626; margin-bottom: 10px; }}
  .fail-summary li {{ margin-left: 18px; margin-bottom: 4px; font-size: 13px; }}

  /* ── Print ───────────────────────────────────────────────── */
  @media print {{
    .print-btn, #lightbox {{ display: none !important; }}
    .tc-body {{ display: block !important; }}
    body {{ background: #fff; }}
    .tc-card {{ box-shadow: none; border: 1px solid #e5e7eb; page-break-inside: avoid; }}
  }}
</style>
</head>
<body>
<div id="lightbox"><span id="lightbox-close" onclick="closeLightbox()">✕</span><img id="lb-img" src="" alt=""/></div>

<div class="container">
  <!-- Header -->
  <div class="header">
    <div>
      <h1>🧪 {report_title}</h1>
      <div class="meta">
        {env_meta_line}
      </div>
    </div>
    <button class="print-btn" onclick="window.print()">🖨 列印 / 儲存 PDF</button>
  </div>

  <!-- Summary stats -->
  <div class="summary">
    <div class="stat-card total"><div class="num">{total}</div><div class="label">總案例數</div></div>
    <div class="stat-card pass"><div class="num">{passed}</div><div class="label">通過</div></div>
    <div class="stat-card fail"><div class="num">{failed}</div><div class="label">失敗</div></div>
    <div class="stat-card skip"><div class="num">{skipped}</div><div class="label">略過</div></div>
    <div class="stat-card duration"><div class="num">{duration}s</div><div class="label">執行時間</div></div>
  </div>

  <!-- Pass-rate bar -->
  <div class="pass-bar-wrap">
    <div class="pb-label">通過率 {pass_rate}%</div>
    <div class="pass-bar"><div class="fill" style="width:{pass_rate}%"></div></div>
  </div>

  {fail_summary_block}

  <!-- Environment -->
  <div class="env-card">
    <h2>執行環境</h2>
    <div class="env-table">
      {env_rows}
    </div>
  </div>

  <!-- Test cases -->
  <div class="section-title">測試案例 <span class="badge">{total} 項</span></div>
  {tc_cards}
</div>

<script>
function toggleCard(el) {{
  el.closest('.tc-card').classList.toggle('open');
}}
function openLightbox(src) {{
  document.getElementById('lb-img').src = src;
  document.getElementById('lightbox').classList.add('active');
}}
function closeLightbox() {{
  document.getElementById('lightbox').classList.remove('active');
}}
document.getElementById('lightbox').addEventListener('click', function(e) {{
  if (e.target === this) closeLightbox();
}});
document.addEventListener('keydown', function(e) {{
  if (e.key === 'Escape') closeLightbox();
}});
// Auto-expand failed cards
document.querySelectorAll('.tc-card.failed').forEach(function(c) {{ c.classList.add('open'); }});
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def encode_image(path: Path) -> str | None:
    """Return base64 data-URI for an image, or None if file not found."""
    if not path or not path.exists():
        return None
    ext = path.suffix.lower().lstrip(".")
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}.get(ext, "image/png")
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{data}"


def escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_tc_card(tc: dict, screenshot_dir: Path, video_dir: Path | None) -> str:
    tc_id = escape_html(tc.get("id", ""))
    tc_name = escape_html(tc.get("name", ""))
    status: str = tc.get("status", "skipped")
    dur = tc.get("duration_seconds", 0)
    error = tc.get("error") or ""

    # Steps table
    step_rows = ""
    for step in tc.get("steps", []):
        s_status = step.get("status", "passed")
        s_action = escape_html(step.get("action", ""))
        s_target = escape_html(str(step.get("target", "")))
        s_value = escape_html(str(step.get("value", "")))
        s_err = escape_html(step.get("error") or "")
        s_ss_name = step.get("screenshot")

        status_cell = f'<span class="step-pass">✓</span>' if s_status == "passed" else f'<span class="step-fail">✗</span>'
        ss_cell = ""
        if s_ss_name:
            img_path = screenshot_dir / s_ss_name
            data_uri = encode_image(img_path)
            if data_uri:
                ss_cell = f'<span class="step-ss" onclick="openLightbox(\'{data_uri}\')">📷 截圖</span>'
            else:
                ss_cell = f'<span style="color:#9ca3af">📷 {escape_html(s_ss_name)}</span>'
        err_cell = f'<br/><span class="step-error">{s_err}</span>' if s_err else ""
        target_display = s_target[:80] + ("…" if len(s_target) > 80 else "")
        step_rows += (
            f"<tr>"
            f"<td>{status_cell}</td>"
            f"<td><span class='step-action'>{s_action}</span></td>"
            f"<td>{target_display}{(' → ' + s_value) if s_value else ''}{err_cell}</td>"
            f"<td>{ss_cell}</td>"
            f"</tr>"
        )

    steps_table = (
        "<table class='steps-table'>"
        "<thead><tr><th></th><th>動作</th><th>對象 / 數值</th><th>截圖</th></tr></thead>"
        f"<tbody>{step_rows}</tbody></table>"
    ) if step_rows else "<p style='color:#9ca3af;font-size:13px'>（無步驟記錄）</p>"

    # Error block
    error_block = f'<div class="tc-error">{escape_html(error)}</div>' if error else ""

    # Video
    video_block = ""
    video_file = tc.get("video")
    if video_file and video_dir:
        video_path = video_dir / video_file
        if video_path.exists():
            video_block = (
                "<div class='video-wrap'>"
                "<label>🎥 測試錄影</label>"
                f'<video controls src="{video_path.resolve().as_uri()}"></video>'
                "</div>"
            )

    return (
        f'<div class="tc-card {status}">'
        f'<div class="tc-header" onclick="toggleCard(this)">'
        f'<span class="tc-status">{status.upper()}</span>'
        f'<span class="tc-id">{tc_id}</span>'
        f'<span class="tc-name">{tc_name}</span>'
        f'<span class="tc-dur">{dur}s</span>'
        f'<span class="tc-chevron">▶</span>'
        f'</div>'
        f'<div class="tc-body">'
        f'{error_block}'
        f'{steps_table}'
        f'{video_block}'
        f'</div>'
        f'</div>'
    )


def build_fail_summary(test_cases: list[dict]) -> str:
    failed = [tc for tc in test_cases if tc.get("status") == "failed"]
    if not failed:
        return ""
    items = "".join(f'<li><strong>{escape_html(tc["id"])}</strong> — {escape_html(tc["name"])}</li>' for tc in failed)
    return (
        '<div class="fail-summary">'
        '<h2>❌ 失敗案例清單</h2>'
        f'<ul>{items}</ul>'
        '</div>'
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a self-contained one-page HTML test report from results.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("results", help="Path to results.json (from run_tests.py)")
    parser.add_argument("--output", "-o", default="reports/report.html", help="Output HTML file (default: reports/report.html)")
    parser.add_argument("--screenshots-dir", default="", help="Directory containing screenshot files")
    parser.add_argument("--videos-dir", default="", help="Directory containing video files")
    args = parser.parse_args()

    results_path = Path(args.results)
    if not results_path.exists():
        print(f"[ERROR] File not found: {results_path}", file=sys.stderr)
        sys.exit(1)

    payload = json.loads(results_path.read_text(encoding="utf-8"))
    meta: dict = payload.get("meta", {})
    summary: dict = payload.get("summary", {})
    test_cases: list[dict] = payload.get("test_cases", [])

    # Resolve directories
    def resolve_dir(arg: str, fallback: str) -> Path | None:
        p = Path(arg) if arg else results_path.parent / fallback
        return p if p.exists() else None

    screenshot_dir = resolve_dir(args.screenshots_dir, "screenshots") or Path(".")
    video_dir = resolve_dir(args.videos_dir, "videos")

    total = summary.get("total", len(test_cases))
    passed = summary.get("passed", sum(1 for tc in test_cases if tc.get("status") == "passed"))
    failed = summary.get("failed", sum(1 for tc in test_cases if tc.get("status") == "failed"))
    skipped = summary.get("skipped", 0)
    duration = summary.get("duration_seconds", 0)
    started_at = summary.get("started_at", "")
    pass_rate = round(passed / total * 100) if total else 0

    report_title = escape_html(meta.get("title", "Test Report"))
    env_meta_line = " · ".join(filter(None, [
        meta.get("environment", ""),
        meta.get("base_url", ""),
        f"執行時間 {started_at[:19].replace('T', ' ')} UTC" if started_at else "",
        f"測試人員: {meta.get('tested_by', '')}" if meta.get("tested_by") else "",
    ]))

    env_rows = ""
    env_fields = [
        ("Base URL", meta.get("base_url", "—")),
        ("環境", meta.get("environment", "—")),
        ("測試人員", meta.get("tested_by", "—")),
        ("執行日期", meta.get("date", started_at[:10] if started_at else "—")),
        ("開始時間", started_at[:19].replace("T", " ") + " UTC" if started_at else "—"),
    ]
    for k, v in env_fields:
        env_rows += f'<span class="k">{k}</span><span class="v">{escape_html(str(v))}</span>'

    tc_cards = "".join(build_tc_card(tc, screenshot_dir, video_dir) for tc in test_cases)
    fail_summary_block = build_fail_summary(test_cases)

    html = HTML_TEMPLATE.format(
        report_title=report_title,
        env_meta_line=escape_html(env_meta_line),
        total=total, passed=passed, failed=failed, skipped=skipped,
        duration=duration, pass_rate=pass_rate,
        env_rows=env_rows,
        tc_cards=tc_cards,
        fail_summary_block=fail_summary_block,
    )

    out_path = Path(args.output)
    out_path.write_text(html, encoding="utf-8")
    print(f"✅ Report generated → {out_path.resolve()}")
    print(f"   {total} cases: {passed} passed / {failed} failed / {skipped} skipped")
    print(f"\nNext step: python scripts/update_docx.py docs/input.docx {results_path} --output reports/report_input.docx")


if __name__ == "__main__":
    main()
