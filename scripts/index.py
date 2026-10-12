#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from urllib.parse import quote
from datetime import datetime, timezone, timedelta
from jinja2 import Environment, FileSystemLoader, select_autoescape


# ============================================================
# 模板渲染
# ============================================================

# 模板目录（相对于项目根目录）
TEMPLATE_DIR = "templates"


def render(template_name, **context):
    """
    渲染指定模板。

    参数：
        template_name: 模板文件路径（相对 templates/ 目录），如 "base.html.j2"
        **context:     传给模板的变量

    返回：
        渲染后的 HTML 字符串
    """
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,      # 块标签后的第一个换行符自动去掉
        lstrip_blocks=True,    # 块标签前的空白自动去掉
    )
    template = env.get_template(template_name)
    return template.render(**context)


# ============================================================
# 板块构造
# ============================================================

def section_software_list(title, items):
    """
    软件卡片列表板块（带筛选按钮）。

    参数：
        title: 板块标题
        items: 软件列表，每项结构：
            {
                "name":        展示名,
                "version":     版本号,
                "url":         原始下载链接,
                "file_size":   文件大小（字节）,
                "file_size_text": 格式化后的大小（如 "12.3 MB"）,
                "icon":        图标 URL（可为空）,
                "type":        分类（如 "Win64"、"Android"）,
                "description": 简介,
                "mirrors":     [(镜像名, 镜像链接), ...],
            }

    返回：
        {
            "title":      标题,
            "type":       "software_list",
            "items":      items,
            "types":      去重后的分类列表（按出现顺序）,
            "first_type": 第一个分类（用于默认显示）,
        }
    """
    types = list(dict.fromkeys([it["type"] for it in items if it.get("type")]))
    return {
        "title": title,
        "type": "software_list",
        "items": items,
        "types": types,
        "first_type": types[0] if types else None,
    }


def section_copy_cards(title, items):
    """
    复制型卡片（网格）板块。

    参数：
        title: 板块标题
        items: 卡片列表，每项结构：
            {
                "name":        展示名,
                "url_literal": 已经过 json.dumps 的 JS 字符串字面量,
            }

    返回：
        {
            "title": 标题,
            "type":  "copy_cards",
            "items": items,
        }
    """
    return {
        "title": title,
        "type": "copy_cards",
        "items": items,
    }


def section_copy_cards_wide(title, items):
    """
    复制型卡片（单行大卡片）板块，支持多张。

    items 里每项结构：
        {
            "name":            展示名,
            "js_var":          JS 变量名（英文，全局唯一，如 "EXTENSION_JS_TEXT"）,
            "content_literal": 已经过 json.dumps 的 JS 字符串字面量,
        }

    示例：
        section_copy_cards_wide("📋 规则及配置", [
            {
                "name": "Clash Verge Rev全局扩展覆写脚本",
                "js_var": "EXTENSION_JS_TEXT",
                "content_literal": json.dumps(js_text, ensure_ascii=False),
            },
            {
                "name": "Clash 配置模板",
                "js_var": "CLASH_CONFIG_TEXT",
                "content_literal": json.dumps(config_text, ensure_ascii=False),
            },
        ])
    """
    return {
        "title": title,
        "type": "copy_cards_wide",
        "items": items,
    }


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
