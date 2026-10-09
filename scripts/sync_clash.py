#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone, timedelta

import requests
import yaml

# ---------- 配置 ----------
TARGETS_FILE = os.path.join("task", "targets.json")
OUTPUT_DIR = "clash"      # 清洗后的 yaml 放仓库 clash 目录
TIMEOUT = 30              # 请求超时（秒）
UA = "okhttp/4.12.0"
TZ = timezone(timedelta(hours=8))

# 临时空间：优先用环境变量（GitHub Actions runner.temp），否则用系统临时目录
TMP_DIR = os.environ.get("RUNNER_TEMP") or tempfile.gettempdir()


def log(msg: str):
    print(f"[{datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def load_targets(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_targets(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def md5_of_file(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_to_temp(url: str, name: str):
    """
    下载到临时空间。
    返回 (status, tmp_path, error_msg)
    status: 'ok' | 'fail' | 'lost'
    """
    tmp_path = os.path.join(TMP_DIR, f"sub_{name}.tmp")
    try:
        with requests.get(url, timeout=TIMEOUT, headers={"User-Agent": UA}, stream=True) as resp:
            if resp.status_code == 404:
                return "lost", None, "http 404"
            if resp.status_code != 200:
                return "fail", None, f"http {resp.status_code}"

            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    except requests.exceptions.Timeout:
        return "fail", None, "timeout"
    except requests.exceptions.RequestException as e:
        return "fail", None, str(e)

    return "ok", tmp_path, ""


def clean_subscription_from_file(path: str) -> dict:
    """
    读取临时文件，清洗成只保留 proxies 的 dict。
    支持 clash yaml 与 base64 编码订阅。
    """
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read().strip()

    data = None
    try:
        data = yaml.safe_load(text)
    except Exception:
        data = None

    if not isinstance(data, dict):
        try:
            decoded = base64.b64decode(text + "=" * (-len(text) % 4)).decode("utf-8", "ignore")
            data = yaml.safe_load(decoded)
        except Exception:
            data = None

    if not isinstance(data, dict):
        raise ValueError("无法解析订阅内容为有效的 YAML")

    proxies = data.get("proxies")
    if not proxies:
        raise ValueError("订阅中未找到 proxies 字段")

    return {"proxies": proxies}


def write_yaml(name: str, data: dict) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"{name}.yaml")
    with open(filepath, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )
    return filepath


def main():
    if not os.path.isfile(TARGETS_FILE):
        log(f"找不到 {TARGETS_FILE}")
        sys.exit(1)

    targets = load_targets(TARGETS_FILE)

    # ---------- 第一阶段：全部下载到临时空间 + 算 md5 ----------
    results = []          # [(item, status, tmp_path, remote_md5, err)]
    can_early_exit = True  # md5 全一致 且 status 全 ok 才为 True

    for item in targets:
        name = (item.get("name") or "").strip()
        url = (item.get("url") or "").strip()
        old_md5 = (item.get("md5") or "").strip().lower()
        old_status = (item.get("status") or "").strip().lower()

        if not name or not url:
            log(f"跳过无效条目: {item}")
            continue

        log(f"检查: {name} -> {url}")
        status, tmp_path, err = fetch_to_temp(url, name)

        if status != "ok":
            log(f"  获取失败: {status} ({err})")
            results.append((item, status, None, None, err))
            can_early_exit = False
            continue

        remote_md5 = md5_of_file(tmp_path)
        results.append((item, "ok", tmp_path, remote_md5, ""))

        if remote_md5 != old_md5:
            log(f"  MD5 变化: {old_md5 or '空'} -> {remote_md5}")
            can_early_exit = False
        else:
            log(f"  MD5 一致: {remote_md5}")

        if old_status != "ok":
            can_early_exit = False

    # ---------- 提前退出：md5 全一致 且 status 全 ok ----------
    if can_early_exit:
        log("所有订阅 MD5 未变化且状态均为 ok，退出")
        sys.exit(0)

    # ---------- 第二阶段：处理需要变更的条目 ----------
    changed = False

    for item, status, tmp_path, remote_md5, err in results:
        name = (item.get("name") or "").strip()
        old_md5 = (item.get("md5") or "").strip().lower()
        old_status = (item.get("status") or "").strip().lower()

        # 失败：只刷新 status
        if status != "ok":
            if old_status != status:
                item["status"] = status
                changed = True
                log(f"{name}: status -> {status}")
            continue

        # 成功且 md5 一致
        if remote_md5 == old_md5:
            if old_status != "ok":
                item["status"] = "ok"
                changed = True
                log(f"{name}: status -> ok（内容未变）")
            else:
                log(f"{name}: 无变化，跳过")
            continue

        # 成功且 md5 变化：清洗 + 写 yaml
        log(f"{name}: 更新中")
        try:
            cleaned = clean_subscription_from_file(tmp_path)
            filepath = write_yaml(name, cleaned)
            log(f"  已生成: {filepath}")
        except Exception as e:
            log(f"  处理失败: {e}")
            if old_status != "fail":
                item["status"] = "fail"
                changed = True
            continue

        item["md5"] = remote_md5
        item["last_modified"] = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
        item["status"] = "ok"
        changed = True

    if changed:
        save_targets(TARGETS_FILE, targets)
        log("targets.json 已更新")
    else:
        log("targets.json 无需更新")

    log("完成")


if __name__ == "__main__":
    main()
