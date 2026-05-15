# 🎬 豆瓣电影 Top250 爬虫 & 数据分析系统
> 一套完整、可直接运行的豆瓣 Top250 数据采集 + 清洗 + 入库 + 分析 + 可视化项目

GitHub：https://github.com/mollywprld/douban

---

## 📌 项目概述
- 本项目基于 **Python + Requests + Selenium + Scrapy + MySQL + Pandas + Matplotlib/WordCloud**，

  实现**豆瓣电影 Top250 全链路数据采集与智能分析**。

  **核心能力：**

  - 自动爬取豆瓣 Top250 全部 250 部电影
  - 动态渲染详情页，获取年份、片长、类型、IMDb、短评
  - 批量下载高清电影海报
  - 结构化清洗、去重、异常处理
  - MySQL 关系型数据库持久化（movies + comments 外键关联）
  - 统计分析、导演 / 类型 / 年份分布、评分热度相关性
  - 短评情感分析（正面 / 中性 / 负面）
  - 高频关键词词云、交互式可视化
  - 支持 **Requests（轻量）+ Scrapy（高性能）** 双爬虫架构

  **最终产出：**

  - ✅ **250 部电影结构化数据**
  - ✅ **3750 条用户短评（每部 15 条）**
  - ✅ **250 张高清电影海报**
  - ✅ **7 类专业可视化图表**
  - ✅ **完整 MySQL 数据表**

---

## 📁 目录结构（完整）
```
douban/
├── main.py                     # 项目主入口（一键执行全流程）
├── requirements.txt            # 所有依赖包
├── comparison_results.json     # 爬虫性能对比结果
├── performance_comparison.py   # 爬虫性能对比代码
├── tes.py                       # 临时测试数据库脚本
├── README.md
├── msedgedriver.exe            # Selenium Edge 浏览器驱动
│
├── core/                        # 爬虫核心模块
│   ├── requests_crawler.py     # Requests 列表页爬虫
│   ├── selenium_crawler.py     # Selenium 详情+短评爬虫
│   ├── base_crawler.py         # 爬虫基类
│   └── image_downloader.py     # 海报下载工具
│
├── analysis/                    # 数据分析模块
│   ├── data_cleaner.py         # 数据清洗、结构化
│   ├── sentiment_analysis.py   # 短评情感分析、关键词提取
│   └── visualization.py        # 可视化图表生成
│
├── db/                          # 数据库模块
│   ├── mysql_handler.py        # MySQL 连接、建表、插入
│   └── create_tables.sql       # SQL 建表脚本
│
├── scrapy_douban/              # Scrapy 高性能爬虫（备用）
│   ├── scrapy_douban/
│   │   ├── items.py                 # Scrapy 数据模型
│   │   ├── pipelines.py             # 数据管道（JSON/CSV/SQLite）
│   │   ├── middlewares.py          # 反爬中间件
│   │   ├── middlewares_backup.py   # 中间件备份
│   │   ├── settings.py              # Scrapy 配置
│   │   └── spiders/
│   │       └── douban_spider.py    # Scrapy 爬虫主逻辑
│   ├── posters_scrapy/          # Scrapy 版海报
│   ├── douban_scrapy.json       # Scrapy 原始数据
│   ├── douban_scrapy.db         # SQLite 数据库
│   ├── movies_scrapy.csv        # 电影 CSV
│   └── comments_scrapy.csv      # 评论 CSV
│
├── utils/                       # 工具类
│   ├── logger.py                # 日志配置
│   ├── user_agents.py           # 随机 UA 池
│   └── proxy_pool.py            # 代理池
│
├── data/                        # 数据输出目录
│   ├── raw/                     # 原始爬取数据
│   │   └── douban_top250_raw.json
│   ├── processed/               # 清洗后数据 + 可视化
│   │   ├── cleaned_movies.csv
│   │   ├── cleaned_movies.xlsx
│   │   ├── cleaned_movies.json
│   │   ├── rating_dist.png
│   │   ├── genre_pie.png
│   │   ├── scatter.png
│   │   ├── year_trend.png
│   │   ├── director_dist.png
│   │   ├── sentiment_dist.png
│   │   └── wordcloud.png
│   └── images/                  # 所有电影海报
│
├── logs/                        # 运行日志
└── .vscode/                     # VSCode 配置
```

---

## 🧩 文件功能说明
### 1. 主程序
- `main.py`：**一键执行**爬虫 → 清洗 → 入库 → 分析 → 可视化。
- `requirements.txt`：项目所有依赖包。
- `comparison_results.json`：Requests vs Scrapy 性能对比结果。
- `msedgedriver.exe`：Selenium Edge 浏览器驱动。
- `performance_comparison.py`：性能对比测试脚本。

### 2. core（爬虫核心）
- `requests_crawler.py`：爬取 Top250 列表页（排名、标题、评分、简介）。
- `selenium_crawler.py`：动态爬取详情页（年份、片长、类型、IMDb、短评）。
- `base_crawler.py`：爬虫基类（随机延时、UA/代理更新、重试）。
- `image_downloader.py`：批量下载电影海报，支持断点续传、去重。

### 3. analysis（数据分析）
- `data_cleaner.py`：清洗原始 JSON → 结构化（导演、类型、主演、年份）。
- `sentiment_analysis.py`：短评情感分析（正面/中性/负面）、关键词提取。
- `visualization.py`：生成直方图、饼图、散点、趋势、词云等图表。

### 4. db（数据库）
- `mysql_handler.py`：MySQL 连接、自动建表、批量插入电影/评论。
- `create_tables.sql`：标准 SQL 建表脚本。

### 5. scrapy_douban（备用高性能爬虫）
- `items.py`：Scrapy 数据模型。
- `pipelines.py`：JSON/CSV/SQLite 导出管道。
- `middlewares.py`：UA、延时、重试中间件。
- `settings.py`：Scrapy 全局配置。
- `douban_spider.py`：Scrapy 爬虫主逻辑。

### 6. utils（工具）
- `logger.py`：日志输出（控制台 + 文件）。
- `user_agents.py`：随机 User-Agent 池。
- `proxy_pool.py`：代理池（可扩展）。

### 7. data（数据目录）
- `data/raw/`：**原始未清洗 JSON**。
- `data/processed/`：**清洗后数据 + 所有可视化图**。
- `data/images/`：**全部电影海报**。

### 8. logs
- 程序运行日志，便于排错。

---

## 🚀 快速运行
```bash
# 1. 克隆仓库
git clone https://github.com/mollywprld/douban.git
cd douban

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 MySQL（本地默认：root/123456）
# 4. 一键执行
python main.py
```

---

## 📊 输出结果
### ✅ 爬取数据
- 电影：**250 条**
- 短评：**3750 条（每部 15 条）**
- 海报：**250 张**

### ✅ MySQL 表结构
- ### movies 表（MySQL）

  - `rank_num`：排名
  - `title`：中文标题
  - `rating`：评分
  - `comment_num`：评价人数
  - `genre`：电影类型
  - `director`：导演
  - `actors`：主演
  - `year`：上映年份
  - `runtime`：片长
  - `imdb`：IMDb
  - `info`：原始信息
  - `quote`：经典台词

- ### comments 表（MySQL）

  - `movie_id`：关联电影 ID
  - `username`：用户名
  - `rating`：用户评分
  - `content`：短评内容
  - `time`：评论时间

### ✅ 可视化图表（自动生成）
- 评分分布直方图
- 电影类型饼图
- 评分-评论散点图
- 年份趋势图
- 导演分布图
- 情感分布柱状图
- 短评词云

## ✅ 项目特点

- ✅ **完整双爬虫架构**：Requests（轻量）+ Scrapy（高性能）
- ✅ **全自动流程**：爬取→清洗→入库→分析→可视化
- ✅ **动态渲染支持**：Selenium 无头浏览器
- ✅ **数据结构化**：导演、类型、主演自动解析
- ✅ **MySQL 外键关联**：数据完整性强
- ✅ **情感分析 + 词云**：NLP 能力
- ✅ **专业可视化**：7 类图表
- ✅ **完善反爬**：UA、延时、重试、Cookie
- ✅ **海报批量下载**：断点续传
- ✅ **完整日志 + 异常处理**