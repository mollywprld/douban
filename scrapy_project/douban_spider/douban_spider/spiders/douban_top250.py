import scrapy
import requests

class DoubanTop250Spider(scrapy.Spider):
    name = "douban_top250"
    allowed_domains = ["movie.douban.com"]

    def start_requests(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Cookie': 'bid=kxkFgY9bt8A; dbcl2="295054165:Rc2GBZyAbdM"; ll="118254"; ap_v=0,6.0; ck=gj4C',
            'Referer': 'https://movie.douban.com/top250',
        }

        for start in range(0, 250, 25):
            url = f'https://movie.douban.com/top250?start={start}&filter='
            yield scrapy.Request(url, headers=headers, callback=self.parse)

    def parse(self, response):
        for item in response.xpath('//div[@class="item"]'):
            yield {
                '排名': item.xpath('.//em/text()').get(),
                '片名': item.xpath('.//span[@class="title"][1]/text()').get(),
                '评分': item.xpath('.//span[@class="rating_num"]/text()').get(),
                '评价人数': item.xpath('.//div[@class="star"]/span[last()]/text()').get(),
                '链接': item.xpath('.//div[@class="hd"]/a/@href').get(),
            }