# import pymysql
# import csv
# import json
# from itemadapter import ItemAdapter
# from .items import DoubanMovieItem, DoubanCommentItem

# class MySQLPipeline:
#     def __init__(self):
#         self.conn = pymysql.connect(
#             host="localhost",
#             user="root",
#             password="123456",  # 改成你自己的密码！
#             db="douban",
#             charset="utf8mb4"
#         )
#         self.cursor = self.conn.cursor()

#     def process_item(self, item, spider):
#         if isinstance(item, DoubanMovieItem):
#             sql = """
#             INSERT INTO movies (rank_num, title, title_en, rating, comment_num, info, quote, detail_url, poster_path, year, runtime, imdb)
#             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#             ON DUPLICATE KEY UPDATE rating=VALUES(rating);
#             """
#             self.cursor.execute(sql, (
#                 item.get('rank_num'),
#                 item.get('title'),
#                 item.get('title_en'),
#                 item.get('rating'),
#                 item.get('comment_num'),
#                 item.get('info'),
#                 item.get('quote'),
#                 item.get('detail_url'),
#                 item.get('poster_path'),
#                 item.get('year'),
#                 item.get('runtime'),
#                 item.get('imdb')
#             ))
#         elif isinstance(item, DoubanCommentItem):
#             sql = """
#             INSERT INTO comments (movie_id, username, rating, content, time)
#             VALUES (%s, %s, %s, %s, %s);
#             """
#             self.cursor.execute(sql, (
#                 item.get('movie_id'),
#                 item.get('username'),
#                 item.get('rating'),
#                 item.get('content'),
#                 item.get('time')
#             ))
#         self.conn.commit()
#         return item

#     def close_spider(self, spider):
#         self.cursor.close()
#         self.conn.close()

# class CSVJSONPipeline:
#     def open_spider(self, spider):
#         self.movie_file = open("../../data/scrapy_movies.csv", "w", encoding="utf-8-sig", newline="")
#         self.comment_file = open("../../data/scrapy_comments.csv", "w", encoding="utf-8-sig", newline="")
#         self.movie_writer = csv.DictWriter(self.movie_file, fieldnames=DoubanMovieItem.fields.keys())
#         self.comment_writer = csv.DictWriter(self.comment_file, fieldnames=DoubanCommentItem.fields.keys())
#         self.movie_writer.writeheader()
#         self.comment_writer.writeheader()
#         spider.movie_data = []

#     def process_item(self, item, spider):
#         adapter = ItemAdapter(item)
#         if isinstance(item, DoubanMovieItem):
#             self.movie_writer.writerow(adapter.asdict())
#             spider.movie_data.append(adapter.asdict())
#         elif isinstance(item, DoubanCommentItem):
#             self.comment_writer.writerow(adapter.asdict())
#         return item

#     def close_spider(self, spider):
#         self.movie_file.close()
#         self.comment_file.close()
#         with open("../../data/scrapy_movies.json", "w", encoding="utf-8") as f:
#             json.dump(spider.movie_data, f, ensure_ascii=False, indent=2)