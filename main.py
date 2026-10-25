"""主流程：分页爬取 → 详情解析 → 清洗去重 → JSON/CSV/Excel/MySQL → 图片下载 → 统计"""
import argparse
import json
import logging
import time

import config
from spider.cleaner import build_record, clean_records
from spider.fetcher import Fetcher
from spider.image_downloader import download_images
from spider.parser import parse_detail_page, parse_list_page
from spider.storage import save_csv, save_excel, save_json, save_mysql, save_sql_file
from urllib.parse import urljoin


def setup_logging():
    log_file = config.LOG_DIR / "spider.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def crawl(pages, delay, with_images):
    start = time.time()
    fetcher = Fetcher(timeout=config.TIMEOUT, max_retries=config.MAX_RETRIES, delay=delay)
    records = []

    page_url = config.LIST_URL.format(page=1)
    crawled_pages = 0
    while page_url and crawled_pages < pages:
        resp = fetcher.get(page_url)
        if resp is None:
            break
        items, next_url = parse_list_page(resp.text, page_url)
        crawled_pages += 1

        for item in items:
            detail_resp = fetcher.get(item["detail_url"])
            if detail_resp is None:
                continue
            detail = parse_detail_page(detail_resp.text, item["detail_url"])
            # 详情页图片地址是相对路径，转成绝对地址
            if detail.get("detail_image_url"):
                item["image_url"] = urljoin(item["detail_url"], detail["detail_image_url"])
            records.append(build_record(item, detail))

        page_url = next_url
        logging.info("进度：已抓 %s 页 / 目标 %s 页，累计 %s 条", crawled_pages, pages, len(records))

    logging.info("抓取结束：%s 页，%s 条原始数据，请求 %s 次，失败 %s 次",
                 crawled_pages, len(records), fetcher.request_count, len(fetcher.failures))

    if fetcher.failures:
        (config.DATA_DIR / "failed_urls.json").write_text(
            json.dumps(fetcher.failures, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logging.warning("失败链接已记录到 data/failed_urls.json")

    cleaned, dup, dropped = clean_records(records)
    save_json(cleaned, config.DATA_DIR / "books.json")
    save_csv(cleaned, config.DATA_DIR / "books.csv")
    save_excel(cleaned, config.DATA_DIR / "books.xlsx")

    if not save_mysql(cleaned):
        save_sql_file(cleaned, config.SQL_DIR / "insert_books.sql")

    image_stat = None
    if with_images and cleaned:
        image_stat = download_images(cleaned, config.IMAGE_DIR, max_workers=config.MAX_WORKERS)

    elapsed = time.time() - start
    summary = {
        "页数": crawled_pages,
        "原始条数": len(records),
        "有效条数": len(cleaned),
        "重复条数": dup,
        "脏数据条数": dropped,
        "失败链接数": len(fetcher.failures),
        "耗时(秒)": round(elapsed, 2),
        "图片": image_stat,
    }
    print("\n========== 采集结果统计 ==========")
    for key, value in summary.items():
        print(f"{key}: {value}")
    print("输出目录:", config.DATA_DIR)
    print("=================================")
    return summary


def main():
    parser = argparse.ArgumentParser(description="books.toscrape.com 爬虫练习")
    parser.add_argument("--pages", type=int, default=3, help="抓取列表页数（每页 20 条）")
    parser.add_argument("--delay", type=float, default=config.DELAY, help="请求间隔（秒）")
    parser.add_argument("--images", action="store_true", help="是否批量下载封面图片")
    args = parser.parse_args()

    setup_logging()
    crawl(pages=args.pages, delay=args.delay, with_images=args.images)


if __name__ == "__main__":
    main()
