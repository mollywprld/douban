import os
import requests
import random
from utils.logger import logger
from utils.user_agents import get_random_ua

# 关闭SSL警告
import urllib3
urllib3.disable_warnings()

class ImageDownloader:
    def __init__(self, save_dir):  # 修复初始化方法名错误
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        # 初始化请求头（增加防盗链）
        self.headers = {
            "User-Agent": get_random_ua(),
            "Referer": "https://movie.douban.com/",
            "Accept": "image/webp,image/jpeg,image/png,image/gif",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        # 重试次数
        self.retry_count = 2

    def _safe_name(self, name):
        """安全文件名（增强特殊字符过滤）"""
        if not name:
            name = "unknown"
        # 过滤Windows/Mac/Linux非法字符
        # 修复：使用双引号包裹字符串，避免单引号冲突
        invalid_chars = r'\/:*?"<>|`~!@#$%^&*()+=[]{};' + "'." 
        for c in invalid_chars:
            name = name.replace(c, "_")
        # 限制长度
        return name[:30].strip()

    def download(self, url, filename):
        """下载图片（增强重试+校验）"""
        if not url or not filename:
            logger.warning("URL或文件名为空，跳过下载")
            return False
        
        # 处理文件名
        name = self._safe_name(filename) + ".jpg"
        path = os.path.join(self.save_dir, name)
        
        # 检查文件是否已存在且有效
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            if file_size > 1024:  # 大于1KB认为有效
                logger.info(f"图片已存在且有效：{name}")
                return True
            else:
                logger.warning(f"图片文件过小，重新下载：{name}")
                os.remove(path)
        
        # 开始下载（带重试）
        for attempt in range(self.retry_count + 1):
            try:
                # 流式下载（避免内存溢出）
                resp = requests.get(
                    url, 
                    headers=self.headers, 
                    timeout=15, 
                    stream=True, 
                    verify=False,
                    allow_redirects=True
                )
                resp.raise_for_status()
                
                # 校验响应内容类型
                content_type = resp.headers.get("Content-Type", "")
                if not any(ct in content_type for ct in ["image/jpeg", "image/png", "image/webp"]):
                    logger.warning(f"非图片类型，跳过：{content_type} | {filename}")
                    return False
                
                # 写入文件
                with open(path, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                
                # 校验文件大小
                final_size = os.path.getsize(path)
                if final_size < 1024:
                    os.remove(path)
                    logger.warning(f"下载的图片过小（{final_size}字节）：{name}")
                    if attempt < self.retry_count:
                        logger.info(f"第{attempt+1}次重试下载：{name}")
                        continue
                    return False
                
                logger.info(f"图片下载成功：{name} | 大小：{final_size/1024:.1f}KB")
                return True
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"图片下载失败（第{attempt+1}次）：{e} | {filename}")
                if attempt < self.retry_count:
                    import time
                    time.sleep(random.uniform(1, 3))
                    continue
                return False
            except Exception as e:
                logger.error(f"图片下载异常：{e} | {filename}")
                return False