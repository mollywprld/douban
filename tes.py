import pymysql
from pymysql.err import OperationalError

# ====================== 数据库连接配置（你只需要改这里！）======================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",           # 你的MySQL用户名
    "password": "123456",     # 你的MySQL密码
    "charset": "utf8mb4"
}

# 目标数据库名
DB_NAME = "douban"

def test_mysql_demo():
    """MySQL 建库、建表、插入、查询示例"""
    conn = None
    cursor = None

    try:
        # 1. 连接 MySQL（不指定数据库）
        print("正在连接 MySQL...")
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✅ 连接成功")

        # 2. 创建数据库（不存在则创建）
        print(f"\n正在创建数据库：{DB_NAME}")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4")
        print("✅ 数据库创建完成")

        # 3. 选中数据库
        cursor.execute(f"USE {DB_NAME}")

        # 4. 创建电影表
        print("\n正在创建表：movies")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS movies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            rating FLOAT,
            director VARCHAR(100),
            year INT,
            quote TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cursor.execute(create_table_sql)
        print("✅ 表创建完成")

        # 5. 插入示例数据
        print("\n正在插入测试数据...")
        insert_sql = """
        INSERT INTO movies (title, rating, director, year, quote)
        VALUES (%s, %s, %s, %s, %s)
        """

        # 3条测试电影数据
        test_data = [
            ("肖申克的救赎", 9.7, "弗兰克·德拉邦特", 1994, "希望是件好东西，也许是世上最好的东西"),
            ("霸王别姬", 9.6, "陈凯歌", 1993, "说的是一辈子，差一年，一个月，一天，一个时辰，都不算一辈子"),
            ("阿甘正传", 9.5, "罗伯特·泽米吉斯", 1994, "生活就像一盒巧克力，你永远不知道下一颗是什么")
        ]

        # 批量插入
        cursor.executemany(insert_sql, test_data)
        conn.commit()
        print(f"✅ 成功插入 {len(test_data)} 条测试数据")

        # 6. 查询验证
        print("\n===== 查询结果 =====")
        cursor.execute("SELECT * FROM movies")
        results = cursor.fetchall()

        for row in results:
            print(f"排名ID：{row[0]} | 电影：{row[1]} | 评分：{row[2]} | 导演：{row[3]} | 年份：{row[4]}")
            print(f"经典台词：{row[5]}\n")

        print("\n🎉 所有操作执行成功！")

    except OperationalError as e:
        print(f"❌ MySQL 错误：{e}")
    except Exception as e:
        print(f"❌ 程序异常：{e}")
    finally:
        # 关闭连接
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("\n连接已关闭")

if __name__ == "__main__":
    test_mysql_demo()