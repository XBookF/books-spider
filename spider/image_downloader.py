"""图片批量下载：线程池 + 重试 + 跳过已存在 + 文件名清洗"""
import logging
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


def safe_filename(name, fallback="image"):
    name = re.sub(r'[\\/:*?"<>|\s]+', "_", name).strip("._")
    return name or fallback


def download_one(session, url, save_dir, filename, retries=2):
    """下载单张图片，返回 (文件名, 字节数, 是否成功)"""
    path = Path(save_dir) / filename
    if path.exists() and path.stat().st_size > 0:
        return filename, path.stat().st_size, True

    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, timeout=15, stream=True)
            resp.raise_for_status()
            with open(path, "wb") as fp:
                for chunk in resp.iter_content(8192):
                    fp.write(chunk)
            time.sleep(0.05)
            return filename, path.stat().st_size, True
        except requests.RequestException as exc:
            logger.warning("图片下载失败(%s/%s) %s -> %s", attempt, retries, url, exc)
            time.sleep(0.3 * attempt)
    return filename, 0, False


def download_images(records, save_dir, max_workers=8):
    """并发下载，返回统计 dict"""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

    tasks = []
    for record in records:
        if not record.get("image_url"):
            continue
        ext = Path(urlparse(record["image_url"]).path).suffix or ".jpg"
        basename = safe_filename(record["upc"] or record["title"], fallback="image")
        tasks.append((record["image_url"], save_dir, basename + ext))

    ok, failed, total_bytes = 0, 0, 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(download_one, session, *task) for task in tasks]
        for future in as_completed(futures):
            _, size, success = future.result()
            if success:
                ok += 1
                total_bytes += size
            else:
                failed += 1

    logger.info("图片下载完成：成功 %s 张，失败 %s 张，共 %.1f KB",
                ok, failed, total_bytes / 1024)
    return {"ok": ok, "failed": failed, "bytes": total_bytes}
