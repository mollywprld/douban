# -*- coding: utf-8 -*-
import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import jieba
import numpy as np
import plotly.express as px
import plotly.io as pio
from utils.logger import logger
# 配置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
# 配置Plotly
pio.renderers.default = "browser"  # 浏览器打开交互式图表


class MovieVisualizer:
    """可视化工具类（修复statsmodels依赖问题）"""
    def __init__(self, df):
        self.df = df
        self.save_dir = "data/processed"
        os.makedirs(self.save_dir, exist_ok=True)
        self.color_palette = sns.color_palette("Set2")

    def plot_rating_dist(self):
        """评分分布直方图（优化样式）"""
        plt.figure(figsize=(12, 6))
        sns.histplot(
            self.df['rating'], 
            bins=20, 
            kde=True, 
            color='#FF6B6B', 
            edgecolor='black', 
            alpha=0.7
        )
        # 添加均值线
        mean_rating = self.df['rating'].mean()
        plt.axvline(mean_rating, color='red', linestyle='--', linewidth=2, label=f'平均分：{mean_rating:.2f}')

        plt.title('豆瓣Top250电影评分分布', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('评分', fontsize=14)
        plt.ylabel('电影数量', fontsize=14)
        plt.grid(axis='y', alpha=0.3)
        plt.legend(fontsize=12)
        plt.tight_layout()
        plt.savefig(f'{self.save_dir}/rating_dist.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("✅ 评分分布直方图已生成")

    def plot_genre_pie(self):
        """类型饼图（Top10）"""
        genre_count = self.df['genre'].str.split("|", expand=True).stack().value_counts().head(10)

        plt.figure(figsize=(10, 10))
        # 突出最大占比
        explode = [0.1 if i == 0 else 0.05 for i in range(len(genre_count))]

        wedges, texts, autotexts = plt.pie(
            genre_count, 
            labels=genre_count.index, 
            autopct='%1.1f%%', 
            startangle=90,
            colors=self.color_palette,
            explode=explode,
            shadow=True
        )
        # 美化文字
        plt.setp(autotexts, size=11, weight="bold", color="white")
        plt.setp(texts, size=12)
        plt.title('电影类型分布（Top10）', fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig(f'{self.save_dir}/genre_pie.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("✅ 类型饼图已生成")

    def plot_rating_comment_corr(self):
        """评分-评价人数相关性分析（修复statsmodels依赖，用seaborn绘制趋势线）"""
        # 转换评价人数为数值型
        df_corr = self.df.copy()
        df_corr['comment_num'] = pd.to_numeric(df_corr['comment_num'], errors='coerce')
        df_corr = df_corr.dropna(subset=['rating', 'comment_num'])

        # 计算相关系数
        corr = df_corr[['rating', 'comment_num']].corr().iloc[0,1]

        # 静态图（带趋势线，无需statsmodels）
        plt.figure(figsize=(12, 6))
        # 散点图
        sns.scatterplot(
            x='rating', 
            y='comment_num', 
            data=df_corr, 
            hue='rating', 
            palette='viridis', 
            alpha=0.7,
            s=80  # 点大小
        )
        # 趋势线（seaborn的regplot，无需额外依赖）
        sns.regplot(
            x='rating', 
            y='comment_num', 
            data=df_corr, 
            scatter=False, 
            color='red', 
            line_kws={'linestyle': '--', 'linewidth': 2}
        )

        plt.title(f'评分与评价人数相关性 (相关系数: {corr:.3f})', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('评分', fontsize=14)
        plt.ylabel('评价人数', fontsize=14)
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{self.save_dir}/scatter.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 交互式图（去掉trendline，避免statsmodels依赖）
        fig = px.scatter(
            df_corr, 
            x='rating', 
            y='comment_num', 
            hover_data=['title', 'director', 'year'],
            title=f'评分与评价人数相关性 (相关系数: {corr:.3f})',
            color='rating',
            color_continuous_scale=px.colors.sequential.Viridis
        )
        fig.update_layout(
            title_font=dict(size=16, weight='bold'),
            xaxis_title='评分',
            yaxis_title='评价人数',
            font=dict(size=12)
        )
        fig.write_html(f'{self.save_dir}/scatter_interactive.html')
        logger.info("✅ 评分-评价人数散点图已生成")

    def plot_year_trend(self):
        """年份趋势图"""
        # 过滤有效年份
        year_df = self.df[self.df['year'] != "未知年份"].copy()
        year_df['year'] = pd.to_numeric(year_df['year'], errors='coerce')
        year_df = year_df.dropna(subset=['year'])
        year_df = year_df[year_df['year'] >= 1900]  # 过滤异常年份

        # 按十年分组
        year_df['decade'] = (year_df['year'] // 10) * 10
        decade_count = year_df['decade'].value_counts().sort_index()

        plt.figure(figsize=(14, 7))
        ax = decade_count.plot(
            kind='bar', 
            color=self.color_palette, 
            edgecolor='black', 
            alpha=0.8
        )
        # 添加数值标签
        for i, v in enumerate(decade_count):
            ax.text(i, v + 0.5, str(v), ha='center', fontweight='bold', fontsize=10)

        plt.title('高分电影年份分布（按十年）', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('年代', fontsize=14)
        plt.ylabel('电影数量', fontsize=14)
        plt.xticks(rotation=45)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{self.save_dir}/year_trend.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("✅ 年份趋势图已生成")

    def plot_wordcloud(self, text):
        """短评词云（优化样式）"""
        # 文本清洗和分词
        text = self._clean_text_for_wordcloud(text)
        words = jieba.lcut(text)
        words = [w for w in words if w.strip() and w not in self._get_stop_words() and len(w) > 1]
        word_text = ' '.join(words)

        # 生成词云
        wc = WordCloud(
            font_path='msyh.ttc' if os.name == 'nt' else '/System/Library/Fonts/PingFang.ttc',
            width=1600, 
            height=800,
            background_color='white',
            colormap='tab20',
            max_words=300,
            max_font_size=120,
            random_state=42,
            mask=None,
            contour_width=2,
            contour_color='steelblue'
        ).generate(word_text)

        plt.figure(figsize=(16, 8))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(f'{self.save_dir}/wordcloud.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("✅ 短评词云已生成")

    def plot_sentiment_dist(self, sentiment_results):
        """情感分布可视化"""
        # 提取数据
        labels = ['正面', '中性', '负面']
        values = [sentiment_results.get(l, 0) for l in labels]
        percentages = [sentiment_results.get(f"{l}占比", "0.0%") for l in labels]

        # 绘图
        plt.figure(figsize=(8, 6))
        bars = plt.bar(labels, values, color=['#4CAF50', '#FFC107', '#F44336'], alpha=0.8, edgecolor='black')

        # 添加数值和百分比标签
        for bar, val, pct in zip(bars, values, percentages):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                     f'{val}条\n({pct})',
                     ha='center', va='bottom', fontweight='bold')

        plt.title('短评情感倾向分布', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('情感倾向', fontsize=14)
        plt.ylabel('短评数量', fontsize=14)
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{self.save_dir}/sentiment_dist.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("✅ 情感分布直方图已生成")

    def plot_director_dist(self, director_dist):
        """导演分布可视化（Top15）"""
        top15_director = director_dist.head(15)

        plt.figure(figsize=(12, 8))
        bars = top15_director.plot(kind='barh', color=self.color_palette, edgecolor='black', alpha=0.8)

        # 添加数值标签
        for bar in bars.patches:
            width = bar.get_width()
            plt.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                     f'{int(width)}',
                     ha='left', va='center', fontweight='bold')

        plt.title('热门导演电影数量分布（Top15）', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('电影数量', fontsize=14)
        plt.ylabel('导演', fontsize=14)
        plt.gca().invert_yaxis()  # 反转y轴，数量多的在上面
        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{self.save_dir}/director_dist.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("✅ 导演分布直方图已生成")

    def _clean_text_for_wordcloud(self, text):
        """清洗词云文本"""
        import re
        # 去除特殊符号、数字、英文
        text = re.sub(r'[^\u4e00-\u9fa5]', ' ', text)
        # 去除多余空格
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _get_stop_words(self):
        """获取停用词"""
        return {
            '的', '了', '和', '是', '我', '也', '都', '有', '就', '不', '在', '很', '去', '也', '还', '又',
            '你', '他', '她', '它', '我们', '你们', '他们', '她们', '它们', '这个', '那个', '这些', '那些',
            '什么', '怎么', '这样', '那样', '非常', '超级', '真的', '实在', '简直', '根本', '几乎', '差不多',
            '然后', '之后', '之前', '现在', '时候', '因为', '所以', '虽然', '但是', '而且', '并且', '或者',
            '还是', '还有', '就是', '只是', '只有', '只要', '只有', '不管', '无论', '即使', '虽然', '尽管',
            '电影', '影片', '片子', '导演', '演员', '剧情', '故事', '画面', '音乐', '台词', '表演', '角色',
            '自己', '别人', '大家', '所有人', '每个人', '第一次', '第二次', '最后', '终于', '最终', '结束',
            '开始', '开头', '结尾', '结局', '过程', '结果', '原因', '理由', '方式', '方法', '地方', '时间',
            '知道', '觉得', '认为', '看到', '发现', '感觉', '喜欢', '讨厌', '害怕', '感动', '难过', '开心',
            '人生', '生活', '世界', '社会', '家庭', '朋友', '亲人', '爱人', '孩子', '父母', '兄弟', '姐妹',
            '这里', '那里', '哪里', '这里', '那里', '哪里', '上面', '下面', '里面', '外面', '前面', '后面',
            '一个', '两个', '三个', '几个', '很多', '许多', '大部分', '全部', '所有', '整个', '部分', '一些',
            '一点', '一些', '很多', '许多', '非常', '特别', '极其', '相当', '比较', '稍微', '略微', '几乎',
            '完全', '绝对', '彻底', '全部', '所有', '整个', '整体', '部分', '局部', '个别', '单独', '独自',
            '一起', '共同', '同时', '同步', '立刻', '马上', '赶紧', '赶快', '迅速', '快速', '缓慢', '逐渐',
            '终于', '最终', '最后', '末了', '结尾', '结局', '结束', '终止', '停止', '开始', '开头', '开端',
            '因为', '由于', '鉴于', '基于', '所以', '因此', '因而', '于是', '从而', '导致', '造成', '引起',
            '虽然', '尽管', '虽说', '即使', '就算', '哪怕', '但是', '可是', '然而', '不过', '只是', '只不过',
            '而且', '并且', '同时', '此外', '另外', '还有', '再者', '何况', '况且', '或者', '或是', '还是',
            '不是', '没有', '无', '非', '否', '不', '没', '别', '莫', '非', '无', '没有', '不是', '不对',
            '好', '坏', '高', '低', '大', '小', '多', '少', '远', '近', '快', '慢', '热', '冷', '暖', '凉',
            '新', '旧', '老', '少', '年轻', '年老', '古老', '现代', '传统', '时尚', '流行', '过时', '老旧',
            '好看', '难看', '漂亮', '丑陋', '美丽', '丑恶', '善良', '邪恶', '正义', '邪恶', '光明', '黑暗',
            '快乐', '悲伤', '开心', '难过', '高兴', '伤心', '兴奋', '低落', '激动', '平静', '愤怒', '温和',
            '害怕', '恐惧', '勇敢', '懦弱', '坚强', '脆弱', '坚定', '动摇', '执着', '放弃', '坚持', '妥协',
            '成功', '失败', '胜利', '失利', '赢', '输', '得', '失', '获得', '失去', '得到', '丧失', '拥有',
            '存在', '消失', '出现', '离去', '来', '去', '进', '出', '上', '下', '前', '后', '左', '右', '里', '外'
        }