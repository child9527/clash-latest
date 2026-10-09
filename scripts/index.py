import os
from urllib.parse import quote
from datetime import datetime, timezone, timedelta

# 仓库 raw 根地址
REPO = "child9527/clash-latest"
BRANCH = "main"

# 各目录的 raw 前缀
CLASH_RAW_PREFIX = f"https://raw.githubusercontent.com/{REPO}/refs/heads/{BRANCH}/clash/"
V2RAY_RAW_PREFIX = f"https://raw.githubusercontent.com/{REPO}/refs/heads/{BRANCH}/v2ray/"

# 镜像前缀
GH_PROXY = "https://gh-proxy.com/"


def fetch_files(local_dir, raw_prefix):
    """
    扫描本地目录下的订阅文件，返回 [{name, mirror_url}] 列表
    仅收录 .yaml / .yml / .txt
    """
    if not os.path.exists(local_dir):
        print(f"⚠️ 未找到目录: {local_dir}")
        return []

    allowed_ext = (".yaml", ".yml", ".txt")
    items = []

    for fname in os.listdir(local_dir):
        full_path = os.path.join(local_dir, fname)
        if not os.path.isfile(full_path):
            continue
        if not fname.lower().endswith(allowed_ext):
            continue

        # 对文件名做 URL 编码（防止中文/空格）
        encoded_fname = quote(fname)

        raw_url = f"{raw_prefix}{encoded_fname}"
        mirror_url = f"{GH_PROXY}{raw_url}"

        # 展示名去掉后缀
        display_name = os.path.splitext(fname)[0]

        items.append({
            "name": display_name,
            "mirror_url": mirror_url,
        })

    # 按文件名长度排序
    items.sort(key=lambda x: len(x["name"]))
    return items


def generate_html(clash_items, v2ray_items):
    bj_tz = timezone(timedelta(hours=8))
    now = datetime.now(bj_tz).strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>订阅中心 · Child9527</title>
<style>
body {{
    margin: 0;
    font-family: Arial, sans-serif;
    background: #1e1e1e;
    color: #e0e0e0;
}}

/* 顶部导航栏 */
.navbar {{
    width: 100%;
    background: #2b2b2b;
    border-bottom: 2px solid #4aa3ff;
    padding: 12px 20px;
    display: flex;
    gap: 20px;
    align-items: center;
    box-shadow: 0 0 12px rgba(74,163,255,0.3);
}}

.navbar a {{
    color: #e0e0e0;
    text-decoration: none;
    font-size: 16px;
    padding: 6px 10px;
    border-radius: 6px;
    transition: 0.2s;
}}

.navbar a:hover {{
    background: #4aa3ff;
    color: #000;
}}

/* 内容区块 */
.section {{
    max-width: 1000px;
    margin: 40px auto;
    padding: 0 20px;
}}

.section-title {{
    color: #4aa3ff;
    font-size: 1.3rem;
    margin: 30px 0 15px 0;
    border-left: 4px solid #4aa3ff;
    padding-left: 10px;
}}

/* 紧凑卡片网格 */
.compact-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 12px;
    margin-bottom: 30px;
}}

.source-card {{
    background: #2b2b2b;
    border: 1px solid #4aa3ff;
    box-shadow: 0 0 8px rgba(74,163,255,0.3);
    border-radius: 10px;
    padding: 12px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
}}

.source-name {{
    color: #ffffff;
    font-size: 0.95rem;
    font-weight: bold;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}

.copy-btn {{
    font-size: 0.85rem;
    padding: 6px 12px;
    background: #3a7bd5;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;
    white-space: nowrap;
}}

.copy-btn:hover {{
    background: #2f6bb8;
}}

/* Toast 提示浮窗 */
.toast {{
    position: fixed;
    bottom: 30px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(74, 163, 255, 0.95);
    color: #000;
    font-weight: bold;
    padding: 10px 20px;
    border-radius: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    display: none;
    z-index: 1000;
}}

/* 底部 */
.footer {{
    text-align: center;
    padding: 20px;
    color: #888888;
    margin-top: 40px;
}}
</style>
</head>

<body>

<!-- 导航栏 -->
<div class="navbar">
    <a href="https://child9527.github.io/">首页</a>
    <a href="https://child9527.github.io/software/">软件中心</a>
    <a href="https://child9527.github.io/tvbox/">TVbox订阅</a>
    <a href="https://child9527.github.io/about/">关于本站</a>
</div>

<!-- 内容区块 -->
<div class="section">
<h2>订阅中心</h2>

<!-- 1. Clash 订阅 -->
<div class="section-title">🌐 Clash 订阅</div>
<div class="compact-grid">
"""

    if clash_items:
        for src in clash_items:
            html += f"""
    <div class="source-card">
        <div class="source-name">{src['name']}</div>
        <button class="copy-btn" onclick="copyUrl(this, '{src['mirror_url']}')">复制链接</button>
    </div>
"""
    else:
        html += """
    <div class="source-card">
        <div class="source-name">暂无订阅</div>
    </div>
"""

    html += """</div>

<!-- 2. V2ray 订阅 -->
<div class="section-title">🚀 V2ray 订阅</div>
<div class="compact-grid">
"""

    if v2ray_items:
        for src in v2ray_items:
            html += f"""
    <div class="source-card">
        <div class="source-name">{src['name']}</div>
        <button class="copy-btn" onclick="copyUrl(this, '{src['mirror_url']}')">复制链接</button>
    </div>
"""
    else:
        html += """
    <div class="source-card">
        <div class="source-name">暂无订阅</div>
    </div>
"""

    html += f"""</div>

<div class="footer">
    自动生成时间：{now}
</div>
</div>

<div id="toast" class="toast">链接已成功复制到剪贴板！</div>

<script>
function copyUrl(btn, url) {{
    navigator.clipboard.writeText(url).then(() => {{
        showToast("已复制：" + url);
        const originalText = btn.innerText;
        btn.innerText = "已复制";
        btn.style.background = "#28a745";
        setTimeout(() => {{
            btn.innerText = originalText;
            btn.style.background = "#3a7bd5";
        }}, 2000);
    }}).catch(err => {{
        console.error("复制失败:", err);
    }});
}}

function showToast(msg) {{
    const toast = document.getElementById("toast");
    toast.innerText = msg;
    toast.style.display = "block";
    setTimeout(() => {{
        toast.style.display = "none";
    }}, 2000);
}}
</script>

</body>
</html>
"""

    return html


if __name__ == "__main__":
    clash_items = fetch_files("clash", CLASH_RAW_PREFIX)
    v2ray_items = fetch_files("v2ray", V2RAY_RAW_PREFIX)

    html = generate_html(clash_items, v2ray_items)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html 生成成功！")
