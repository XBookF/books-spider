"""动态页面案例：quotes.toscrape.com/js 由 JavaScript 渲染，requests 抓不到，必须用浏览器内核

运行：python spider/selenium_demo.py
单位：Selenium 4 自带 Selenium Manager，会按本机 Chrome 版本自动匹配驱动
"""
import json
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://quotes.toscrape.com/js/"
OUT = Path(__file__).resolve().parent.parent / "data" / "quotes_js.json"


def with_requests():
    resp = requests.get(URL, timeout=15)
    soup = BeautifulSoup(resp.text, "lxml")
    return len(soup.select("div.quote"))


def with_selenium():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(URL)
        # 显式等待：等 JS 把 .quote 渲染出来，而不是 sleep 硬等
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.quote"))
        )
        quotes = []
        for node in driver.find_elements(By.CSS_SELECTOR, "div.quote"):
            quotes.append({
                "text": node.find_element(By.CSS_SELECTOR, "span.text").text,
                "author": node.find_element(By.CSS_SELECTOR, "small.author").text,
                "tags": [t.text for t in node.find_elements(By.CSS_SELECTOR, "a.tag")],
            })
        return quotes
    finally:
        driver.quit()


def main():
    direct = with_requests()
    print(f"requests + BeautifulSoup 解析到 {direct} 条（JS 未执行，所以是 0）")

    quotes = with_selenium()
    print(f"Selenium 渲染后解析到 {len(quotes)} 条")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(quotes, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已保存:", OUT)


if __name__ == "__main__":
    sys.exit(main())
