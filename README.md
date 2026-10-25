# books-spider

基于 Python 的电商数据采集示例项目：从分页列表页出发，抓取商品详情与封面图，经过清洗去重后输出 JSON / CSV / Excel，并写入 MySQL。

目标站点为爬虫练习站点 [books.toscrape.com](https://books.toscrape.com/)，结构稳定、允许练习，覆盖了分页、列表页、详情页、图片四类典型场景。

## 功能

- **分页采集**：优先按 URL 规则翻页，同时解析“下一页”节点，不写死总页数
- **双层解析**：列表页使用 BeautifulSoup（CSS 选择器），详情页使用 lxml（XPath）
- **请求稳定性**：Session 复用、连接池、UA、10 秒超时、指数退避重试、请求限速
- **数据清洗**：价格/库存/评分类型转换、必填字段校验、按 UPC 去重、脏数据统计
- **多种输出**：JSON、CSV（utf-8-sig，Excel 打开不乱码）、Excel（表头样式/冻结/筛选）
- **MySQL 入库**：自动建库建表，`upc` 唯一索引 + `ON DUPLICATE KEY UPDATE` 保证幂等
- **图片下载**：线程池并发、失败重试、已存在自动跳过（断点续跑）
- **日志与统计**：控制台 + 文件双日志，输出页数、条数、重复数、失败数、耗时
- **动态页面**：Selenium 抓取 JS 渲染页面的对比示例

## 技术栈

Python 3.10+ · requests · BeautifulSoup4 · lxml · openpyxl · PyMySQL · Selenium

## 项目结构

```
.
├─ main.py                     主流程：翻页 → 详情 → 清洗 → 存储 → 统计
├─ config.py                   站点、超时、重试、MySQL 配置
├─ requirements.txt
├─ spider/
│  ├─ fetcher.py               请求层：Session、Retry、编码、限速、失败记录
│  ├─ parser.py                解析层：CSS 列表页 + XPath 详情页
│  ├─ cleaner.py               清洗层：类型转换、校验、去重
│  ├─ storage.py               存储层：JSON / CSV / Excel / MySQL / SQL 脚本
│  ├─ image_downloader.py      图片批量下载
│  └─ selenium_demo.py         Selenium 动态页面示例
├─ sql/
│  └─ schema.sql               建表语句与常用查询
└─ data/                       运行时生成（已加入 .gitignore）
```

## 快速开始

```bash
pip install -r requirements.txt

# 抓取 3 页（60 条），同时下载封面图
python main.py --pages 3 --images
```

输出：

```
data/books.json      JSON 数据
data/books.csv       UTF-8 BOM，Excel 可直接打开
data/books.xlsx      带表头样式、冻结窗格、筛选
data/images/         封面图（按 UPC 命名）
data/logs/spider.log 运行日志
```

### 写入 MySQL

默认连接 `127.0.0.1:3306`，库名 `books_db`，账号密码通过环境变量传入：

```bash
# Windows PowerShell
$env:MYSQL_PASSWORD="你的密码"
python main.py --pages 3

# macOS / Linux
export MYSQL_PASSWORD="你的密码"
python main.py --pages 3
```

也可以覆盖 `MYSQL_HOST`、`MYSQL_PORT`、`MYSQL_USER`、`MYSQL_DATABASE`。

首次运行会自动创建数据库和 `books` 表；连接失败时会自动降级导出 `sql/insert_books.sql`，可在 MySQL 中手动执行。

### 动态页面示例

```bash
python spider/selenium_demo.py
```

同一页面：`requests` 只能解析到 0 条（内容由 JS 渲染），Selenium 渲染后解析到 10 条。

## 数据字段

`upc`、`title`、`category`、`price`、`price_excl_tax`、`tax`、`rating`、`stock`、`reviews`、`description`、`image_url`、`detail_url`

## 设计说明

- **为什么用 Session**：复用 TCP 连接与 Cookie，配合连接池和 `Retry` 统一处理重试与退避。
- **为什么两种解析方式**：列表页结构规整，CSS 选择器更简洁；详情页是 `th/td` 规格表，XPath 表达更自然。
- **为什么按 UPC 去重**：UPC 是商品唯一编码，内存 `set`、数据库唯一索引、UPSERT 三层都依赖它。
- **为什么价格用 DECIMAL**：金额不能有浮点误差，`DECIMAL(10,2)` 精确到分。
- **为什么 CSV 用 utf-8-sig**：Windows Excel 默认按 GBK 打开，带 BOM 才不会中文乱码。
- **编码兜底**：站点未声明 charset 时 `requests` 会按 ISO-8859-1 解码，用 `apparent_encoding` 修正。
- **先连服务再建库**：连接参数指定不存在的数据库会直接报 1049，因此先连接服务、创建数据库、再 `USE`。

## 说明

本项目仅用于学习与练习，目标站点为公开的爬虫练习站点。请遵守目标网站的 robots.txt 与服务条款，控制请求频率，不采集隐私数据。
