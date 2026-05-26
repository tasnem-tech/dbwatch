# dbwatch

> A CLI tool that watches SQL databases for schema and data changes — like `git diff` for your database.

## Features

- **Schema diffing** — detects added/removed tables, column changes, type changes, nullability changes
- **Row count tracking** — spots data growth or shrinkage across snapshots  
- **Row-hash comparison** — optionally fingerprints every table's data for mutation detection
- **Watch mode** — polls continuously and alerts on any change
- **Multiple outputs** — rich terminal tables, JSON, or file output
- **Any SQL DB** — SQLite, PostgreSQL, MySQL via SQLAlchemy

## Install

```bash
pip install dbwatch
# With PostgreSQL support:
pip install "dbwatch[postgres]"
```

## Quick start

```bash
# 1. Point dbwatch at your database
dbwatch init --url "sqlite:///myapp.db"

# 2. Snapshot before a migration
dbwatch snapshot --label before-migration

# 3. Run your migration
alembic upgrade head

# 4. See what changed
dbwatch diff --from before-migration

# 5. Watch continuously
dbwatch watch --interval 30
```

## Commands

| Command | Description |
|---|---|
| `dbwatch init --url <url>` | Save DB connection config |
| `dbwatch snapshot --label <name>` | Capture current state |
| `dbwatch diff --from <label>` | Compare two snapshots |
| `dbwatch watch --interval <secs>` | Continuous polling mode |

## Output formats

```bash
dbwatch diff --from before --output terminal   # default rich table
dbwatch diff --from before --output json       # machine-readable
dbwatch diff --from before --output file --out-path report.json
```

## Development

```bash
git clone https://github.com/YOUR_USERNAME/dbwatch
cd dbwatch
pip install -e ".[dev]"
pytest
```

## License

MIT
