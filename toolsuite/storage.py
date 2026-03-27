import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from toolsuite.config import DB_PATH, RAW_DATA_DIR, ensure_directories


@contextmanager
def get_connection():
    ensure_directories()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.commit()
        connection.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS crawls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                status TEXT NOT NULL,
                note TEXT,
                started_at TEXT,
                finished_at TEXT,
                raw_path TEXT,
                metadata_json TEXT,
                error TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crawl_id INTEGER NOT NULL,
                summary TEXT,
                metrics_json TEXT,
                created_at TEXT,
                FOREIGN KEY(crawl_id) REFERENCES crawls(id)
            )
            """
        )


def _row_to_dict(row: sqlite3.Row) -> Dict:
    return {key: row[key] for key in row.keys()}


def create_crawl_record(url: str, note: str = "") -> int:
    started = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO crawls (url, status, note, started_at) VALUES (?, ?, ?, ?)",
            (url, "pending", note, started),
        )
        return int(cursor.lastrowid)


def update_crawl_status(crawl_id: int, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE crawls SET status = ? WHERE id = ?",
            (status, crawl_id),
        )


def mark_crawl_complete(crawl_id: int, raw_path: Path, metadata: Optional[Dict] = None) -> None:
    finished_at = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE crawls
            SET status = ?, finished_at = ?, raw_path = ?, metadata_json = ?
            WHERE id = ?
            """,
            (
                "completed",
                finished_at,
                str(raw_path),
                json.dumps(metadata or {}),
                crawl_id,
            ),
        )


def mark_crawl_failed(crawl_id: int, error: str) -> None:
    finished_at = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE crawls
            SET status = ?, finished_at = ?, error = ?
            WHERE id = ?
            """,
            (
                "failed",
                finished_at,
                error,
                crawl_id,
            ),
        )


def store_analysis_result(crawl_id: int, summary: str, metrics: Dict) -> int:
    created_at = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO analysis_results (crawl_id, summary, metrics_json, created_at) VALUES (?, ?, ?, ?)",
            (crawl_id, summary, json.dumps(metrics), created_at),
        )
        return int(cursor.lastrowid)


def fetch_recent_crawls(limit: int = 20) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM crawls ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def fetch_crawl(crawl_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM crawls WHERE id = ?",
            (crawl_id,),
        ).fetchone()
    return _row_to_dict(row) if row else None


def fetch_latest_crawl() -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM crawls ORDER BY started_at DESC LIMIT 1",
        ).fetchone()
    return _row_to_dict(row) if row else None


def fetch_analysis_for_crawl(crawl_id: int) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM analysis_results WHERE crawl_id = ? ORDER BY created_at DESC",
            (crawl_id,),
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def fetch_latest_analysis() -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM analysis_results ORDER BY created_at DESC LIMIT 1",
        ).fetchone()
    return _row_to_dict(row) if row else None


__all__ = [
    "RAW_DATA_DIR",
    "init_db",
    "create_crawl_record",
    "update_crawl_status",
    "mark_crawl_complete",
    "mark_crawl_failed",
    "store_analysis_result",
    "fetch_recent_crawls",
    "fetch_crawl",
    "fetch_latest_crawl",
    "fetch_analysis_for_crawl",
    "fetch_latest_analysis",
    "get_connection",
]
