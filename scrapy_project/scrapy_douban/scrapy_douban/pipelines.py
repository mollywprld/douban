# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

logger = logging.getLogger(__name__)


class SQLitePipeline:
    """SQLite数据库存储管道"""

    def __init__(self, db_path: str = 'douban_scrapy.db'):
        self.db_path = Path(db_path)
        self.connection = None
        self.cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        db_path = crawler.settings.get('SQLITE_DB_PATH', 'douban_scrapy.db')
        return cls(db_path)

    def open_spider(self, spider):
        """Spider启动时创建数据库和表"""
        self.connection = sqlite3.connect(str(self.db_path))
        self.cursor = self.connection.cursor()

        # 创建movies表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rank TEXT NOT NULL,
                title_cn TEXT,
                title_en TEXT,
                rating TEXT,
                rating_count TEXT,
                directors_cast TEXT,
                quote TEXT,
                detail_link TEXT UNIQUE,
                year TEXT,
                duration TEXT,
                genre TEXT,
                imdb_rating TEXT,
                poster_url TEXT,
                poster_path TEXT,
                crawled_at TEXT,
                spider_name TEXT
            )
        ''')

        # 创建comments表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_id INTEGER NOT NULL,
                author TEXT,
                score TEXT,
                content TEXT,
                time TEXT,
                FOREIGN KEY (movie_id) REFERENCES movies (id)
            )
        ''')

        self.connection.commit()
        logger.info(f"Database initialized: {self.db_path}")

    def close_spider(self, spider):
        """Spider关闭时提交事务并关闭连接"""
        if self.connection:
            self.connection.commit()
            self.connection.close()
            logger.info("Database connection closed")

    def process_item(self, item, spider):
        """处理每个Item"""
        adapter = ItemAdapter(item)

        # 插入电影数据
        movie_data = dict(adapter)
        hot_comments = movie_data.pop('hot_comments', [])

        # 插入电影
        self.cursor.execute('''
            INSERT OR REPLACE INTO movies
            (rank, title_cn, title_en, rating, rating_count, directors_cast, quote,
             detail_link, year, duration, genre, imdb_rating, poster_url, poster_path,
             crawled_at, spider_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            movie_data.get('rank'),
            movie_data.get('title_cn'),
            movie_data.get('title_en'),
            movie_data.get('rating'),
            movie_data.get('rating_count'),
            movie_data.get('directors_cast'),
            movie_data.get('quote'),
            movie_data.get('detail_link'),
            movie_data.get('year'),
            movie_data.get('duration'),
            movie_data.get('genre'),
            movie_data.get('imdb_rating'),
            movie_data.get('poster_url'),
            movie_data.get('poster_path'),
            movie_data.get('crawled_at'),
            movie_data.get('spider_name')
        ))

        movie_id = self.cursor.lastrowid

        # 插入评论数据
        for comment in hot_comments:
            self.cursor.execute('''
                INSERT INTO comments (movie_id, author, score, content, time)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                movie_id,
                comment.get('author'),
                comment.get('score'),
                comment.get('content'),
                comment.get('time')
            ))

        logger.debug(f"Processed movie: {movie_data.get('title_cn')}")
        return item


class JsonExportPipeline:
    """JSON导出管道"""

    def __init__(self, output_file: str = 'douban_scrapy.json'):
        self.output_file = Path(output_file)
        self.items = []

    @classmethod
    def from_crawler(cls, crawler):
        output_file = crawler.settings.get('JSON_OUTPUT_FILE', 'douban_scrapy.json')
        return cls(output_file)

    def open_spider(self, spider):
        """Spider启动时初始化"""
        self.items = []
        logger.info(f"JSON export initialized: {self.output_file}")

    def close_spider(self, spider):
        """Spider关闭时保存JSON文件"""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)
        logger.info(f"Exported {len(self.items)} items to {self.output_file}")

    def process_item(self, item, spider):
        """收集所有Item"""
        adapter = ItemAdapter(item)
        self.items.append(dict(adapter))
        return item


class CsvExportPipeline:
    """CSV导出管道"""

    def __init__(self, movies_file: str = 'movies_scrapy.csv', comments_file: str = 'comments_scrapy.csv'):
        self.movies_file = Path(movies_file)
        self.comments_file = Path(comments_file)
        self.movies_data = []
        self.comments_data = []

    @classmethod
    def from_crawler(cls, crawler):
        movies_file = crawler.settings.get('CSV_MOVIES_FILE', 'movies_scrapy.csv')
        comments_file = crawler.settings.get('CSV_COMMENTS_FILE', 'comments_scrapy.csv')
        return cls(movies_file, comments_file)

    def open_spider(self, spider):
        """Spider启动时初始化"""
        self.movies_data = []
        self.comments_data = []
        logger.info(f"CSV export initialized: {self.movies_file}, {self.comments_file}")

    def close_spider(self, spider):
        """Spider关闭时保存CSV文件"""
        import csv

        # 保存电影数据
        if self.movies_data:
            movie_fieldnames = sorted({key for item in self.movies_data for key in item.keys()})
            with open(self.movies_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=movie_fieldnames)
                writer.writeheader()
                writer.writerows(self.movies_data)
            logger.info(f"Exported {len(self.movies_data)} movies to {self.movies_file}")

        # 保存评论数据
        if self.comments_data:
            comment_fieldnames = sorted({key for item in self.comments_data for key in item.keys()})
            with open(self.comments_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=comment_fieldnames)
                writer.writeheader()
                writer.writerows(self.comments_data)
            logger.info(f"Exported {len(self.comments_data)} comments to {self.comments_file}")

    def process_item(self, item, spider):
        """处理每个Item"""
        adapter = ItemAdapter(item)
        item_dict = dict(adapter)

        # 添加电影数据
        movie_data = {k: v for k, v in item_dict.items() if k != 'hot_comments'}
        self.movies_data.append(movie_data)

        # 添加评论数据
        movie_id = len(self.movies_data)  # 简单的主键
        for comment in item_dict.get('hot_comments', []):
            comment_data = {
                'movie_id': movie_id,
                'author': comment.get('author'),
                'score': comment.get('score'),
                'content': comment.get('content'),
                'time': comment.get('time')
            }
            self.comments_data.append(comment_data)

        return item


class ValidationPipeline:
    """数据验证管道"""

    def process_item(self, item, spider):
        """验证Item数据的完整性"""
        adapter = ItemAdapter(item)

        # 检查必需字段
        required_fields = ['rank', 'title_cn', 'rating', 'detail_link']
        for field in required_fields:
            if not adapter.get(field):
                logger.warning(f"Missing required field '{field}' for item: {adapter.get('title_cn')}")

        # 验证评分范围
        rating = adapter.get('rating')
        if rating:
            try:
                rating_float = float(rating)
                if not 0 <= rating_float <= 10:
                    logger.warning(f"Invalid rating {rating} for {adapter.get('title_cn')}")
            except ValueError:
                logger.warning(f"Invalid rating format {rating} for {adapter.get('title_cn')}")

        return item


class ScrapyDoubanPipeline:
    """默认管道（保持兼容性）"""

    def process_item(self, item, spider):
        return item
