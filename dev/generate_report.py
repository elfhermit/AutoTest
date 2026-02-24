import os
import re
import glob
import base64
import datetime
import markdown # 需確保環境有安裝 pip install markdown

# 設定路徑
ARTIFACTS_DIR = os.path.join(".agent", "test_artifacts")
MD_FILE = os.path.join(ARTIFACTS_DIR, "walkthrough.md")
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(REPORTS_DIR, f"Acceptance_Report_{TIMESTAMP}.html")

# MIME type 對照表
MIME_MAP = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.webp': 'image/webp',
    '.gif': 'image/gif',
}

def image_to_base64(image_path):
    """將圖片轉換為 Base64 編碼字串"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        print(f"警告：無法讀取圖片 {image_path}，錯誤：{e}")
        return None

def get_mime_type(filepath):
    """根據副檔名取得 MIME type"""
    ext = os.path.splitext(filepath)[1].lower()
    return MIME_MAP.get(ext, 'image/png')

def generate_html():
    if not os.path.exists(MD_FILE):
        print(f"錯誤：找不到 {MD_FILE}")
        return

    # 1. 讀取 Markdown 內容
    with open(MD_FILE, "r", encoding="utf-8") as f:
        md_text = f.read()

    # 2. 轉換 Markdown 為 HTML
    html_content = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])

    # 3. 尋找並嵌入圖片 (使用正規表達式匹配 img src 屬性)
    # 支援 .png, .jpg, .jpeg, .webp, .gif
    supported_exts = ['*.png', '*.jpg', '*.jpeg', '*.webp', '*.gif']
    image_files = []
    for ext in supported_exts:
        image_files.extend(glob.glob(os.path.join(ARTIFACTS_DIR, ext)))
    
    for img_path in image_files:
        filename = os.path.basename(img_path)
        b64_str = image_to_base64(img_path)
        if b64_str is None:
            continue
        mime = get_mime_type(img_path)
        # 使用正規表達式匹配 src 屬性中包含該檔名的所有引用
        pattern = re.compile(
            r'src="[^"]*?' + re.escape(filename) + r'"',
            re.IGNORECASE
        )
        html_content = pattern.sub(
            f'src="data:{mime};base64,{b64_str}"',
            html_content
        )
        # 同時處理直接以檔名作為 src 的情況（Markdown 轉換可能產生）
        if filename in html_content:
            html_content = html_content.replace(filename, f"data:{mime};base64,{b64_str}")

    # 4. 尋找影片並附加在底部 (Markdown 通常不直接支援影片嵌入，我們手動加)
    video_section = ""
    video_files = glob.glob(os.path.join(ARTIFACTS_DIR, "*.webm")) + glob.glob(os.path.join(ARTIFACTS_DIR, "*.mp4"))
    
    if video_files:
        video_section += "<h2>🎥 測試錄影紀錄</h2>"
        for vid_path in video_files:
            with open(vid_path, "rb") as v:
                b64_vid = base64.b64encode(v.read()).decode('utf-8')
                mime = "video/webm" if vid_path.endswith(".webm") else "video/mp4"
                video_section += f'''
                <div class="video-container">
                    <p><strong>{os.path.basename(vid_path)}</strong></p>
                    <video controls width="100%">
                        <source src="data:{mime};base64,{b64_vid}" type="{mime}">
                        您的瀏覽器不支援影片標籤。
                    </video>
                </div>
                '''

    # 5. 組合最終 HTML (包含 CSS 美化)
    final_html = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>自動化驗收報告</title>
        <style>
            body {{ font-family: "Microsoft JhengHei", sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; color: #333; }}
            h1, h2, h3 {{ color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 0.5rem; }}
            code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
            pre {{ background: #282c34; color: #abb2bf; padding: 1rem; border-radius: 5px; overflow-x: auto; }}
            img {{ max-width: 100%; border: 1px solid #ddd; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 1rem 0; }}
            .status-pass {{ color: green; font-weight: bold; }}
            .video-container {{ margin-bottom: 2rem; background: #f9f9f9; padding: 1rem; border-radius: 8px; }}
            .timestamp {{ color: #888; font-size: 0.9rem; }}
        </style>
    </head>
    <body>
        <h1>🔍 自動化功能驗收報告</h1>
        <p class="timestamp">報告生成時間：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <hr>
        {html_content}
        {video_section}
    </body>
    </html>
    """

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)
    print(f"報告已生成：{OUTPUT_FILE}")

if __name__ == "__main__":
    generate_html()