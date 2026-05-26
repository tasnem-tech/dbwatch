"""
Output formatting — terminal (Rich tables), JSON, or file.
"""
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import box
from dbwatch.differ import Diff

console = Console()


def _terminal(delta: Diff) -> None:
    """Print a Rich-formatted diff table to the terminal."""
    console.rule(f"[bold]dbwatch diff[/bold]  {delta.from_label} → {delta.to_label}")
    console.print(f"  [dim]{delta.from_ts}  →  {delta.to_ts}[/dim]\n")

    if not delta.has_changes:
        console.print("[green]✓ No changes detected.[/green]")
        return

    tbl = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold")
    tbl.add_column("Table",              style="bold")
    tbl.add_column("Status")
    tbl.add_column("Rows (before→after)")
    tbl.add_column("Column changes")

    STATUS_COLOR = {"added": "green", "removed": "red", "changed": "yellow"}

    for t in delta.tables:
        if t.status == "unchanged":
            continue
        color = STATUS_COLOR[t.status]
        col_summary = ", ".join(
            f"{c['type'].replace('_', ' ')} '{c['column']}'"
            for c in t.column_changes
        ) or "—"
        rows_str = (
            f"{t.row_count_before} → {t.row_count_after}"
            if t.status == "changed" else "—"
        )
        tbl.add_row(
            t.name,
            f"[{color}]{t.status}[/{color}]",
            rows_str,
            col_summary,
        )

    console.print(tbl)


def _to_dict(delta: Diff) -> dict:
    """Serialise a Diff to a plain dict suitable for JSON output."""
    return {
        "from": delta.from_label,
        "to": delta.to_label,
        "from_ts": delta.from_ts,
        "to_ts": delta.to_ts,
        "has_changes": delta.has_changes,
        "tables": [
            {
                "name": t.name,
                "status": t.status,
                "row_count_before": t.row_count_before,
                "row_count_after": t.row_count_after,
                "column_changes": t.column_changes,
                "data_changed": t.data_changed,
            }
            for t in delta.tables
            if t.status != "unchanged"
        ],
    }


def report(delta: Diff, mode: str = "terminal", path: Optional[Path] = None) -> None:
    """Route output to the requested destination."""
    if mode == "terminal":
        _terminal(delta)
    elif mode == "json":
        console.print_json(json.dumps(_to_dict(delta)))
    elif mode == "file":
        if not path:
            raise ValueError("--out-path required when --output=file")
        path.write_text(json.dumps(_to_dict(delta), indent=2))
        console.print(f"[green]✓ Diff written to {path}[/green]")
    else:
        raise ValueError(f"Unknown output mode: {mode!r}")
