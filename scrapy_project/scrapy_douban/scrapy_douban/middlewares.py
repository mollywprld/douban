# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import logging
import random
import time
from typing import Optional

import selenium.webdriver as webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from scrapy import signals
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import IgnoreRequest
from scrapy.http import HtmlResponse, Request, Response

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

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


class RandomUserAgentMiddleware:
    """随机User-Agent中间件"""

    def __init__(self, user_agents=None):
        self.user_agents = user_agents or USER_AGENTS

    @classmethod
    def from_crawler(cls, crawler):
        user_agents = crawler.settings.get('USER_AGENTS', USER_AGENTS)
        return cls(user_agents)

    def process_request(self, request: Request, spider=None):
        """为每个请求设置随机User-Agent"""
        if not request.headers.get('User-Agent'):
            request.headers['User-Agent'] = random.choice(self.user_agents)
        return None


class RandomDelayMiddleware:
    """随机延时中间件"""

    def __init__(self, delay_min=1.0, delay_max=4.0):
        self.delay_min = delay_min
        self.delay_max = delay_max

    @classmethod
    def from_crawler(cls, crawler):
        delay_min = crawler.settings.getfloat('RANDOM_DELAY_MIN', 1.0)
        delay_max = crawler.settings.getfloat('RANDOM_DELAY_MAX', 4.0)
        return cls(delay_min, delay_max)

    def process_request(self, request: Request, spider=None):
        """在请求前添加随机延时"""
        delay = random.uniform(self.delay_min, self.delay_max)
        logger.debug(f"Delaying request to {request.url} by {delay:.2f}s")
        time.sleep(delay)
        return None


class SeleniumRenderMiddleware:
    """使用Selenium渲染豆瓣页面以绕过安全拦截。"""

    def __init__(self, driver_path: Optional[str] = None, headless: bool = True):
        self.driver_path = driver_path
        self.headless = headless
        self.driver = None

    @classmethod
    def from_crawler(cls, crawler):
        driver_path = crawler.settings.get('SELENIUM_DRIVER_PATH')
        headless = crawler.settings.getbool('SELENIUM_HEADLESS', True)
        middleware = cls(driver_path=driver_path, headless=headless)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def spider_opened(self, spider):
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1600,1200')
        options.add_argument('--lang=zh-CN,zh;q=0.9')
        options.add_argument(f'--user-agent={random.choice(USER_AGENTS)}')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            if self.driver_path:
                service = Service(str(self.driver_path))
                self.driver = webdriver.Edge(service=service, options=options)
            else:
                self.driver = webdriver.Edge(options=options)

            self.driver.execute_cdp_cmd(
                'Page.addScriptToEvaluateOnNewDocument',
                {
                    'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
                },
            )
            self.driver.set_page_load_timeout(45)
            self.driver.implicitly_wait(5)
            logger.info('Started Selenium browser for Douban rendering')
        except WebDriverException as exc:
            logger.error('Unable to start Selenium browser: %s', exc)
            self.driver = None

    def spider_closed(self, spider):
        if self.driver:
            try:
                self.driver.quit()
                logger.info('Closed Selenium browser')
            except Exception:
                pass
            self.driver = None

    def _should_render(self, request: Request) -> bool:
        if request.meta.get('render', True) is False:
            return False
        return request.url.startswith('https://movie.douban.com')

    def process_request(self, request: Request, spider=None):
        if not self.driver or not self._should_render(request):
            return None

        try:
            self.driver.get(request.url)
            time.sleep(random.uniform(2.0, 3.5))
            body = self.driver.page_source.encode('utf-8')
            response = HtmlResponse(
                url=request.url,
                body=body,
                encoding='utf-8',
                request=request,
                status=200,
            )
            if 'sec.douban.com' in self.driver.current_url or 'sec.douban.com' in response.text:
                logger.warning('Detected Douban security interception while rendering %s', request.url)
            return response
        except Exception as exc:
            logger.warning('Selenium render error for %s: %s (%s)', request.url, type(exc).__name__, exc)
            return None


class DoubanRetryMiddleware(RetryMiddleware):
    """豆瓣专用重试中间件"""

    def __init__(self, settings):
        super().__init__(settings)
        self.max_retry_times = settings.getint('RETRY_TIMES', 5)
        self.retry_http_codes = set(settings.getlist('RETRY_HTTP_CODES', [403, 429, 500, 502, 503, 504]))

    def process_response(self, request: Request, response: Response, spider=None):
        """处理响应，根据状态码决定是否重试"""
        if response.status in self.retry_http_codes:
            reason = f'HTTP {response.status} for {request.url}'
            return self._retry(request, reason) or response

        content_type = response.headers.get('Content-Type', b'').decode('utf-8', errors='ignore').lower()
        body_text = None
        if 'text' in content_type or 'html' in content_type:
            try:
                body_text = response.text
            except AttributeError:
                body_text = None

        # 检查是否被豆瓣安全拦截
        if 'sec.douban.com' in response.url or (body_text and 'sec.douban.com' in body_text):
            reason = f'Douban security interception for {request.url}'
            return self._retry(request, reason) or response

        return response

    def process_exception(self, request: Request, exception, spider=None):
        """处理异常"""
        return self._retry(request, str(exception))


class ScrapyDoubanSpiderMiddleware:
    """Spider中间件"""

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider=None):
        return None

    def process_spider_output(self, response, result, spider=None):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider=None):
        pass

    def spider_opened(self, spider):
        logger.info(f'Spider {spider.name} opened')


class ScrapyDoubanDownloaderMiddleware:
    """Downloader中间件"""

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider=None):
        return None

    def process_response(self, request, response, spider=None):
        return response

    def process_exception(self, request, exception, spider=None):
        pass

    def spider_opened(self, spider):
        logger.info(f'Downloader middleware for {spider.name} opened')