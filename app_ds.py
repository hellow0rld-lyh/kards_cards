import json
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# 配置参数
CONFIG = {
    "json_path": "./cards.json",     # JSON文件路径
    "output_dir": "downloaded_images",  # 图片保存目录
    "domain_prefix": "www.kards.com",   # 域名前缀
    "max_workers": 64,                 # 并发线程数
    "timeout": 15,                     # 单个请求超时时间（秒）
    "retries": 3                       # 失败重试次数
}

def process_json():
    """处理JSON文件并生成图片URL列表"""
    with open(CONFIG['json_path'], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    nodes = data['data']['cards']['edges']
    imgurls = []
    
    for node in nodes:
        # 拼接完整图片URL（自动处理路径斜杠）
        raw_path = node['node']['imageUrl'].lstrip('/')
        full_url = f"https://{CONFIG['domain_prefix']}/{raw_path}"
        imgurls.append(full_url)
    
    return imgurls

def download_image(url, save_path):
    """下载单个图片"""
    for attempt in range(CONFIG['retries']):
        try:
            response = requests.get(
                url,
                timeout=CONFIG['timeout'],
                stream=True,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
            
        except Exception as e:
            if attempt == CONFIG['retries'] - 1:
                print(f"\n下载失败: {url} | 错误: {str(e)}")
            continue
    return False

def batch_download(urls):
    """批量下载任务"""
    tasks = []
    
    with ThreadPoolExecutor(max_workers=CONFIG['max_workers']) as executor:
        # 提交下载任务
        for idx, url in enumerate(urls):
            # 从URL提取文件名
            filename = os.path.basename(url).split("?")[0]
            save_path = os.path.join(CONFIG['output_dir'], filename)
            
            tasks.append(executor.submit(
                download_image,
                url,
                save_path
            ))
        
        # 进度条显示
        success = 0
        with tqdm(total=len(tasks), desc="下载进度", unit="img") as pbar:
            for future in as_completed(tasks):
                if future.result():
                    success += 1
                pbar.update(1)
                
    print(f"\n下载完成！成功 {success}/{len(urls)}")
    print(f"图片保存至：{os.path.abspath(CONFIG['output_dir'])}")

if __name__ == "__main__":
    # 步骤1：处理JSON获取URL列表
    print("正在解析JSON文件...")
    try:
        img_urls = process_json()
        print(f"发现 {len(img_urls)} 张待下载图片")
    except Exception as e:
        print(f"JSON解析失败: {str(e)}")
        exit(1)
    
    # 步骤2：执行下载
    batch_download(img_urls)