import asyncio
import json
import time
from typing import Dict, Optional

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig

from toolsuite.config import DEFAULT_MAX_CRAWL_BYTES, RAW_DATA_DIR
from toolsuite.storage import (
    create_crawl_record,
    init_db,
    mark_crawl_complete,
    mark_crawl_failed,
    update_crawl_status,
)


async def _fetch_url(url: str):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS),
        )
    return result


def _truncate_payload(text: Optional[str], max_bytes: int) -> Optional[str]:
    if text is None:
        return None
    encoded = text.encode("utf-8", errors="ignore")
    if len(encoded) <= max_bytes:
        return text
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated + "\n<!-- truncated -->"


def run_crawl(url: str, note: str = "") -> Dict:
    init_db()
    crawl_id = create_crawl_record(url=url, note=note)
    update_crawl_status(crawl_id, "running")
    raw_file = RAW_DATA_DIR / f"crawl_{crawl_id}_{int(time.time())}.json"
    try:
        result = asyncio.run(_fetch_url(url))
        html_bytes = (result.html or "").encode("utf-8", errors="ignore")
        html_truncated = len(html_bytes) > DEFAULT_MAX_CRAWL_BYTES
        html_content = _truncate_payload(result.html, DEFAULT_MAX_CRAWL_BYTES)
        markdown_content = _truncate_payload(
            str(result.markdown) if result.markdown is not None else None,
            DEFAULT_MAX_CRAWL_BYTES,
        )
        raw_payload = {
            "crawl_id": crawl_id,
            "url": url,
            "success": result.success,
            "status_code": result.status_code,
            "html": html_content,
            "markdown": markdown_content,
            "links": result.links,
            "metadata": result.metadata,
            "cleaned_html": _truncate_payload(result.cleaned_html, DEFAULT_MAX_CRAWL_BYTES),
        }
        with open(raw_file, "w", encoding="utf-8") as handle:
            json.dump(raw_payload, handle, ensure_ascii=False, indent=2)
        mark_crawl_complete(
            crawl_id=crawl_id,
            raw_path=raw_file,
            metadata={
                "status_code": result.status_code,
                "success": result.success,
                "truncated": html_truncated,
            },
        )
        return {"crawl_id": crawl_id, "raw_path": str(raw_file), "success": True}
    except Exception as exc:  # noqa: BLE001
        mark_crawl_failed(crawl_id, error=str(exc))
        return {"crawl_id": crawl_id, "raw_path": str(raw_file), "success": False, "error": str(exc)}


__all__ = ["run_crawl"]
