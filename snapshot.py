"""
Snapshot logic — captures schema (columns, types, constraints)
and optionally row-level SHA-256 hashes for every table.
Snapshots are stored as JSON files in .dbwatch_snapshots/.
"""
import json
import hashlib
import datetime
from pathlib import Path
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

SNAPSHOT_DIR = Path(".dbwatch_snapshots")


def _schema(engine: Engine) -> dict:
    """Introspect all tables and return a schema dict."""
    insp = inspect(engine)
    tables = {}
    for tname in insp.get_table_names():
        cols = [
            {
                "name": c["name"],
                "type": str(c["type"]),
                "nullable": c["nullable"],
            }
            for c in insp.get_columns(tname)
        ]
        pk = insp.get_pk_constraint(tname).get("constrained_columns", [])
        fks = [
            {"cols": fk["constrained_columns"], "ref": fk["referred_table"]}
            for fk in insp.get_foreign_keys(tname)
        ]
        tables[tname] = {"columns": cols, "primary_key": pk, "foreign_keys": fks}
    return tables


def _row_counts(engine: Engine, tables: list) -> dict:
    """Return a {table: count} dict for all tables."""
    counts = {}
    with engine.connect() as conn:
        for t in tables:
            row = conn.execute(text(f'SELECT COUNT(*) FROM "{t}"')).fetchone()
            counts[t] = row[0]
    return counts


def _row_hashes(engine: Engine, tables: list) -> dict:
    """
    Hash all rows in each table with SHA-256.
    Rows are sorted by the first column to ensure deterministic ordering.
    """
    hashes = {}
    with engine.connect() as conn:
        for t in tables:
            rows = conn.execute(text(f'SELECT * FROM "{t}" ORDER BY 1')).fetchall()
            digest = hashlib.sha256(str(rows).encode()).hexdigest()
            hashes[t] = digest
    return hashes


def take(engine: Engine, label: str = "latest", include_data: bool = False) -> dict:
    """Capture the full database state and return as a dict."""
    tables = _schema(engine)
    table_names = list(tables.keys())
    snap = {
        "label": label,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "tables": tables,
        "row_counts": _row_counts(engine, table_names),
    }
    if include_data:
        snap["row_hashes"] = _row_hashes(engine, table_names)
    return snap


def save(snap: dict, label: str) -> Path:
    """Write a snapshot to disk as JSON."""
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    path = SNAPSHOT_DIR / f"{label}.json"
    path.write_text(json.dumps(snap, indent=2))
    return path


def load(label: str) -> dict:
    """Read a snapshot from disk by label."""
    path = SNAPSHOT_DIR / f"{label}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Snapshot '{label}' not found. Run `dbwatch snapshot --label {label}` first."
        )
    return json.loads(path.read_text())
