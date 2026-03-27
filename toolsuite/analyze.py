import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Optional

from bs4 import BeautifulSoup

from toolsuite.storage import (
    fetch_crawl,
    fetch_latest_crawl,
    init_db,
    store_analysis_result,
)


STOPWORDS = {
    "the",
    "and",
    "for",
    "are",
    "with",
    "that",
    "this",
    "from",
    "have",
    "has",
    "was",
    "were",
    "your",
    "you",
    "our",
    "their",
    "will",
    "shall",
    "about",
    "into",
    "than",
    "when",
    "what",
    "where",
    "which",
    "while",
    "who",
    "how",
}


def _load_raw_payload(raw_path: Path) -> Dict:
    with open(raw_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _extract_text(payload: Dict) -> str:
    html = payload.get("html")
    markdown = payload.get("markdown")
    if html:
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(" ", strip=True)
    if markdown:
        soup = BeautifulSoup(markdown, "html.parser")
        return soup.get_text(" ", strip=True)
    return ""


def _count_links(payload: Dict) -> int:
    links = payload.get("links")
    if isinstance(links, dict):
        aggregated = []
        for key, items in links.items():
            if isinstance(items, list):
                aggregated.extend(items)
        return len(aggregated)
    if isinstance(links, list):
        return len(links)
    return 0


def _keyword_frequency(text: str, top_n: int = 10):
    words = re.findall(r"[A-Za-z]{3,}", text.lower())
    filtered = [word for word in words if word not in STOPWORDS]
    counter = Counter(filtered)
    return counter.most_common(top_n)


def analyze_crawl(crawl_id: Optional[int] = None) -> Dict:
    init_db()
    crawl_record = fetch_crawl(crawl_id) if crawl_id is not None else fetch_latest_crawl()
    if not crawl_record:
        raise ValueError("No crawl record available for analysis")
    raw_path = crawl_record.get("raw_path")
    if not raw_path:
        raise FileNotFoundError("Selected crawl does not have a persisted raw payload")

    payload = _load_raw_payload(Path(raw_path))
    text = _extract_text(payload)
    words = re.findall(r"[A-Za-z]{3,}", text)
    keyword_stats = _keyword_frequency(text)
    link_count = _count_links(payload)

    metrics = {
        "word_count": len(words),
        "link_count": link_count,
        "top_keywords": [
            {"keyword": keyword, "count": count}
            for keyword, count in keyword_stats
        ],
    }
    summary = (
        f"Word count: {metrics['word_count']} | Links detected: {metrics['link_count']}"
    )
    analysis_id = store_analysis_result(
        crawl_id=crawl_record["id"], summary=summary, metrics=metrics
    )
    return {
        "analysis_id": analysis_id,
        "crawl_id": crawl_record["id"],
        "metrics": metrics,
        "summary": summary,
    }


__all__ = ["analyze_crawl"]
