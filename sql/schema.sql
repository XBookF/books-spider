-- 建库建表（面试可讲：唯一索引保证幂等，重复采集不会产生重复数据）
CREATE DATABASE IF NOT EXISTS books_db DEFAULT CHARSET utf8mb4;
USE books_db;

CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    upc VARCHAR(32) NOT NULL UNIQUE COMMENT '商品唯一编码，天然去重键',
    title VARCHAR(255) NOT NULL,
    category VARCHAR(64),
    price DECIMAL(10, 2),
    price_excl_tax DECIMAL(10, 2),
    tax DECIMAL(10, 2),
    rating TINYINT,
    stock INT,
    reviews INT DEFAULT 0,
    description TEXT,
    image_url VARCHAR(512),
    detail_url VARCHAR(512),
    crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_price (price)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 常用查询（面试可能让你现场写）
-- 1. 每个分类的书籍数量和均价
SELECT category, COUNT(*) AS cnt, ROUND(AVG(price), 2) AS avg_price
FROM books GROUP BY category ORDER BY cnt DESC;

-- 2. 价格最高的 10 本书
SELECT title, price, rating FROM books ORDER BY price DESC LIMIT 10;

-- 3. 评分不低于 4 星且库存大于 10 的书
SELECT title, rating, stock FROM books WHERE rating >= 4 AND stock > 10;

-- 4. 分页查询（limit offset 写法）
SELECT title, price FROM books ORDER BY id LIMIT 0, 20;
