import json
import os
import time
import random
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from core.base_crawler import BaseCrawler
from utils.logger import logger
from utils.proxy_pool import get_random_proxy, load_cookies
from core.image_downloader import ImageDownloader
from core.selenium_crawler import SeleniumDetailCrawler
# 关闭SSL警告
import urllib3
urllib3.disable_warnings()


class DoubanTop250Crawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        self.base_url = "https://movie.douban.com/top250?start={}&filter="
        self.movies = []
        self.all_comments = []
        self.data_dir = "data/raw"
        self.poster_dir = "data/images"
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.poster_dir, exist_ok=True)
        self.img_downloader = ImageDownloader(self.poster_dir)
        # 使用上下文管理器初始化selenium
        self.detail_crawler = SeleniumDetailCrawler()

    def _requests_get(self, url):
        """增强版GET请求（重试+代理轮换+Cookie刷新）"""
        headers = self.headers.copy()
        cookies = load_cookies()
        headers["Cookie"] = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        # 增加请求头
        headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1"
        })
        for attempt in range(self.retry_count):
            try:
                resp = requests.get(
                    url,
                    headers=headers,
                    proxies=self.get_proxies(),
                    timeout=10,
                    verify=False,
                    allow_redirects=True
                )
                resp.raise_for_status()

                # 检查是否被反爬
                if "检测到异常访问" in resp.text or "验证" in resp.text:
                    logger.warning("触发反爬机制，更新代理/UA并等待")
                    self.update_proxy_and_ua()
                    self.random_sleep(5, 10)
                    continue

                # 重置代理失败计数
                self.proxy_failure_count = 0
                return resp

            except requests.exceptions.RequestException as e:
                logger.warning(f"请求失败（第{attempt+1}次）：{e} | URL：{url}")
                # 标记代理失败
                self.mark_proxy_failure()
                # 更新代理和UA
                self.update_proxy_and_ua()
                # 指数退避等待
                self.random_sleep(2*(attempt+1), 4*(attempt+1))

        logger.error(f"请求最终失败：{url}")
        return None

    def crawl_page(self, start):
        """爬取单页（增强数据校验）"""
        url = self.base_url.format(start)
        resp = self._requests_get(url)
        if not resp:
            logger.error(f"请求失败：{url}")
            return

        # 解析页面
        soup = BeautifulSoup(resp.text, "lxml")
        items = soup.find_all("div", class_="item")
        if not items:
            logger.error(f"页面无数据：{url}")
            return

        # 解析每个电影项
        success_count = 0
        for item in items:
            movie = self._parse_item(item)
            if movie:
                self.movies.append(movie)
                success_count += 1

        logger.info(f"成功爬取：{url} | 总数：{len(items)} | 成功解析：{success_count}")
        # 随机休眠（增加范围）
        self.random_sleep(2.5, 5.5)

    def _parse_item(self, item):
        """解析电影项（修复quote台词提取，兼容豆瓣真实HTML结构）"""
        movie = {}
        try:
            # 排名（安全转换）
            rank_tag = item.find("em")
            rank_num = rank_tag.text.strip() if rank_tag else "0"
            movie["rank_num"] = int(rank_num) if rank_num.isdigit() else 0

            # 标题（增强解析，安全判断）
            title_tag = item.find("span", class_="title")
            other_tag = item.find("span", class_="other")
            main_title = title_tag.text.strip() if title_tag else ""
            other_title = other_tag.text.strip().replace("/", "").strip() if other_tag else ""
            movie["title"] = f"{main_title} {other_title}".strip()
            if not movie["title"]:
                logger.warning("电影标题为空，跳过")
                return None

            # 评分（安全转换）
            rating_tag = item.find("span", class_="rating_num")
            rating_str = rating_tag.text.strip() if rating_tag else "0.0"
            movie["rating"] = float(rating_str) if rating_str.replace(".", "").isdigit() else 0.0

            # 评价人数（安全清理格式）
            cmt_tag = item.find("span", string=lambda s: s and "人评价" in s)
            comment_num = cmt_tag.text.replace("人评价", "").replace(",", "").strip() if cmt_tag else "0"
            movie["comment_num"] = int(comment_num) if comment_num.isdigit() else 0

            # 信息（安全判断）
            bd_tag = item.find("div", class_="bd")
            info_tag = bd_tag.find("p") if bd_tag else None
            movie["info"] = info_tag.text.strip().replace("  ", " ") if info_tag else ""

            # ===================== 修复：quote经典台词提取（兼容豆瓣真实结构）=====================
            quote_tag = item.find("p", class_="quote")
            if quote_tag:
                # 优先找span标签（豆瓣真实结构无class="inq"）
                span_tag = quote_tag.find("span")
                if span_tag and span_tag.text.strip():
                    movie["quote"] = span_tag.text.strip()
                else:
                    # 无span则直接取p标签的文本，去掉前后的引号
                    quote_text = quote_tag.text.strip().strip('“”""''')
                    movie["quote"] = quote_text if quote_text else "无经典台词"
            else:
                movie["quote"] = "无经典台词"
            # ======================================================================================

            # 详情页URL（安全判断）
            a_tag = item.find("a")
            movie["detail_url"] = a_tag["href"].strip() if a_tag and "href" in a_tag.attrs else ""

            # 海报下载（安全判断）
            img_tag = item.find("img")
            poster_path = ""
            if img_tag and img_tag.get("src"):
                img_url = img_tag["src"]
                # 下载海报
                if self.img_downloader.download(img_url, movie["title"]):
                    poster_path = os.path.join(self.poster_dir, f"{self.img_downloader._safe_name(movie['title'])}.jpg")
            movie["poster_path"] = poster_path

            # 爬取详情页数据（安全判断）
            if movie["detail_url"]:
                detail = self.detail_crawler.crawl_detail(movie["detail_url"])
                if detail:
                    # 合并详情数据（覆盖原有字段）
                    movie.update({
                        "year": detail.get("year", ""),
                        "runtime": detail.get("runtime", ""),
                        "imdb": detail.get("imdb", "")
                    })
                    # 收集评论
                    if "comments" in detail and isinstance(detail["comments"], list):
                        for c in detail["comments"]:
                            if c.get("content"):  # 仅保存有内容的评论
                                self.all_comments.append((
                                    movie["rank_num"],  # 替换为rank_num，适配数据库关联
                                    c.get("username", ""),
                                    c.get("rating", ""),
                                    c.get("content", ""),
                                    c.get("time", "")
                                ))

            # 数据校验（核心字段不能为空）
            if movie["rank_num"] == 0 or movie["rating"] == 0.0:
                logger.warning(f"核心字段缺失：{movie['title']} | 排名：{movie['rank_num']} | 评分：{movie['rating']}")
                return None

            return movie

        except Exception as e:
            logger.error(f"解析失败：{e} | 电影标题：{movie.get('title', '未知')}")
            return None

    def crawl_all(self):
        """爬取所有页面（增强进度展示）"""
        logger.info("开始爬取豆瓣Top250全部数据...")
        # 清空历史数据
        self.movies = []
        self.all_comments = []

        # 分批爬取（10页，每页25条，共250条）
        for i in tqdm(range(0, 250, 25), desc="爬取进度", unit="页"):
            self.crawl_page(i)

        # 数据统计
        logger.info(f"爬取完成 | 电影总数：{len(self.movies)} | 评论总数：{len(self.all_comments)}")
        return self.movies

    def save_data(self):
        """保存原始数据（增强容错）"""
        if not self.movies:
            logger.warning("无数据可保存")
            return None

        json_path = os.path.join(self.data_dir, "douban_top250_raw.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(self.movies, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"原始数据保存成功：{json_path} | 数据量：{len(self.movies)}")
            return json_path
        except Exception as e:
            logger.error(f"保存数据失败：{e}")
            return None

    def get_all_comments(self):
        """获取所有评论（数据校验+去重，适配数据库插入格式）"""
        # 转换为数据库插入格式
        comment_list = []
        comment_keys = set()
        
        for comment in self.all_comments:
            if len(comment) < 5:
                continue
            
            # 构造插入字典
            comment_dict = {
                "movie_rank": comment[0],
                "username": comment[1],
                "rating": comment[2],
                "content": comment[3],
                "comment_time": comment[4]
            }
            
            # 去重：按电影排名+用户名+内容前100字
            key = f"{comment[0]}_{comment[1]}_{comment[3][:100]}"
            if key not in comment_keys:
                comment_keys.add(key)
                comment_list.append(comment_dict)

        logger.info(f"评论去重 | 原始：{len(self.all_comments)} | 去重后：{len(comment_list)}")
        return comment_list

    def close(self):
        """关闭所有资源"""
        self.detail_crawler.close()
        logger.info("爬虫资源已全部释放")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        if exc_type:
            logger.error(f"爬虫执行异常：{exc_val}")