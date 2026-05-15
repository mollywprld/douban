import time
import random
from utils.user_agents import get_random_ua
from utils.proxy_pool import get_random_proxy
from utils.logger import logger

class BaseCrawler:
    """爬虫基类：封装通用功能（增强版）"""
    def __init__(self):
        self.headers = {"User-Agent": get_random_ua()}
        self.proxy = get_random_proxy()
        self.retry_count = 3  # 默认重试次数
        self.proxy_failure_count = 0  # 代理失败计数
        self.max_proxy_failure = 5  # 最大代理失败次数（超过则切换）

    def random_sleep(self, min_sec=2, max_sec=5):
        """随机休眠（防反爬，增加随机性）"""
        sleep_time = random.uniform(min_sec, max_sec)
        logger.info(f"休眠 {sleep_time:.2f} 秒")
        time.sleep(sleep_time)

    def get_proxies(self):
        """获取代理配置（增强代理校验+轮换）"""
        if not self.proxy:
            return None
        
        # 代理失败次数过多，重新获取
        if self.proxy_failure_count >= self.max_proxy_failure:
            logger.info(f"代理失败{self.proxy_failure_count}次，重新获取代理")
            self.proxy = get_random_proxy()
            self.proxy_failure_count = 0
        
        return self.proxy

    def update_proxy_and_ua(self):
        """更新代理和UA（增强反爬）"""
        self.proxy = get_random_proxy()
        self.headers["User-Agent"] = get_random_ua()
        # 重置失败计数
        self.proxy_failure_count = 0
        logger.info("已更新代理和User-Agent")

    def mark_proxy_failure(self):
        """标记代理失败"""
        self.proxy_failure_count += 1
        logger.warning(f"代理失败计数：{self.proxy_failure_count}/{self.max_proxy_failure}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if exc_type:
            logger.error(f"爬虫执行异常：{exc_val}")