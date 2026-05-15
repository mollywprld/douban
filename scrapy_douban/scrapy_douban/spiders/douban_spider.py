import json
import logging
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import scrapy
from scrapy import Request
from scrapy.http import HtmlResponse

from ..items import DoubanMovieItem

# User-Agent池
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/124.0.0.0 Safari/537.36",
]

logger = logging.getLogger(__name__)


class DoubanTop250Spider(scrapy.Spider):
    """豆瓣Top250爬虫Spider"""

    name = 'douban_top250'
    allowed_domains = ['movie.douban.com']
    start_urls = ['https://movie.douban.com/top250']

    custom_settings = {
        'DOWNLOAD_DELAY': 2,  # 基础下载延时
        'RANDOMIZE_DOWNLOAD_DELAY': True,  # 随机化延时
        'DOWNLOAD_TIMEOUT': 15,
        'CONCURRENT_REQUESTS': 1,  # 限制并发请求
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'ROBOTSTXT_OBEY': False,  # 不遵守robots.txt
        'COOKIES_ENABLED': True,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    }

    def __init__(self, posters_dir='posters_scrapy', limit=250, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.posters_dir = Path(posters_dir)
        self.posters_dir.mkdir(parents=True, exist_ok=True)
        self.limit = int(limit)
        self.crawled_count = 0

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.limit = int(kwargs.get('limit', crawler.settings.getint('LIMIT', getattr(spider, 'limit', 250))))
        return spider

    def start_requests(self) -> Generator[Request, None, None]:
        """生成初始请求"""
        for start in range(0, min(250, self.limit), 25):
            url = f"https://movie.douban.com/top250?start={start}&filter="
            yield Request(
                url=url,
                callback=self.parse_list_page,
                headers={'User-Agent': random.choice(USER_AGENTS)},
                meta={'start': start, 'render': True},
                dont_filter=True
            )

    def parse_list_page(self, response: HtmlResponse) -> Generator[DoubanMovieItem, None, None]:
        """解析列表页面"""
        if self.crawled_count >= self.limit:
            return

        # 检查是否被拦截
        if 'sec.douban.com' in response.url or 'sec.douban.com' in response.text:
            logger.warning("Detected Douban security interception on %s", response.url)
            # 重新请求当前页面
            yield Request(
                url=response.url,
                callback=self.parse_list_page,
                headers={'User-Agent': random.choice(USER_AGENTS)},
                meta=response.meta,
                dont_filter=True,
                priority=10  # 提高优先级
            )
            return

        # 解析电影列表
        movies = self._extract_movies_from_list(response)
        for movie_data in movies:
            if self.crawled_count >= self.limit:
                break

            movie_item = DoubanMovieItem()
            movie_item.update(movie_data)
            movie_item['crawled_at'] = datetime.now().isoformat()
            movie_item['spider_name'] = self.name

            # 请求详情页面
            yield Request(
                url=movie_item['detail_link'],
                callback=self.parse_detail_page,
                headers={'User-Agent': random.choice(USER_AGENTS)},
                meta={'movie_item': movie_item, 'render': True},
                dont_filter=True
            )

            self.crawled_count += 1

    def parse_detail_page(self, response: HtmlResponse) -> Generator[DoubanMovieItem, None, None]:
        """解析详情页面"""
        movie_item = response.meta['movie_item']

        # 提取详情信息
        movie_item.update(self._extract_movie_details(response))

        # 提取海报URL
        poster_url = self._extract_poster_url(response)
        if poster_url:
            movie_item['poster_url'] = poster_url

        # 请求评论页面
        comments_url = f"{movie_item['detail_link'].rstrip('/')}/comments?status=P"
        yield Request(
            url=comments_url,
            callback=self.parse_comments_page,
            headers={'User-Agent': random.choice(USER_AGENTS)},
            meta={'movie_item': movie_item, 'comments': [], 'page': 1, 'render': True},
            dont_filter=True
        )

    def parse_comments_page(self, response: HtmlResponse) -> Generator[DoubanMovieItem, None, None]:
        """解析评论页面"""
        movie_item = response.meta['movie_item']
        comments = response.meta.get('comments', [])
        page = response.meta.get('page', 1)

        # 提取当前页评论
        page_comments = self._extract_comments(response)
        comments.extend(page_comments)

        # 检查是否需要下一页
        if len(comments) < 15 and page < 3:  # 最多爬取3页评论
            next_link = response.css('span.next a::attr(href)').get()
            if next_link:
                next_url = response.urljoin(next_link)
                yield Request(
                    url=next_url,
                    callback=self.parse_comments_page,
                    headers={'User-Agent': random.choice(USER_AGENTS)},
                    meta={
                        'movie_item': movie_item,
                        'comments': comments,
                        'page': page + 1,
                        'render': True
                    },
                    dont_filter=True
                )
                return

        # 评论收集完成
        movie_item['hot_comments'] = comments[:15]  # 最多保留15条评论

        # 尽量保留电影对象，海报下载失败不影响Item产出
        if movie_item.get('poster_url'):
            yield Request(
                url=movie_item['poster_url'],
                callback=self.parse_poster,
                headers={
                    'User-Agent': random.choice(USER_AGENTS),
                    'Referer': movie_item['detail_link'],
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
                },
                meta={'movie_item': movie_item, 'render': False},
                dont_filter=True
            )

        yield movie_item

    def parse_poster(self, response: HtmlResponse):
        """处理海报下载"""
        movie_item = response.meta['movie_item']

        # 保存海报
        poster_path = self._save_poster(response, movie_item)
        if poster_path:
            movie_item['poster_path'] = str(poster_path)

        # 不再重复产出Item，当作附加资源下载处理
        return None

    def _extract_movies_from_list(self, response: HtmlResponse) -> List[Dict[str, Any]]:
        """从列表页面提取电影基本信息"""
        movies = []
        for item in response.css('div.item'):
            movie_data = {}

            # 排名
            movie_data['rank'] = item.css('div.pic em::text').get('').strip()

            # 标题
            title_spans = item.css('div.hd span.title::text').getall()
            if title_spans:
                movie_data['title_cn'] = title_spans[0].strip()
                if len(title_spans) > 1:
                    movie_data['title_en'] = title_spans[1].strip()

            # 评分
            movie_data['rating'] = item.css('span.rating_num::text').get('').strip()

            # 评价人数
            star_info = item.css('div.star span::text').getall()
            if star_info and len(star_info) > 0:
                movie_data['rating_count'] = star_info[-1].strip()

            # 导演和主演
            desc_text = item.css('div.bd p::text').getall()
            if desc_text:
                movie_data['directors_cast'] = ' '.join([t.strip() for t in desc_text if t.strip()])

            # 引用
            movie_data['quote'] = item.css('span.inq::text').get('').strip()

            # 详情链接
            movie_data['detail_link'] = item.css('div.hd a::attr(href)').get('').strip()

            if movie_data.get('detail_link'):
                movies.append(movie_data)

        return movies

    def _extract_movie_details(self, response: HtmlResponse) -> Dict[str, Any]:
        """提取电影详情信息"""
        details = {}

        # 上映年份
        year = response.css('span.year::text').get()
        if year:
            details['year'] = year.strip('() ')

        # 片长
        info_text = response.css('div#info::text').getall()
        info_full = ' '.join([t.strip() for t in info_text if t.strip()])
        duration_match = re.search(r'片长[:：]?\s*([0-9]+分钟)', info_full)
        if duration_match:
            details['duration'] = duration_match.group(1)

        # 类型
        genres = response.css('span[property="v:genre"]::text').getall()
        details['genre'] = ', '.join([g.strip() for g in genres if g.strip()])

        # IMDb评分
        imdb_link = response.css('a[href*="imdb.com"]::text').get()
        if imdb_link:
            details['imdb_rating'] = imdb_link.strip()

        return details

    def _extract_poster_url(self, response: HtmlResponse) -> Optional[str]:
        """提取海报URL"""
        poster_url = response.css('div#mainpic img::attr(src)').get()
        return poster_url.strip() if poster_url else None

    def _extract_comments(self, response: HtmlResponse) -> List[Dict[str, str]]:
        """提取评论"""
        comments = []
        for comment_item in response.css('div.comment-item'):
            comment = {}

            # 作者
            comment['author'] = comment_item.css('span.comment-info a::text').get('').strip()

            # 评分
            rating = comment_item.css('span.comment-info span.rating::attr(title)').get()
            comment['score'] = rating.strip() if rating else ''

            # 时间
            comment['time'] = comment_item.css('span.comment-info span.comment-time::text').get('').strip()

            # 内容
            comment['content'] = comment_item.css('span.short::text').get('').strip()

            if comment.get('content'):
                comments.append(comment)

        return comments

    def _save_poster(self, response: HtmlResponse, movie_item: DoubanMovieItem) -> Optional[Path]:
        """保存海报文件"""
        try:
            # 生成文件名
            title = movie_item.get('title_cn') or movie_item.get('title_en') or f"movie_{movie_item.get('rank')}"
            safe_name = re.sub(r'[\\/:*?"<>|]+', '_', title)[:100]

            # 获取文件扩展名
            content_type = response.headers.get('Content-Type', b'').decode('utf-8', errors='ignore')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'webp' in content_type:
                ext = '.webp'
            else:
                ext = '.jpg'  # 默认扩展名

            poster_path = self.posters_dir / f"{safe_name}{ext}"

            # 保存文件
            with open(poster_path, 'wb') as f:
                f.write(response.body)

            logger.info(f"Saved poster: {poster_path}")
            return poster_path

        except Exception as e:
            logger.warning(f"Failed to save poster for {movie_item.get('title_cn')}: {e}")
            return None