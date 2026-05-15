import scrapy

class DoubanMovieItem(scrapy.Item):
    rank_num = scrapy.Field()
    title = scrapy.Field()
    title_en = scrapy.Field()
    rating = scrapy.Field()
    comment_num = scrapy.Field()
    info = scrapy.Field()
    quote = scrapy.Field()
    detail_url = scrapy.Field()
    poster_path = scrapy.Field()
    year = scrapy.Field()
    runtime = scrapy.Field()
    imdb = scrapy.Field()

class DoubanCommentItem(scrapy.Item):
    movie_id = scrapy.Field()
    username = scrapy.Field()
    rating = scrapy.Field()
    content = scrapy.Field()
    time = scrapy.Field()