"""Tests for the diff engine (differ.py)."""
import pytest
from dbwatch.differ import diff


# ── helpers ────────────────────────────────────────────────────────────────

def _snap(label, tables, counts, hashes=None):
    return {
        "label": label,
        "timestamp": "2024-01-01T00:00:00",
        "tables": tables,
        "row_counts": counts,
        **({"row_hashes": hashes} if hashes else {}),
    }


def _tbl(cols):
    return {"columns": cols, "primary_key": ["id"], "foreign_keys": []}


COLS_V1 = [
    {"name": "id",   "type": "INTEGER", "nullable": False},
    {"name": "name", "type": "VARCHAR", "nullable": True},
]
COLS_V2 = COLS_V1 + [{"name": "email", "type": "VARCHAR", "nullable": True}]
COLS_V3 = [
    {"name": "id",   "type": "INTEGER", "nullable": False},
    {"name": "name", "type": "TEXT",    "nullable": True},   # type changed
]


# ── tests ───────────────────────────────────────────────────────────────────

def test_no_changes():
    snap = _snap("a", {"users": _tbl(COLS_V1)}, {"users": 10})
    assert not diff(snap, snap).has_changes


def test_table_added():
    a = _snap("a", {}, {})
    b = _snap("b", {"orders": _tbl(COLS_V1)}, {"orders": 5})
    delta = diff(a, b)
    assert delta.has_changes
    t = delta.tables[0]
    assert t.status == "added"
    assert t.name == "orders"


def test_table_removed():
    a = _snap("a", {"users": _tbl(COLS_V1)}, {"users": 3})
    b = _snap("b", {}, {})
    assert diff(a, b).tables[0].status == "removed"


def test_column_added():
    a = _snap("a", {"users": _tbl(COLS_V1)}, {"users": 5})
    b = _snap("b", {"users": _tbl(COLS_V2)}, {"users": 5})
    t = diff(a, b).tables[0]
    assert t.status == "changed"
    assert any(c["type"] == "column_added" and c["column"] == "email" for c in t.column_changes)


def test_column_removed():
    a = _snap("a", {"users": _tbl(COLS_V2)}, {"users": 5})
    b = _snap("b", {"users": _tbl(COLS_V1)}, {"users": 5})
    t = diff(a, b).tables[0]
    assert any(c["type"] == "column_removed" and c["column"] == "email" for c in t.column_changes)


def test_type_changed():
    a = _snap("a", {"users": _tbl(COLS_V1)}, {"users": 5})
    b = _snap("b", {"users": _tbl(COLS_V3)}, {"users": 5})
    t = diff(a, b).tables[0]
    assert any(c["type"] == "type_changed" and c["column"] == "name" for c in t.column_changes)


def test_row_count_change():
    tbl = {"users": _tbl(COLS_V1)}
    a = _snap("a", tbl, {"users": 10})
    b = _snap("b", tbl, {"users": 20})
    t = diff(a, b).tables[0]
    assert t.status == "changed"
    assert t.row_count_before == 10
    assert t.row_count_after == 20


def test_data_hash_change():
    tbl = {"users": _tbl(COLS_V1)}
    a = _snap("a", tbl, {"users": 5}, hashes={"users": "abc123"})
    b = _snap("b", tbl, {"users": 5}, hashes={"users": "def456"})
    assert diff(a, b).tables[0].data_changed


def test_data_hash_unchanged():
    tbl = {"users": _tbl(COLS_V1)}
    a = _snap("a", tbl, {"users": 5}, hashes={"users": "abc123"})
    b = _snap("b", tbl, {"users": 5}, hashes={"users": "abc123"})
    assert not diff(a, b).tables[0].data_changed


def test_multiple_tables():
    a = _snap("a", {"users": _tbl(COLS_V1), "posts": _tbl(COLS_V1)}, {"users": 5, "posts": 10})
    b = _snap("b", {"users": _tbl(COLS_V2), "posts": _tbl(COLS_V1)}, {"users": 5, "posts": 10})
    delta = diff(a, b)
    statuses = {t.name: t.status for t in delta.tables}
    assert statuses["users"] == "changed"
    assert statuses["posts"] == "unchanged"
