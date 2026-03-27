from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "tool_suite.db"

DEFAULT_MAX_CRAWL_BYTES = 2_000_000  # guardrail for accidental huge writes


def ensure_directories() -> None:
    """Create required directories for persistence."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


__all__ = [
    "BASE_DIR",
    "DATA_DIR",
    "RAW_DATA_DIR",
    "DB_PATH",
    "DEFAULT_MAX_CRAWL_BYTES",
    "ensure_directories",
]
