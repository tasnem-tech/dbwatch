"""
Polling loop — watches the database on a fixed interval,
auto-snapshots on each tick, diffs against the previous state,
and prints any changes to the terminal.

Handles SIGINT (Ctrl+C) for a clean shutdown.
"""
import time
import signal
import datetime
from sqlalchemy.engine import Engine
from rich.console import Console
from dbwatch import snapshot, differ, reporter

console = Console()
_running = True


def _handle_sigint(sig, frame):
    global _running
    _running = False
    console.print("\n[yellow]Stopping watch…[/yellow]")


def run(engine: Engine, interval: int = 60, include_data: bool = False) -> None:
    """Poll the database every `interval` seconds and report changes."""
    signal.signal(signal.SIGINT, _handle_sigint)
    console.print(
        f"[bold]dbwatch[/bold] watching every {interval}s "
        f"{'(with data hashing) ' if include_data else ''}"
        f"— press Ctrl+C to stop\n"
    )

    # Initial baseline snapshot
    snap_prev = snapshot.take(engine, label="watch_prev", include_data=include_data)
    snapshot.save(snap_prev, "watch_prev")

    while _running:
        time.sleep(interval)
        if not _running:
            break

        ts = datetime.datetime.utcnow().strftime("%H:%M:%S")
        snap_curr = snapshot.take(engine, label="watch_curr", include_data=include_data)
        snapshot.save(snap_curr, "watch_curr")

        delta = differ.diff(snap_prev, snap_curr)
        if delta.has_changes:
            console.rule(f"[yellow]{ts} — changes detected[/yellow]")
            reporter.report(delta)
        else:
            console.print(f"[dim]{ts} — no changes[/dim]")

        # Roll forward: current becomes the new baseline
        snap_prev = snap_curr
        snapshot.save(snap_curr, "watch_prev")
