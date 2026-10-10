#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from urllib.parse import quote
from datetime import datetime, timezone, timedelta

from renderer import render
from sections import (
    section_copy_cards,
    section_copy_cards_wide,
)


# ============================================================
# 配置
# ============================================================

# 仓库 raw 根地址
REPO = "child9527/clash-latest"
BRANCH = "main"

# 各目录的 raw 前缀
CLASH_RAW_PREFIX = f"https://raw.githubusercontent.com/{REPO}/refs/heads/{BRANCH}/clash/"
V2RAY_RAW_PREFIX = f"https://raw.githubusercontent.com/{REPO}/refs/heads/{BRANCH}/v2ray/"

# 镜像前缀
GH_PROXY = "https://gh-proxy.com/"

# 要内嵌到 HTML 的规则文本路径
EXTENSION_JS_FILE = "scripts/extension_js.txt"

# 输出文件
OUTPUT = "index.html"


# ============================================================
# 数据获取
# ============================================================

def fetch_files(local_dir, raw_prefix):
    """
    扫描本地目录下的订阅文件，返回 [{name, url_literal}] 列表。
    仅收录 .yaml / .yml / .txt。
    url_literal 已经过 json.dumps，可直接塞进 JS。
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
            "url_literal": json.dumps(mirror_url, ensure_ascii=False),
        })

    # 按文件名长度排序
    items.sort(key=lambda x: len(x["name"]))
    return items


def load_extension_js(path):
    """读取要内嵌的规则文本，失败时返回空字符串"""
    if not os.path.isfile(path):
        print(f"⚠️ 未找到规则文件: {path}")
        return ""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


# ============================================================
# 组装 sections
# ============================================================

def build_sections():
    """
    组装所有板块。

    以后新增板块，只改这里：
        sections.append(section_xxx("板块标题", 数据))
    """
    sections = []

    # 板块 1：Clash 订阅
    clash_items = fetch_files("clash", CLASH_RAW_PREFIX)
    sections.append(section_copy_cards("🌐 Clash 订阅", clash_items))

    # 板块 2：V2ray 订阅
    v2ray_items = fetch_files("v2ray", V2RAY_RAW_PREFIX)
    sections.append(section_copy_cards("🚀 V2ray 订阅", v2ray_items))

    # 板块 3：复制规则文本（Clash Verge Rev 全局扩展脚本）
    extension_js_text = load_extension_js(EXTENSION_JS_FILE)
    if extension_js_text:
        sections.append(section_copy_cards_wide("📋 规则及配置", [
            {
                "name": "Clash Verge Rev全局扩展脚本",
                "js_var": "EXTENSION_JS_TEXT",
                "content_literal": json.dumps(extension_js_text, ensure_ascii=False),
            },
        ]))
    else:
        print("ℹ️ extension_js.txt 不存在或为空，跳过规则板块")

    return sections


# ============================================================
# 主入口
# ============================================================

def main():
    bj_tz = timezone(timedelta(hours=8))
    now = datetime.now(bj_tz).strftime("%Y-%m-%d %H:%M:%S")

    sections = build_sections()

    html = render(
    "base.html.j2",
    sections=sections,
    now=now,
    page_title="科学订阅",
    )

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"index.html 生成成功！共 {len(sections)} 个板块。")


if __name__ == "__main__":
    main()
