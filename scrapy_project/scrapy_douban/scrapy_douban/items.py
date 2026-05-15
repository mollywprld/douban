# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DoubanMovieItem(scrapy.Item):
    """豆瓣电影Item定义"""
    # 基本信息
    rank = scrapy.Field()
    title_cn = scrapy.Field()
    title_en = scrapy.Field()
    rating = scrapy.Field()
    rating_count = scrapy.Field()
    directors_cast = scrapy.Field()
    quote = scrapy.Field()
    detail_link = scrapy.Field()

    # 详情信息
    year = scrapy.Field()
    duration = scrapy.Field()
    genre = scrapy.Field()
    imdb_rating = scrapy.Field()

    # 媒体信息
    poster_url = scrapy.Field()
    poster_path = scrapy.Field()

    # 评论信息
    hot_comments = scrapy.Field()

    # 元数据
    crawled_at = scrapy.Field()
    spider_name = scrapy.Field()
