from snownlp import SnowNLP
import pandas as pd
import jieba
from collections import Counter
import re
from utils.logger import logger

class SentimentAnalyzer:
    """情感分析器（优化分词和关键词提取）"""
    def __init__(self):
        # 扩展停用词表
        self.stop_words = {
            "的", "了", "是", "我", "你", "他", "它", "都", "也", "和", "就", "不", "在", "有", 
            "这", "那", "而", "于", "之", "但", "却", "还", "又", "只", "更", "很", "最", "还",
            "一个", "一部", "一点", "一些", "所有", "任何", "没有", "可以", "可能", "应该", "因为",
            "所以", "虽然", "但是", "如果", "那么", "比如", "例如", "就是", "只是", "不过", "其实"
        }
        # 加载自定义词典（提升分词准确性）
        try:
            jieba.load_userdict("data/dict/movie_dict.txt")
        except:
            logger.warning("未找到自定义词典，使用默认分词")

    def clean_text(self, text):
        """文本清洗（去特殊字符、空格）"""
        if not text or pd.isna(text):
            return ""
        # 移除特殊字符
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', text)
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def analyze(self, text):
        """单条文本情感分析"""
        clean_text = self.clean_text(text)
        if not clean_text:
            return "中性", 0.5
        
        try:
            s = SnowNLP(clean_text)
            score = s.sentiments
            if score > 0.7:
                return "正面", round(score, 3)
            elif score < 0.3:
                return "负面", round(score, 3)
            else:
                return "中性", round(score, 3)
        except Exception as e:
            logger.warning(f"情感分析失败：{e} | 文本：{text[:20]}")
            return "中性", 0.5
    
    def batch_analyze(self, texts):
        """批量分析（优化性能）"""
        results = {"正面": 0, "中性": 0, "负面": 0}
        scores = []
        valid_texts = [self.clean_text(t) for t in texts if t]
        
        for text in valid_texts:
            sentiment, score = self.analyze(text)
            results[sentiment] += 1
            scores.append(score)
        
        # 计算占比
        total = sum(results.values())
        if total > 0:
            results["正面占比"] = f"{results['正面']/total*100:.1f}%"
            results["中性占比"] = f"{results['中性']/total*100:.1f}%"
            results["负面占比"] = f"{results['负面']/total*100:.1f}%"
        
        return results, scores
    
    def extract_keywords(self, texts, top_n=20):
        """提取关键词（优化分词）"""
        all_words = []
        valid_texts = [self.clean_text(t) for t in texts if t]
        
        for text in valid_texts:
            # 精确模式分词
            words = jieba.lcut(text, cut_all=False)
            # 过滤停用词和短词
            words = [
                w for w in words 
                if w.strip() and w not in self.stop_words and len(w) > 1
            ]
            all_words.extend(words)
        
        # 统计词频
        word_count = Counter(all_words)
        return word_count.most_common(top_n)
    
    def get_sentiment_score_avg(self, scores):
        """计算平均情感得分"""
        if not scores:
            return 0.5
        return round(sum(scores)/len(scores), 3)