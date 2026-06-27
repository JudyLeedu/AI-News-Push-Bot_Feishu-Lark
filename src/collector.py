"""内容采集模块：RSS 抓取 + 网页抓取"""
import re
import hashlib
from datetime import datetime, timezone
from typing import Optional

import feedparser
import httpx
from bs4 import BeautifulSoup
from src.config import get_config


# ---------- RSS ----------
async def fetch_rss(url: str, max_items: int = 10) -> list[dict]:
    """抓取 RSS feed，返回文章列表"""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, follow_redirects=True)
        resp.raise_for_status()

    feed = feedparser.parse(resp.text)
    items = []
    for entry in feed.entries[:max_items]:
        items.append({
            "title": entry.get("title", "").strip(),
            "url": entry.get("link", ""),
            "summary": _clean_html(entry.get("summary", "")),
            "published": _parse_date(entry),
            "source": feed.feed.get("title", ""),
        })
    return items


# ---------- Web 抓取 ----------
async def fetch_web(url: str, max_items: int = 10) -> list[dict]:
    """抓取网页，提取文章链接列表"""
    async with httpx.AsyncClient(timeout=30, headers={
        "User-Agent": "Mozilla/5.0 (compatible; AINewsBot/1.0)"
    }) as client:
        resp = await client.get(url, follow_redirects=True)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    items = []

    # 常见文章列表选择器
    selectors = [
        "article", ".post", ".blog-post", ".article", ".entry",
        "a[href*='/blog/']", "a[href*='/news/']",
        "li a[href]", "h2 a[href]", "h3 a[href]",
    ]

    seen = set()
    for selector in selectors:
        for el in soup.select(selector):
            if el.name == "a":
                title = el.get_text(strip=True)
                href = el.get("href", "")
            else:
                a_tag = el.find("a")
                if not a_tag:
                    continue
                title = a_tag.get_text(strip=True)
                href = a_tag.get("href", "")

            if not title or not href or len(title) < 5:
                continue

            # 补全相对 URL
            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(url, href)

            uid = hashlib.md5(href.encode()).hexdigest()
            if uid in seen:
                continue
            seen.add(uid)

            items.append({
                "title": title,
                "url": href,
                "summary": "",
                "published": "",
                "source": "",
            })

            if len(items) >= max_items * 3:
                break
        if len(items) >= max_items * 3:
            break

    return items


# ---------- 内容过滤 ----------
def filter_items(items: list[dict], frequency: str) -> list[dict]:
    """按关键词和频次过滤内容"""
    cfg = get_config()["filters"]
    keywords = [k.lower() for k in cfg.get("keywords", [])]
    exclude_kw = [k.lower() for k in cfg.get("exclude_keywords", [])]

    max_n = {
        "daily": cfg.get("daily_max_items", 5),
        "weekly": cfg.get("weekly_max_items", 1),
        "monthly": cfg.get("monthly_max_items", 1),
    }.get(frequency, 5)

    filtered = []
    for item in items:
        text = f"{item['title']} {item['summary']}".lower()

        # 排除
        if any(kw in text for kw in exclude_kw):
            continue

        # 关键词匹配
        if keywords and not any(kw in text for kw in keywords):
            continue

        filtered.append(item)
        if len(filtered) >= max_n:
            break

    return filtered


# ---------- 采集入口 ----------
async def collect_content(frequency: str) -> list[dict]:
    """按频次采集内容"""
    cfg = get_config()["sources"]
    sources = cfg.get(frequency, [])
    all_items = []

    for src in sources:
        try:
            if src.get("type") == "rss":
                items = await fetch_rss(src["url"])
            else:
                items = await fetch_web(src["url"])
            for item in items:
                item["source"] = src["name"]
            all_items.extend(items)
        except Exception as e:
            print(f"[Collect] 采集 {src['name']} 失败: {e}")

    # 去重
    seen = set()
    unique = []
    for item in all_items:
        uid = hashlib.md5(item["url"].encode()).hexdigest()
        if uid not in seen:
            seen.add(uid)
            unique.append(item)

    return filter_items(unique, frequency)


# ---------- 工具 ----------
def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text)[:500]


def _parse_date(entry) -> str:
    for field in ("published_parsed", "updated_parsed"):
        tp = entry.get(field)
        if tp:
            try:
                dt = datetime(*tp[:6], tzinfo=timezone.utc)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                pass
    return ""
