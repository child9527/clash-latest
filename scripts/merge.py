import requests
import yaml
import re
import time
import os
from datetime import datetime

# 1. 定义本地镜像文件列表 (都在仓库根目录)
LOCAL_SOURCES = [
    "free-nodes.yml",
    "tglaoshiji.yml"
]

# 2. 剩下的远程订阅源 (移除了本地已有的两个)
REMOTE_SOURCES = [
    "https://raw.githubusercontent.com/tugepaopao/tugepaopao.github.io/master/free.yaml",
    "https://raw.githubusercontent.com/vless-free/free/main/clash.yaml",
    "https://raw.githubusercontent.com/snakem982/proxypool/main/source/clash-meta.yaml",
    "https://raw.githubusercontent.com/snakem982/proxypool/main/source/clash-meta-2.yaml",
    "https://raw.githubusercontent.com/free18/v2ray/main/source/c.yaml",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity.yml"
]

# 国家关键词与表情包映射
COUNTRY_MAP = {
    '🇺🇸 美国': r'美国|US|United States|America|States',
    '🇯🇵 日本': r'日本|JP|Japan|Tokyo|Osaka|Saitama',
    '🇭🇰 香港': r'香港|HK|HongKong|Hong Kong',
    '🇸🇬 新加坡': r'新加坡|SG|Singapore',
    '🇹🇼 台湾': r'台湾|TW|Taiwan|ROC',
    '🇰🇷 韩国': r'韩国|KR|Korea|South Korea|Seoul',
    '🇬🇧 英国': r'英国|UK|United Kingdom|Britain|London',
    '🇩🇪 德国': r'德国|DE|Germany|Frankfurt',
    '🇫🇷 法国': r'法国|FR|France|Paris',
    '🇷🇺 俄罗斯': r'俄罗斯|RU|Russia|Moscow',
    '🇨🇦 加拿大': r'加拿大|CA|Canada|Toronto',
    '🇳🇱 荷兰': r'荷兰|NL|Netherlands|Amsterdam'
}

def get_country_name(old_name):
    for country, pattern in COUNTRY_MAP.items():
        if re.search(pattern, str(old_name), re.I):
            return country
    return '🏳️ 其他'

def process_data(data, merged_proxies, seen_servers, country_counters):
    """通用解析逻辑"""
    if data and isinstance(data, dict) and 'proxies' in data:
        added_count = 0
        for p in data['proxies']:
            if not isinstance(p, dict): continue
            
            # 协议修正
            if p.get('type') == 'ss':
                method = p.get('cipher') or p.get('method')
                if method == 'chacha20-poly1305':
                    p['cipher'] = 'chacha20-ietf-poly1305'
            
            # 基础过滤
            server, port = p.get('server'), p.get('port')
            if not server or not port: continue

            server_key = f"{server}:{port}"
            if server_key not in seen_servers:
                country = get_country_name(p.get('name', ''))
                country_counters[country] = country_counters.get(country, 0) + 1
                p['name'] = f"{country} {country_counters[country]:02d}"
                merged_proxies.append(p)
                seen_servers.add(server_key)
                added_count += 1
        return added_count
    return 0

def fetch_and_merge():
    merged_proxies = []
    seen_servers = set()
    country_counters = {}

    print(f"========================================")
    print(f"🚀 MultiSource 节点整合任务开始")
    print(f"⏰ 北京时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"========================================")

    # A. 处理所有本地镜像源
    for local_file in LOCAL_SOURCES:
        if os.path.exists(local_file):
            print(f"📦 正在解析本地镜像: {local_file}")
            try:
                with open(local_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    added = process_data(data, merged_proxies, seen_servers, country_counters)
                    print(f"✅ 成功加载本地节点: {added} 个")
            except Exception as e:
                print(f"❌ 读取本地文件 {local_file} 失败: {e}")
        else:
            print(f"⚠️ 提示: 本地未找到 {local_file}")

    # B. 处理剩下的远程订阅源
    for url in REMOTE_SOURCES:
        print(f"📥 正在抓取远程源: {url}")
        try:
            headers = {'User-Agent': 'ClashMeta/1.18.0'}
            for i in range(2):
                try:
                    response = requests.get(url, headers=headers, timeout=25)
                    response.raise_for_status()
                    break
                except:
                    if i == 1: raise
                    time.sleep(2)

            content = response.text
            content = "".join(line for line in content.splitlines(True) if line.strip())
            data = yaml.safe_load(content)
            added = process_data(data, merged_proxies, seen_servers, country_counters)
            print(f"✅ 抓取成功，新增去重节点: {added} 个")
        except Exception as e:
            print(f"⚠️ 该远程源抓取失败，已跳过")

    # 结果导出
    if not merged_proxies:
        print("❌ 错误：未抓取到任何有效节点，任务终止。")
        return

    final_config = {
        'proxies': merged_proxies,
        'proxy-groups': [
            {
                'name': 'Proxy',
                'type': 'url-test',
                'proxies': [p['name'] for p in merged_proxies],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300,
                'tolerance': 50
            }
        ],
        'rules': ['MATCH,Proxy']
    }

    with open('MultiSource.yml', 'w', encoding='utf-8') as f:
        yaml.dump(final_config, f, allow_unicode=True, sort_keys=False)
    
    print(f"========================================")
    print(f"🎉 整合成功！最终去重节点总数: {len(merged_proxies)}")
    print(f"💾 文件已同步至仓库根目录: MultiSource.yml")
    print(f"========================================")

if __name__ == "__main__":
    fetch_and_merge()
