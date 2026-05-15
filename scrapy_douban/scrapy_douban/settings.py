# Scrapy settings for scrapy_douban project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "scrapy_douban"

SPIDER_MODULES = ["scrapy_douban.spiders"]
NEWSPIDER_MODULE = "scrapy_douban.spiders"

ADDONS = {}

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "scrapy_douban (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False  # 不遵守robots.txt以便爬取豆瓣

# Concurrency and throttling settings
CONCURRENT_REQUESTS = 1  # 限制并发请求
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 2  # 基础下载延时
RANDOMIZE_DOWNLOAD_DELAY = True  # 随机化延时

# Download timeout
DOWNLOAD_TIMEOUT = 15

# Disable cookies (豆瓣不需要cookies)
COOKIES_ENABLED = True

# Disable Telnet Console
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    "scrapy_douban.middlewares.ScrapyDoubanSpiderMiddleware": 543,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    "scrapy_douban.middlewares.SeleniumRenderMiddleware": 100,
    "scrapy_douban.middlewares.RandomUserAgentMiddleware": 400,
    "scrapy_douban.middlewares.RandomDelayMiddleware": 500,
    "scrapy_douban.middlewares.DoubanRetryMiddleware": 600,
    "scrapy_douban.middlewares.ScrapyDoubanDownloaderMiddleware": 543,
}

# Selenium settings
SELENIUM_HEADLESS = True
SELENIUM_DRIVER_PATH = None

# Configure item pipelines
ITEM_PIPELINES = {
    "scrapy_douban.pipelines.ValidationPipeline": 100,
    "scrapy_douban.pipelines.SQLitePipeline": 200,
    "scrapy_douban.pipelines.JsonExportPipeline": 300,
    "scrapy_douban.pipelines.CsvExportPipeline": 400,
}

# 自定义设置
# 随机延时范围
RANDOM_DELAY_MIN = 1.0
RANDOM_DELAY_MAX = 4.0

# 重试设置
RETRY_TIMES = 5
RETRY_HTTP_CODES = [403, 429, 500, 502, 503, 504]

# 数据存储设置
SQLITE_DB_PATH = 'douban_scrapy.db'
JSON_OUTPUT_FILE = 'douban_scrapy.json'
CSV_MOVIES_FILE = 'movies_scrapy.csv'
CSV_COMMENTS_FILE = 'comments_scrapy.csv'

# 日志设置
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"