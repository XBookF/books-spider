"""清洗层：类型转换、空值校验、按 UPC 去重（面试高频：脏数据怎么处理）"""
import logging
import re

logger = logging.getLogger(__name__)

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
PRICE_RE = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")
STOCK_RE = re.compile(r"\((\d+)\s+available\)")


def parse_price(text):
    """'£51.77' / 'Â£51.77' / '1,234.50' -> float，失败返回 None"""
    if not text:
        return None
    match = PRICE_RE.search(text.replace(",", ""))
    return float(match.group(1)) if match else None


def parse_stock(text):
    """'In stock (22 available)' -> 22；无数字则按是否有货给 0/1"""
    if not text:
        return 0
    match = STOCK_RE.search(text)
    if match:
        return int(match.group(1))
    return 1 if "in stock" in text.lower() else 0


def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def build_record(list_item, detail):
    """把列表页 + 详情页字段合并成一条标准记录"""
    return {
        "upc": clean_text(detail.get("upc", "")),
        "title": clean_text(list_item.get("title", "")),
        "category": clean_text(detail.get("category", "")),
        "price": parse_price(list_item.get("price_text", "")),
        "price_excl_tax": parse_price(detail.get("price_excl_tax_text", "")),
        "tax": parse_price(detail.get("tax_text", "")),
        "rating": RATING_MAP.get(list_item.get("rating_text", ""), 0),
        "stock": parse_stock(detail.get("availability_text", "")),
        "reviews": int(detail.get("reviews") or 0),
        "description": clean_text(detail.get("description", "")),
        "image_url": list_item.get("image_url", ""),
        "detail_url": list_item.get("detail_url", ""),
    }


def validate(record):
    """必填校验：UPC 是唯一键，标题和价格缺失的数据直接丢弃"""
    if not record.get("upc"):
        return False, "缺少 UPC"
    if not record.get("title"):
        return False, "缺少标题"
    if record.get("price") is None:
        return False, "价格解析失败"
    return True, ""


def clean_records(records):
    """校验 + 按 UPC 去重，返回 (有效记录, 去重数, 丢弃数)"""
    valid, seen, dup, dropped = [], set(), 0, 0
    for record in records:
        ok, reason = validate(record)
        if not ok:
            dropped += 1
            logger.warning("丢弃脏数据：%s | %s", reason, record.get("title") or record.get("detail_url"))
            continue
        if record["upc"] in seen:
            dup += 1
            continue
        seen.add(record["upc"])
        valid.append(record)
    logger.info("清洗完成：有效 %s 条，重复 %s 条，丢弃 %s 条", len(valid), dup, dropped)
    return valid, dup, dropped
