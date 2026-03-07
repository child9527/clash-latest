const axios = require('axios');
const fs = require('fs');

// V2RaySE 的公共数据源接口（通常为该地址）
const RAW_URL = 'https://oss.v2rayse.com/proxies'; 

async function fetchNodes() {
    try {
        console.log('正在从 V2RaySE 获取节点...');
        const response = await axios.get(RAW_URL);
        const base64Data = response.data;

        // 解码 Base64 获取明文节点列表
        const plainText = Buffer.from(base64Data, 'base64').toString('utf-8');
        const nodes = plainText.split('\n').filter(line => line.trim() !== '');

        console.log(`成功获取 ${nodes.length} 个节点。`);

        // 构建简单的 YAML 结构（仅包含节点名，具体转换依赖 subconverter 可更强大）
        // 这里我们先生成一个标准的明文列表，因为 Clash 订阅通常需要 subconverter 进一步转换
        // 如果你想直接生成 YAML，建议在 Actions 中调用你之前的 subconverter 逻辑
        
        fs.writeFileSync('v2rayse_raw.txt', base64Data);
        console.log('原始数据已保存至 v2rayse_raw.txt');

    } catch (error) {
        console.error('抓取失败:', error.message);
        process.exit(1);
    }
}

fetchNodes();
