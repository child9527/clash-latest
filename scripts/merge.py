import requests
import yaml
import re

# 6个原始订阅源
SOURCES = [
    "https://github.com/snakem982/proxypool/raw/refs/heads/main/source/clash-meta.yaml",
    "https://github.com/snakem982/proxypool/raw/refs/heads/main/source/clash-meta-2.yaml",
    "https://github.com/free18/v2ray/raw/refs/heads/main/c.yaml",
    "https://github.com/child9527/clash-latest/raw/refs/heads/main/free-nodes.yml",
    "https://github.com/child9527/clash-latest/raw/refs/heads/main/tglaoshiji.yml",
    "https://github.com/mahdibland/V2RayAggregator/raw/refs/heads/master/Eternity.yml"
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
        if re.search(pattern, old_name, re.I):
            return country
    return '🏳️ 其他'

def fetch_and_merge():
    merged_proxies = []
    seen_servers = set()
    country_counters = {}

    for url in SOURCES:
        try:
            # 模拟浏览器 User-Agent 避免被屏蔽
            headers = {'User-Agent': 'ClashMeta/1.18.0'}
            response = requests.get(url, headers=headers, timeout=20)
            # 处理一些源返回的乱码或非标准格式
            try:
                data = yaml.safe_load(response.text)
            except Exception:
                continue
            
            if data and 'proxies' in data:
                for p in data['proxies']:
                    # --- 协议修正逻辑开始 ---
                    # 1. 修正 Shadowsocks 的加密方式
                    if p.get('type') == 'ss':
                        # 兼容 cipher 或 method 字段
                        method = p.get('cipher') or p.get('method')
                        if method == 'chacha20-poly1305':
                            p['cipher'] = 'chacha20-ietf-poly1305'
                    
                    # 2. 基础有效性过滤 (必须有地址和端口)
                    if not p.get('server') or not p.get('port'):
                        continue
                    # --- 协议修正逻辑结束 ---

                    # 关键逻辑：按服务器地址和端口去重
                    server_key = f"{p.get('server')}:{p.get('port')}"
                    if server_key not in seen_servers:
                        # 识别国家并重命名
                        country = get_country_name(p.get('name', ''))
                        country_counters[country] = country_counters.get(country, 0) + 1
                        p['name'] = f"{country} {country_counters[country]:02d}"
                        
                        merged_proxies.append(p)
                        seen_servers.add(server_key)
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    # 构建 Clash 最小化配置输出
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

    # 导出为 MultiSource.yml
    with open('MultiSource.yml', 'w', encoding='utf-8') as f:
        yaml.dump(final_config, f, allow_unicode=True, sort_keys=False)
    print(f"合并完成！共计去重后节点: {len(merged_proxies)}")

if __name__ == "__main__":
    fetch_and_merge()
