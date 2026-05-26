"""
dbwatch CLI — entry point for all commands.
Uses Typer for argument parsing and Rich for terminal output.
"""
import typer
from typing import Optional
from pathlib import Path
from dbwatch import connector, snapshot, differ, reporter, scheduler

app = typer.Typer(
    name="dbwatch",
    help="Monitor SQL databases for schema and data changes.",
    add_completion=False,
)


@app.command()
def init(
    url: str = typer.Option(..., "--url", "-u", help="SQLAlchemy database URL"),
    config: Path = typer.Option(Path(".dbwatch.json"), "--config", "-c"),
):
    """Initialise dbwatch for a database and save connection config."""
    connector.save_config(config, url)
    typer.echo(f"✓ Config saved to {config}")


@app.command(name="snapshot")
def snapshot_cmd(
    label: str = typer.Option("latest", "--label", "-l", help="Name for this snapshot"),
    config: Path = typer.Option(Path(".dbwatch.json"), "--config", "-c"),
    data: bool = typer.Option(False, "--data", "-d", help="Include row-level hashes"),
):
    """Take a snapshot of the current database state."""
    url = connector.load_config(config)
    engine = connector.get_engine(url)
    snap = snapshot.take(engine, label=label, include_data=data)
    snapshot.save(snap, label)
    typer.echo(f"✓ Snapshot '{label}' saved ({len(snap['tables'])} tables)")


@app.command()
def diff(
    from_label: str = typer.Option(..., "--from", "-f", help="Base snapshot label"),
    to_label: str = typer.Option("latest", "--to", "-t", help="Target snapshot label"),
    output: str = typer.Option("terminal", "--output", "-o", help="terminal | json | file"),
    out_path: Optional[Path] = typer.Option(None, "--out-path", "-p"),
):
    """Diff two snapshots and report what changed."""
    snap_a = snapshot.load(from_label)
    snap_b = snapshot.load(to_label)
    delta = differ.diff(snap_a, snap_b)
    reporter.report(delta, mode=output, path=out_path)


@app.command()
def watch(
    interval: int = typer.Option(60, "--interval", "-i", help="Poll interval in seconds"),
    config: Path = typer.Option(Path(".dbwatch.json"), "--config", "-c"),
    data: bool = typer.Option(False, "--data", "-d"),
):
    """Continuously poll the database and report changes."""
    url = connector.load_config(config)
    engine = connector.get_engine(url)
    scheduler.run(engine, interval=interval, include_data=data)


if __name__ == "__main__":
    app()
