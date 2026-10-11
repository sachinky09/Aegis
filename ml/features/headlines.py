"""Layer 3: free headline fetch via Google News RSS (no API key)."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


def fetch_headlines(symbol: str, company_name: str | None = None, limit: int = 8) -> list[dict[str, Any]]:
    q = f"{company_name or symbol} stock NSE"
    url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=en-IN&gl=IN&ceid=IN:en"
    headers = {"User-Agent": "Mozilla/5.0 AegisResearch/1.0"}
    out: list[dict[str, Any]] = []
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=12) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        for item in root.findall(".//item")[:limit]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub = (item.findtext("pubDate") or "").strip()
            source = ""
            src_el = item.find("{http://www.w3.org/2005/Atom}source")
            if src_el is None:
                src_el = item.find("source")
            if src_el is not None and src_el.text:
                source = src_el.text.strip()
            if not title:
                continue
            out.append({
                "title": title,
                "url": link or None,
                "published_at": pub,
                "source": source or "google-news-rss",
                "matched": True,
                "query": q,
            })
    except Exception as e:
        out.append({
            "title": f"Headline feed unavailable: {e}",
            "source": "google-news-rss",
            "published_at": datetime.now(timezone.utc).isoformat(),
            "url": None,
            "matched": False,
            "error": str(e),
        })
    return out
