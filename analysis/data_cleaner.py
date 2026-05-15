import pandas as pd
import json
import os
import re
from utils.logger import logger

class DataCleaner:
    """数据清洗器（修复电影类型提取）"""
    def __init__(self, raw_data_path):
        self.raw_data_path = raw_data_path
        self.df = None
        self.cleaned_df = None

    def load(self):
        """加载原始数据（支持JSON/CSV）"""
        try:
            if self.raw_data_path.endswith('.json'):
                with open(self.raw_data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.df = pd.DataFrame(data)
            elif self.raw_data_path.endswith('.csv'):
                self.df = pd.read_csv(self.raw_data_path, encoding="utf-8-sig")
            else:
                raise ValueError("仅支持JSON/CSV格式")
            
            logger.info(f"原始数据加载完成，共{len(self.df)}条")
            return self.df
        except Exception as e:
            logger.error(f"数据加载失败：{e}")
            raise e

    def clean(self):
        """数据清洗主流程"""
        if self.df is None:
            raise ValueError("请先调用load()加载数据")
        
        logger.info("开始数据清洗...")
        logger.info(f"清洗前缺失值统计：\n{self.df.isnull().sum()}")
        
        # 1. 核心字段去重
        self.cleaned_df = self.df.dropna(subset=["rank_num", "title", "rating"]).reset_index(drop=True)
        
        # 2. 缺失值填充（确保quote台词不显示为空）
        fill_values = {
            "quote": "无经典台词",
            "info": "无详细信息",
            "comment_num": 0,
            "detail_url": "",
            "year": "未知年份",
            "runtime": "未知片长",
            "imdb": "",
            "director": "未知导演",
            "genre": "未知类型",
            "actors": "未知主演"
        }
        self.cleaned_df = self.cleaned_df.fillna(fill_values)
        
        # 3. 数据类型转换
        self._convert_data_types()
        
        # 4. 提取结构化信息（核心修复：导演、主演、类型）
        self._extract_movie_info()
        
        # 5. 去重和异常值过滤
        self.cleaned_df = self.cleaned_df.drop_duplicates(subset=["title", "rating"]).reset_index(drop=True)
        self.cleaned_df = self.cleaned_df[(self.cleaned_df["rating"] >= 0) & (self.cleaned_df["rating"] <= 10)]
        
        logger.info(f"清洗完成，剩余{len(self.cleaned_df)}条有效数据")
        logger.info(f"清洗后缺失值统计：\n{self.cleaned_df.isnull().sum()}")
        return self.cleaned_df

    def _convert_data_types(self):
        """安全的数据类型转换"""
        # 排名
        self.cleaned_df["rank_num"] = pd.to_numeric(
            self.cleaned_df["rank_num"], 
            errors="coerce"
        ).fillna(0).astype(int)
        
        # 评分
        self.cleaned_df["rating"] = pd.to_numeric(
            self.cleaned_df["rating"], 
            errors="coerce"
        ).fillna(0.0).round(1)
        
        # 评价人数
        self.cleaned_df["comment_num"] = self.cleaned_df["comment_num"].astype(str).str.replace(",", "")
        self.cleaned_df["comment_num"] = pd.to_numeric(
            self.cleaned_df["comment_num"], 
            errors="coerce"
        ).fillna(0).astype(int)

    def _extract_movie_info(self):
        """从info字段提取结构化信息（核心修复：正确提取电影类型）"""
        # 提取导演（从info第一行提取）
        def extract_director(info):
            lines = info.split("\n")
            first_line = lines[0] if len(lines) > 0 else ""
            if "导演:" in first_line:
                director_part = first_line.split("导演:")[1].split("主演:")[0].strip()
                # 优先提取中文导演名
                director_match = re.search(r'([\u4e00-\u9fa5·]+)', director_part)
                if director_match:
                    return director_match.group(1).strip()
                return director_part.split()[0] if director_part else "未知导演"
            return "未知导演"
        
        # 提取年份（从info第二行提取）
        def extract_year(info):
            lines = info.split("\n")
            second_line = lines[1] if len(lines) > 1 else info
            year_match = re.search(r'(\d{4})', second_line)
            return year_match.group(1) if year_match else "未知年份"
        
        # 提取电影类型（核心修复：从info第二行提取，输出「犯罪 剧情 爱情」格式）
        def extract_genre(info):
            lines = info.split("\n")
            second_line = lines[1] if len(lines) > 1 else info
            # 按/分割，最后一部分就是类型，直接返回空格分隔的格式
            if "/" in second_line:
                genre_part = second_line.split("/")[-1].strip()
                # 清理多余空格和特殊字符
                genre_part = re.sub(r'\s+', ' ', genre_part).strip()
                return genre_part if genre_part else "未知类型"
            return "未知类型"
        
        # 提取主演（从info第一行提取）
        def extract_actors(info):
            lines = info.split("\n")
            first_line = lines[0] if len(lines) > 0 else ""
            if "主演:" in first_line:
                actors_part = first_line.split("主演:")[1].strip()
                # 提取前3个中文主演
                actors_list = re.findall(r'([\u4e00-\u9fa5·]+)', actors_part)
                if actors_list:
                    return "、".join(actors_list[:3])
                return actors_part[:50] if actors_part else "未知主演"
            return "未知主演"
        
        # 应用提取函数（覆盖原有字段）
        self.cleaned_df["director"] = self.cleaned_df["info"].apply(extract_director)
        self.cleaned_df["year"] = self.cleaned_df["info"].apply(extract_year)
        self.cleaned_df["genre"] = self.cleaned_df["info"].apply(extract_genre)
        self.cleaned_df["actors"] = self.cleaned_df["info"].apply(extract_actors)

    def save(self):
        """保存清洗后的数据"""
        if self.cleaned_df is None:
            raise ValueError("请先调用clean()清洗数据")
        
        save_dir = "data/processed"
        os.makedirs(save_dir, exist_ok=True)
        
        # 保存为Excel（便于查看）
        excel_path = os.path.join(save_dir, "cleaned_movies.xlsx")
        self.cleaned_df.to_excel(excel_path, index=False, engine="openpyxl")
        
        # 保存为CSV（便于后续分析）
        csv_path = os.path.join(save_dir, "cleaned_movies.csv")
        self.cleaned_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        
        # 保存为JSON
        json_path = os.path.join(save_dir, "cleaned_movies.json")
        self.cleaned_df.to_json(json_path, orient="records", force_ascii=False, indent=2)
        
        logger.info(f"清洗后数据已保存到：{save_dir}")
        return save_dir

    # 统计方法
    def get_top10_movies(self):
        """获取高分电影Top10"""
        return self.cleaned_df.sort_values(by="rating", ascending=False).head(10)[
            ["rank_num", "title", "rating", "comment_num", "director"]
        ]
    
    def get_director_dist(self, top_n=15):
        """获取导演作品数量分布"""
        return self.cleaned_df["director"].value_counts().head(top_n)
    
    def get_genre_dist(self):
        """获取电影类型分布"""
        genres = []
        for g in self.cleaned_df["genre"]:
            if g and g != "未知类型":
                genres.extend(g.split(" "))
        return pd.Series(genres).value_counts()
    
    def get_year_dist(self):
        """获取年份分布"""
        year_df = self.cleaned_df[self.cleaned_df["year"] != "未知年份"]
        return year_df["year"].value_counts().sort_index()