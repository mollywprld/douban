from core.requests_crawler import DoubanTop250Crawler
from analysis.data_cleaner import DataCleaner
from analysis.visualization import MovieVisualizer
from analysis.sentiment_analysis import SentimentAnalyzer
from db.mysql_handler import MySQLHandler
from utils.logger import logger
import pandas as pd
import os
import traceback
import sys


def main():
    logger.info("=== 豆瓣电影Top250 爬虫分析系统启动 ===")
    
    crawler = None
    mysql_handler = None
    
    try:
        # 1. 爬取数据（使用上下文管理器）
        logger.info("📌 开始爬取豆瓣Top250数据...")
        with DoubanTop250Crawler() as crawler:
            movies = crawler.crawl_all()
            if not movies:
                logger.error("❌ 未爬取到任何电影数据，退出程序")
                return
            crawler.save_data()

        # 2. 数据清洗
        logger.info("📌 开始数据清洗...")
        raw_data_path = "data/raw/douban_top250_raw.json"
        if not os.path.exists(raw_data_path):
            logger.error(f"❌ 原始数据文件不存在：{raw_data_path}")
            return
        
        cleaner = DataCleaner(raw_data_path)
        cleaner.load()
        cleaner.clean()
        cleaner.save()
        
        # 数据校验
        if cleaner.cleaned_df.empty:
            logger.error("❌ 清洗后无有效数据，退出程序")
            return

        # 3. 数据库存储（使用清洗后的数据，解决 KeyError 问题）
        logger.info("📌 开始将数据存入MySQL数据库...")
        cleaned_movies = cleaner.cleaned_df.to_dict('records')
        try:
            mysql_handler = MySQLHandler(
                host="localhost",
                port=3306,
                user="root",
                password="123456",
                database="douban"
            )
            # 初始化表结构
            mysql_handler.init_tables()
            
            # 插入清洗后的电影数据
            mysql_handler.insert_movies_batch(cleaned_movies)
            
            # 插入短评数据
            all_comments = crawler.get_all_comments()
            if all_comments:
                mysql_handler.insert_comments_batch(all_comments)
            else:
                logger.warning("⚠️ 无短评数据可插入")
            
            logger.info("✅ 数据成功存入MySQL数据库")
        except Exception as e:
            logger.error(f"❌ 数据库存储失败：{e}")
            logger.error(traceback.format_exc())
        finally:
            if mysql_handler:
                mysql_handler.close()
                mysql_handler = None
        
        # 4. 统计分析
        logger.info("📌 开始统计分析...")
        # 4.1 高分电影Top10
        top10 = cleaner.get_top10_movies()
        logger.info("📊 高分电影Top10：")
        logger.info(top10.to_string(index=False))
        
        # 4.2 导演分布
        director_dist = cleaner.get_director_dist()
        logger.info("📊 热门导演分布（Top15）：")
        logger.info(director_dist.to_string())
        
        # 4.3 类型分布
        genre_dist = cleaner.get_genre_dist()
        logger.info("📊 电影类型分布：")
        logger.info(genre_dist.to_string())
        
        # 4.4 评分与评价人数相关性
        corr = cleaner.cleaned_df[['rating', 'comment_num']].corr().iloc[0,1]
        logger.info(f"📊 评分与评价人数相关系数：{corr:.3f}")
        
        # 5. 情感分析
        logger.info("📌 开始短评情感分析...")
        # 提取所有短评内容
        all_comments_text = []
        
        # 优先从数据库/爬虫数据提取
        if crawler and crawler.all_comments:
            for comment in crawler.all_comments:
                if len(comment) >= 4 and comment[3]:
                    all_comments_text.append(comment[3])
        
        if not all_comments_text:
            # 从清洗后的数据补充
            for _, row in cleaner.cleaned_df.iterrows():
                if 'comments' in row and isinstance(row['comments'], list):
                    for comment in row['comments']:
                        if isinstance(comment, dict) and 'content' in comment and comment['content']:
                            all_comments_text.append(comment['content'])
        
        if not all_comments_text:
            logger.warning("⚠️ 无短评数据可分析")
        else:
            # 批量情感分析
            analyzer = SentimentAnalyzer()
            sentiment_results, scores = analyzer.batch_analyze(all_comments_text)
            logger.info("📊 短评情感倾向统计：")
            for sentiment in ['正面', '中性', '负面']:
                count = sentiment_results.get(sentiment, 0)
                percentage = sentiment_results.get(f"{sentiment}占比", "0.0%")
                logger.info(f"{sentiment}：{count}条 ({percentage})")
            
            # 提取关键词
            keywords = analyzer.extract_keywords(all_comments_text)
            logger.info("📊 短评关键词Top20：")
            logger.info(dict(keywords))
        
        # 6. 可视化
        logger.info("📌 开始生成可视化图表...")
        viz = MovieVisualizer(cleaner.cleaned_df)
        viz.plot_rating_dist()          # 评分分布直方图
        viz.plot_genre_pie()            # 类型饼图
        viz.plot_rating_comment_corr()  # 评分-评价人数散点图
        viz.plot_year_trend()           # 年份趋势图
        if all_comments_text:
            all_comments_combined = " ".join(all_comments_text)
            viz.plot_wordcloud(all_comments_combined)  # 短评词云
            if sentiment_results:
                viz.plot_sentiment_dist(sentiment_results)  # 情感分布
        viz.plot_director_dist(director_dist)      # 导演分布
        
        logger.info("=== 系统全部执行完成 ===")
        logger.info(f"📁 所有结果已保存至：{os.path.abspath('data/processed')}")
        
    except Exception as e:
        logger.error(f"❌ 程序执行异常：{e}")
        logger.error(traceback.format_exc())
    finally:
        # 确保资源释放
        if crawler:
            crawler.close()
        if mysql_handler:
            mysql_handler.close()


if __name__ == "__main__":
    main()