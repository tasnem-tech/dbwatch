"""
Database connection management.
Supports any SQLAlchemy-compatible database (SQLite, PostgreSQL, MySQL).
"""
import json
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def get_engine(url: str) -> Engine:
    """Return a SQLAlchemy engine for the given URL."""
    return create_engine(url, pool_pre_ping=True)


def save_config(path: Path, url: str) -> None:
    """Persist the database URL to a local JSON config file."""
    path.write_text(json.dumps({"url": url}, indent=2))


def load_config(path: Path) -> str:
    """Load and return the database URL from config."""
    if not path.exists():
        raise FileNotFoundError(
            f"No config found at {path}. Run `dbwatch init --url <url>` first."
        )
    return json.loads(path.read_text())["url"]


def ping(engine: Engine) -> bool:
    """Return True if the database is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
