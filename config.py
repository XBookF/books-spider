"""项目配置：目标站点、输出目录、MySQL 连接信息（可用环境变量覆盖）"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
IMAGE_DIR = DATA_DIR / "images"
LOG_DIR = DATA_DIR / "logs"
SQL_DIR = BASE_DIR / "sql"

# 目标站点：专为爬虫练习设计，结构稳定，适合演示分页 + 列表页 + 详情页
BASE_URL = "https://books.toscrape.com"
LIST_URL = BASE_URL + "/catalogue/page-{page}.html"

# 请求配置
TIMEOUT = 10          # 单次请求超时（秒）
MAX_RETRIES = 3       # 失败重试次数
DELAY = 0.3           # 每次请求间隔（秒），礼貌爬取
MAX_WORKERS = 8       # 图片下载线程数

# MySQL 配置（本地没有启动 MySQL 时会自动降级为导出 insert.sql）
MYSQL = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "books_db"),
    "charset": "utf8mb4",
}

for _d in (DATA_DIR, IMAGE_DIR, LOG_DIR, SQL_DIR):
    _d.mkdir(parents=True, exist_ok=True)
