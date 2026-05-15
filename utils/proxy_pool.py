import random
import requests
from utils.logger import logger

# 留空 = 不用代理（最稳）
PROXIES = []

def get_random_proxy():
    if not PROXIES:
        logger.info("代理池为空，使用本地IP")
        return None
    random.shuffle(PROXIES)
    test_url = "https://movie.douban.com/robots.txt"
    timeout = 3
    for proxy in PROXIES:
        try:
            resp = requests.get(
                test_url,
                proxies=proxy,
                timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"},
                verify=False
            )
            if resp.status_code == 200:
                logger.info(f"代理有效：{proxy}")
                return proxy
        except Exception:
            continue
    logger.warning("无有效代理，使用本地IP")
    return None

def load_cookies():
    cookies = {
        "bid": "kxkFgY9bt8A",
        "douban-fav-remind": "1",
        "ck": "gj4C",
        "dbcl2": "295054165:Rc2GBZyAbdM",
        "ll": "118254",
        "_vwo_uuid_v2": "D870F3EBBDCA6F8807218DB1C770C4433|f2f93f2a5179853005bfb672afbfb20b",
        "__yadk_uid": "hH4jPVIByM8IbyqatyIfVv1eGL4eGtGc",
        "push_doumail_num": "0",
        "push_noty_num": "0"
    }
    return cookies