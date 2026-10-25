"""请求层：Session 复用、UA、超时、重试、限速、失败记录"""
import logging
import random
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


class Fetcher:
    """统一的 HTTP 抓取入口：面试时可讲 Session 复用、连接池、重试退避、限速"""

    def __init__(self, timeout=10, max_retries=3, delay=0.3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay = delay
        self.failures = []          # [(url, 原因)]，用于最后汇总异常
        self.request_count = 0

        self.session = requests.Session()
        retry = Retry(
            total=max_retries,
            read=max_retries,
            connect=max_retries,
            backoff_factor=0.5,                     # 0.5s、1s、2s 指数退避
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        })

    def get(self, url, **kwargs):
        """返回响应对象；多次尝试仍失败则返回 None，并记录到 failures"""
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout, **kwargs)
                resp.raise_for_status()
                # 编码：部分站点不声明 charset，用 apparent_encoding 兜底，避免中文/£乱码
                if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
                    resp.encoding = resp.apparent_encoding or "utf-8"
                self.request_count += 1
                time.sleep(self.delay + random.uniform(0, 0.1))   # 随机间隔，降低被封风险
                return resp
            except requests.RequestException as exc:
                logger.warning("请求失败(%s/%s) %s -> %s", attempt, self.max_retries, url, exc)
                if attempt < self.max_retries:
                    time.sleep(0.5 * attempt)

        self.failures.append((url, "重试耗尽"))
        return None
