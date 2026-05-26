"""
Diff engine — compares two snapshots and produces a structured delta.

Detects:
  - Added / removed tables
  - Column additions, removals, type changes, nullability changes
  - Row count shifts
  - Data mutations (when row hashes are present in both snapshots)
"""
from dataclasses import dataclass, field


@dataclass
class TableDelta:
    name: str
    status: str          # "added" | "removed" | "changed" | "unchanged"
    column_changes: list = field(default_factory=list)
    row_count_before: int = 0
    row_count_after: int = 0
    data_changed: bool = False


@dataclass
class Diff:
    from_label: str
    to_label: str
    from_ts: str
    to_ts: str
    tables: list[TableDelta] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(t.status != "unchanged" for t in self.tables)


def _diff_columns(before: list, after: list) -> list:
    """Return a list of column-level change descriptors."""
    changes = []
    before_map = {c["name"]: c for c in before}
    after_map  = {c["name"]: c for c in after}

    for name, col in after_map.items():
        if name not in before_map:
            changes.append({"type": "column_added", "column": name})
        elif col["type"] != before_map[name]["type"]:
            changes.append({
                "type": "type_changed",
                "column": name,
                "before": before_map[name]["type"],
                "after": col["type"],
            })
        elif col["nullable"] != before_map[name]["nullable"]:
            changes.append({
                "type": "nullable_changed",
                "column": name,
                "before": before_map[name]["nullable"],
                "after": col["nullable"],
            })

    for name in before_map:
        if name not in after_map:
            changes.append({"type": "column_removed", "column": name})

    return changes


def diff(snap_a: dict, snap_b: dict) -> Diff:
    """Compare two snapshots and return a Diff object."""
    result = Diff(
        from_label=snap_a["label"],
        to_label=snap_b["label"],
        from_ts=snap_a["timestamp"],
        to_ts=snap_b["timestamp"],
    )

    all_tables = set(snap_a["tables"]) | set(snap_b["tables"])

    for tname in sorted(all_tables):
        in_a = tname in snap_a["tables"]
        in_b = tname in snap_b["tables"]

        if in_a and not in_b:
            result.tables.append(TableDelta(name=tname, status="removed"))
            continue
        if in_b and not in_a:
            result.tables.append(TableDelta(name=tname, status="added"))
            continue

        col_changes = _diff_columns(
            snap_a["tables"][tname]["columns"],
            snap_b["tables"][tname]["columns"],
        )
        count_a = snap_a["row_counts"].get(tname, 0)
        count_b = snap_b["row_counts"].get(tname, 0)

        hash_changed = False
        if "row_hashes" in snap_a and "row_hashes" in snap_b:
            hash_changed = (
                snap_a["row_hashes"].get(tname) != snap_b["row_hashes"].get(tname)
            )

        status = "unchanged"
        if col_changes or count_a != count_b or hash_changed:
            status = "changed"

        result.tables.append(TableDelta(
            name=tname,
            status=status,
            column_changes=col_changes,
            row_count_before=count_a,
            row_count_after=count_b,
            data_changed=hash_changed,
        ))

    return result
