import pymysql
import os
import re
from utils.logger import logger

class MySQLHandler:
    def __init__(self, host='localhost', port=3306, user='root', password='root', database='douban'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None
        self.init_connection()

    def init_connection(self):
        """初始化MySQL连接"""
        logger.info("初始化MySQL连接...")
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            self.cursor = self.connection.cursor()
            logger.info("MySQL连接成功")
        except pymysql.MySQLError as e:
            logger.error(f"MySQL连接失败：{e}")
            raise e

    def create_database(self):
        """创建数据库"""
        try:
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"数据库 {self.database} 创建成功/已存在")
        except pymysql.MySQLError as e:
            logger.error(f"数据库创建失败：{e}")
            raise e

    def use_database(self):
        """选中数据库"""
        try:
            self.cursor.execute(f"USE {self.database}")
            logger.info(f"已选中数据库：{self.database}")
        except pymysql.MySQLError as e:
            logger.error(f"数据库选中失败：{e}")
            raise e

    def table_exists(self, table_name):
        """判断表是否存在"""
        try:
            self.cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            return self.cursor.fetchone() is not None
        except pymysql.MySQLError as e:
            logger.error(f"表存在性检查失败：{e}")
            return False

    def execute_sql_file(self, sql_file_path):
        """执行SQL文件"""
        if not os.path.exists(sql_file_path):
            logger.warning(f"SQL文件不存在：{sql_file_path}")
            return False
        
        logger.info(f"找到SQL文件：{sql_file_path}")
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 拆分SQL语句，过滤空行和注释
            sql_statements = re.split(r';\s*$', sql_content, flags=re.MULTILINE)
            valid_statements = []
            for stmt in sql_statements:
                stmt = stmt.strip()
                if stmt and not stmt.startswith('--') and not stmt.startswith('/*'):
                    valid_statements.append(stmt)
            
            if not valid_statements:
                logger.warning("SQL文件中无有效语句")
                return False
            
            for stmt in valid_statements:
                self.cursor.execute(stmt)
            self.connection.commit()
            logger.info("SQL文件执行成功")
            return True
        except Exception as e:
            logger.error(f"SQL文件执行失败：{e}")
            self.connection.rollback()
            return False

    def create_movies_table(self):
        """自动创建movies表（匹配你的SQL结构）"""
        if self.table_exists('movies'):
            return True
        
        logger.warning("核心表 movies 不存在，将自动创建")
        create_sql = """
        CREATE TABLE IF NOT EXISTS movies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            rank_num INT UNIQUE NOT NULL COMMENT '排名',
            title VARCHAR(255) NOT NULL COMMENT '中文标题',
            rating FLOAT NOT NULL COMMENT '评分',
            comment_num INT DEFAULT 0 COMMENT '评价人数',
            info TEXT COMMENT '电影信息',
            quote TEXT COMMENT '经典台词',
            detail_url VARCHAR(512) DEFAULT '' COMMENT '详情页URL',
            poster_path VARCHAR(512) DEFAULT '' COMMENT '海报路径',
            year VARCHAR(10) DEFAULT '' COMMENT '上映年份',
            runtime VARCHAR(20) DEFAULT '' COMMENT '片长',
            imdb VARCHAR(20) DEFAULT '' COMMENT 'IMDb编号',
            genre VARCHAR(255) DEFAULT '' COMMENT '电影类型',
            director VARCHAR(255) DEFAULT '' COMMENT '导演',
            actors TEXT COMMENT '主演',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        try:
            self.cursor.execute(create_sql)
            self.connection.commit()
            logger.info("表 movies 创建成功")
            return True
        except pymysql.MySQLError as e:
            logger.error(f"表 movies 创建失败：{e}")
            self.connection.rollback()
            return False

    def create_comments_table(self):
        """自动创建comments表（匹配你的SQL结构）"""
        if self.table_exists('comments'):
            return True
        
        logger.warning("核心表 comments 不存在，将自动创建")
        create_sql = """
        CREATE TABLE IF NOT EXISTS comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            movie_id INT NOT NULL COMMENT '电影ID',
            username VARCHAR(100) DEFAULT '' COMMENT '评论用户名',
            rating VARCHAR(20) DEFAULT '' COMMENT '用户评分',
            content TEXT NOT NULL COMMENT '评论内容',
            time VARCHAR(50) DEFAULT '' COMMENT '评论时间',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        try:
            self.cursor.execute(create_sql)
            self.connection.commit()
            logger.info("表 comments 创建成功")
            return True
        except pymysql.MySQLError as e:
            logger.error(f"表 comments 创建失败：{e}")
            self.connection.rollback()
            return False

    def init_tables(self, sql_file_path=None):
        """初始化所有表"""
        self.create_database()
        self.use_database()
        
        # 优先执行SQL文件，失败则自动创建表
        if sql_file_path and self.execute_sql_file(sql_file_path):
            return True
        
        # 自动创建核心表
        self.create_movies_table()
        self.create_comments_table()
        return True

    def truncate_table(self, table_name):
        """清空表数据"""
        try:
            # 先禁用外键约束，避免清空失败
            self.cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            self.cursor.execute(f"TRUNCATE TABLE {table_name}")
            self.cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            self.connection.commit()
            logger.info(f"表 {table_name} 清空成功")
            return True
        except pymysql.MySQLError as e:
            logger.warning(f"TRUNCATE表失败：{e}")
            self.cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            self.connection.rollback()
            return False

    def insert_movies_batch(self, movies_data):
        """批量插入电影数据（字段完全匹配SQL）"""
        if not movies_data:
            logger.warning("无电影数据可插入")
            return 0
        
        self.truncate_table('movies')
        
        insert_sql = """
        INSERT INTO movies (
            rank_num, title, rating, comment_num, info, quote,
            detail_url, poster_path, year, runtime, imdb,
            genre, director, actors
        ) VALUES (
            %(rank_num)s, %(title)s, %(rating)s, %(comment_num)s, %(info)s, %(quote)s,
            %(detail_url)s, %(poster_path)s, %(year)s, %(runtime)s, %(imdb)s,
            %(genre)s, %(director)s, %(actors)s
        )
        """
        try:
            self.cursor.executemany(insert_sql, movies_data)
            self.connection.commit()
            insert_count = self.cursor.rowcount
            logger.info(f"成功插入 {insert_count} 条电影数据")
            return insert_count
        except pymysql.MySQLError as e:
            logger.error(f"电影数据插入失败：{e}")
            self.connection.rollback()
            return 0

    def insert_comments_batch(self, comments_data):
        """批量插入评论数据"""
        if not comments_data:
            logger.warning("无评论数据可插入")
            return 0
        
        self.truncate_table('comments')
        
        insert_sql = """
        INSERT IGNORE INTO comments (
            movie_id, username, rating, content, time
        ) VALUES (
            %(movie_rank)s, %(username)s, %(rating)s, %(content)s, %(comment_time)s
        )
        """
        try:
            self.cursor.executemany(insert_sql, comments_data)
            self.connection.commit()
            insert_count = self.cursor.rowcount
            logger.info(f"成功插入 {insert_count} 条短评数据")
            return insert_count
        except pymysql.MySQLError as e:
            logger.error(f"短评数据插入失败：{e}")
            self.connection.rollback()
            return 0

    def close(self):
        """关闭连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            logger.info("MySQL连接已安全关闭")

# 测试代码
if __name__ == "__main__":
    db = MySQLHandler()
    db.init_tables()
    db.close()