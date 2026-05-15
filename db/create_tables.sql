-- 豆瓣电影Top250数据库表结构
-- 电影表
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

-- 短评表
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