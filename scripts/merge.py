import requests
import yaml
import re
import time

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
        if re.search(pattern, str(old_name), re.I):
            return country
    return '🏳️ 其他'

def fetch_and_merge():
    merged_proxies = []
    seen_servers = set()
    country_counters = {}

    for url in SOURCES:
        print(f"正在尝试抓取: {url}")
        try:
            headers = {'User-Agent': 'ClashMeta/1.18.0'}
            # 增加重试机制，防止网络波动
            for i in range(3):
                try:
                    response = requests.get(url, headers=headers, timeout=30)
                    response.raise_for_status() # 如果是 404 或 500 直接抛出异常
                    break
                except Exception:
                    if i == 2: raise
                    time.sleep(2)

            # 极其保守的 YAML 解析
            try:
                content = response.text
                # 预处理：防止一些奇怪的控制字符导致解析失败
                content = "".join(line for line in content.splitlines(True) if line.strip())
                data = yaml.safe_load(content)
            except Exception as e:
                print(f"YAML 解析失败，跳过该源: {url} | 错误: {e}")
                continue
            
            if data and isinstance(data, dict) and 'proxies' in data:
                for p in data['proxies']:
                    if not isinstance(p, dict): continue
                    
                    # 协议修正
                    if p.get('type') == 'ss':
                        method = p.get('cipher') or p.get('method')
                        if method == 'chacha20-poly1305':
                            p['cipher'] = 'chacha20-ietf-poly1305'
                    
                    # 基础有效性过滤
                    server = p.get('server')
                    port = p.get('port')
                    if not server or not port:
                        continue

                    server_key = f"{server}:{port}"
                    if server_key not in seen_servers:
                        country = get_country_name(p.get('name', ''))
                        country_counters[country] = country_counters.get(country, 0) + 1
                        p['name'] = f"{country} {country_counters[country]:02d}"
                        merged_proxies.append(p)
                        seen_servers.add(server_key)
                        
        except Exception as e:
            print(f"该源彻底失效，已跳过: {url} | 错误详情: {e}")

    # 兜底：如果所有源都挂了，至少不能让 Clash 报错
    if not merged_proxies:
        print("警告：未抓取到任何有效节点！")
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
    print(f"处理成功！产出节点总数: {len(merged_proxies)}")

if __name__ == "__main__":
    fetch_and_merge()
