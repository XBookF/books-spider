"""解析层：列表页用 BeautifulSoup(CSS 选择器)，详情页用 lxml XPath（两种都要会）"""
import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from lxml import etree

logger = logging.getLogger(__name__)


def parse_list_page(html, page_url):
    """解析列表页：返回图书条目 + 下一页地址（分页规则靠 li.next 判断，不写死页数）"""
    soup = BeautifulSoup(html, "lxml")
    items = []

    for card in soup.select("article.product_pod"):
        link = card.select_one("h3 a")
        if not link:
            continue
        rating_node = card.select_one("p.star-rating")
        rating_class = rating_node["class"] if rating_node else []
        items.append({
            "title": link.get("title", "").strip(),
            "detail_url": urljoin(page_url, link.get("href", "")),
            "price_text": (card.select_one("p.price_color").get_text(strip=True)
                           if card.select_one("p.price_color") else ""),
            "rating_text": rating_class[-1] if rating_class else "",
            "image_url": urljoin(page_url, card.select_one("img").get("src", ""))
            if card.select_one("img") else "",
        })

    next_node = soup.select_one("li.next a")
    next_url = urljoin(page_url, next_node["href"]) if next_node else None
    logger.info("列表页 %s 解析到 %s 条，下一页：%s", page_url, len(items), next_url or "无")
    return items, next_url


def parse_detail_page(html, detail_url):
    """解析详情页（XPath）：UPC、分类、库存、评论数、描述等"""
    tree = etree.HTML(html)
    if tree is None:
        return {}

    def text_of(node, xpath, default=""):
        """在指定节点下执行 XPath，返回第一段文本（注意必须相对 node，否则会串行）"""
        values = node.xpath(xpath)
        if not values:
            return default
        value = values[0]
        return value.strip() if isinstance(value, str) else value

    def first(xpath, default=""):
        return text_of(tree, xpath, default)

    # 规格表：th -> td 的键值对
    specs = {}
    for row in tree.xpath('//table[contains(@class,"table-striped")]//tr'):
        key = text_of(row, "./th/text()", "")
        value = text_of(row, "./td/text()", "")
        if key:
            specs[key] = value

    desc = first('//div[@id="product_description"]/following-sibling::p[1]/text()')

    return {
        "upc": specs.get("UPC", ""),
        "category": first('//ul[contains(@class,"breadcrumb")]/li[3]/a/text()'),
        "price_excl_tax_text": specs.get("Price (excl. tax)", ""),
        "tax_text": specs.get("Tax", ""),
        "availability_text": specs.get("Availability", ""),
        "reviews": specs.get("Number of reviews", "0"),
        "description": desc,
        "detail_image_url": first('//div[@id="product_gallery"]//img/@src'),
        "detail_url": detail_url,
    }
