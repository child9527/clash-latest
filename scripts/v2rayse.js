const axios = require('axios');
const fs = require('fs');

// V2RaySE 的公共数据源接口
const RAW_URL = 'https://oss.v2rayse.com/proxies'; 

async function fetchNodes() {
    try {
        console.log('正在从 V2RaySE 获取节点...');
        
        // 添加请求头，伪装成普通浏览器
        const response = await axios.get(RAW_URL, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Connection': 'keep-alive'
            },
            timeout: 10000 // 设置 10 秒超时
        });

        const base64Data = response.data;

        if (!base64Data) {
            throw new Error('获取到的数据为空');
        }

        // 写入根目录
        fs.writeFileSync('v2rayse_raw.txt', base64Data);
        console.log('成功获取数据并保存至 v2rayse_raw.txt');

    } catch (error) {
        // 打印更详细的错误信息
        if (error.response) {
            console.error(`抓取失败: 服务器返回状态码 ${error.response.status}`);
            console.error('返回数据:', error.response.data);
        } else {
            console.error('抓取失败:', error.message);
        }
        process.exit(1);
    }
}

fetchNodes();
